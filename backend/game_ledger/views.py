from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.db.models import Count, Avg, Sum, Q
from django.http import JsonResponse
from datetime import datetime, timedelta

from .models import GameSession, GameEvent, GameAnalytics, DailyProfitStats
from .serializers import (
    StartGameSerializer,
    GameEventCreateSerializer,
    GameSessionSerializer,
    GameEventSerializer
)


@api_view(['POST'])
def start_game(request):
    """
    Start a new game session

    POST /game/start/
    Request: {
        "user_id": "string",
        "username": "PlayerName",
        "starting_balance": 1000,
        "grid_size": 5,
        "bomb_probability": 20,
        "stake": 100
    }
    Response: {
        "session_id": "<uuid>",
        "status": "ACTIVE"
    }
    """
    serializer = StartGameSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    validated_data = serializer.validated_data

    # Create new game session
    game_session = GameSession.objects.create(
        user_id=validated_data['user_id'],
        username=validated_data['username'],
        starting_balance=validated_data['starting_balance'],
        stake=validated_data['stake'],
        grid_size=validated_data['grid_size'],
        bomb_probability=validated_data['bomb_probability'],
        status='ACTIVE'
    )

    # Create initial GAME_STARTED event
    GameEvent.objects.create(
        session=game_session,
        event_type='GAME_STARTED',
        amount=validated_data['stake'],
        balance=validated_data['starting_balance'] - validated_data['stake'],
        multiplier=1.0
    )

    return Response({
        'session_id': str(game_session.id),
        'status': game_session.status
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def log_game_event(request):
    """
    Log a game event

    POST /game/event/
    Request: {
        "session_id": "<uuid>",
        "event_type": "CASHOUT",
        "amount": 250,
        "balance": 1150,
        "multiplier": 2.5,
        "cell_position": "2-3"
    }
    Response: {
        "success": true
    }
    """
    serializer = GameEventCreateSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    validated_data = serializer.validated_data
    session_id = validated_data.pop('session_id')

    # Extract session-level fields
    total_winnings = validated_data.pop('total_winnings', None)
    final_wallet_balance = validated_data.pop('final_wallet_balance', None)

    # Get the game session
    try:
        game_session = GameSession.objects.get(id=session_id)
    except GameSession.DoesNotExist:
        return Response(
            {'error': 'Game session not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check if session is still active
    if game_session.status != 'ACTIVE':
        return Response(
            {'error': 'Cannot log events for inactive game sessions'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create the game event (without session-level fields)
    game_event = GameEvent.objects.create(
        session=game_session,
        **validated_data
    )

    # Update session status if this is a terminal event
    if validated_data['event_type'] in ['CASHOUT', 'BOMB_HIT']:
        # Map event types to session status
        status_mapping = {
            'CASHOUT': 'CASHED_OUT',
            'BOMB_HIT': 'BOMB_HIT'
        }
        game_session.status = status_mapping[validated_data['event_type']]
        game_session.ended_at = timezone.now()

        # Update total winnings and final wallet balance
        if total_winnings is not None:
            game_session.total_winnings = total_winnings
        if final_wallet_balance is not None:
            game_session.final_wallet_balance = final_wallet_balance

        game_session.save()

    return Response({
        'success': True,
        'event_id': str(game_event.id)
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_game_session(request, session_id):
    """
    Get details of a specific game session with all events

    GET /game/session/<uuid>/
    Response: GameSession with nested events
    """
    game_session = get_object_or_404(GameSession, id=session_id)
    serializer = GameSessionSerializer(game_session)
    return Response(serializer.data)


@api_view(['GET'])
def get_user_sessions(request, user_id):
    """
    Get all game sessions for a specific user

    GET /game/user/<user_id>/sessions/
    Response: List of GameSessions
    """
    sessions = GameSession.objects.filter(user_id=user_id)
    serializer = GameSessionSerializer(sessions, many=True)
    return Response(serializer.data)


def analytics_dashboard(request):
    """
    Render the analytics dashboard HTML page
    """
    return render(request, 'analytics/dashboard.html')


@api_view(['GET'])
def analytics_data(request):
    """
    Get analytics data for the dashboard

    GET /analytics/data/
    Response: Analytics data broken down by stake amount and bomb rate
    """
    # Get sessions from October 2, 2025 onwards
    start_date = datetime(2025, 10, 2, tzinfo=timezone.utc)
    sessions = GameSession.objects.filter(created_at__gte=start_date)

    # Define our fixed combinations
    combinations = [
        {'stake': 100, 'bomb_rate': 15},
        {'stake': 100, 'bomb_rate': 25},
        {'stake': 200, 'bomb_rate': 15},
        {'stake': 200, 'bomb_rate': 25},
    ]

    analytics_data = []

    for combo in combinations:
        # Filter sessions for this combination
        combo_sessions = sessions.filter(
            stake=combo['stake'],
            bomb_probability=combo['bomb_rate']
        )

        total_sessions = combo_sessions.count()

        if total_sessions > 0:
            # Calculate statistics
            cashed_out = combo_sessions.filter(status='CASHED_OUT').count()
            bomb_hits = combo_sessions.filter(status='BOMB_HIT').count()

            # Calculate win rate
            win_rate = (cashed_out / total_sessions) * 100 if total_sessions > 0 else 0

            # Calculate average winnings for successful cashouts
            successful_sessions = combo_sessions.filter(status='CASHED_OUT', total_winnings__isnull=False)
            avg_winnings = successful_sessions.aggregate(avg_win=Avg('total_winnings'))['avg_win'] or 0

            # Calculate total revenue (stakes collected)
            total_stakes = combo_sessions.aggregate(total_stakes=Sum('stake'))['total_stakes'] or 0

            # Calculate total payouts
            total_payouts = combo_sessions.filter(total_winnings__isnull=False).aggregate(
                total_payouts=Sum('total_winnings')
            )['total_payouts'] or 0

            # Calculate house edge (profit margin)
            house_profit = total_stakes - total_payouts
            house_edge = (house_profit / total_stakes) * 100 if total_stakes > 0 else 0

            # Get recent sessions for this combination
            recent_sessions = combo_sessions.order_by('-created_at')[:10].values(
                'id', 'username', 'status', 'total_winnings', 'created_at'
            )

            analytics_data.append({
                'stake_amount': combo['stake'],
                'bomb_rate': combo['bomb_rate'],
                'total_sessions': total_sessions,
                'cashed_out': cashed_out,
                'bomb_hits': bomb_hits,
                'win_rate': round(win_rate, 2),
                'avg_winnings': float(avg_winnings) if avg_winnings else 0,
                'total_stakes': float(total_stakes),
                'total_payouts': float(total_payouts),
                'house_profit': float(house_profit),
                'house_edge': round(house_edge, 2),
                'recent_sessions': list(recent_sessions)
            })
        else:
            # No sessions for this combination yet
            analytics_data.append({
                'stake_amount': combo['stake'],
                'bomb_rate': combo['bomb_rate'],
                'total_sessions': 0,
                'cashed_out': 0,
                'bomb_hits': 0,
                'win_rate': 0,
                'avg_winnings': 0,
                'total_stakes': 0,
                'total_payouts': 0,
                'house_profit': 0,
                'house_edge': 0,
                'recent_sessions': []
            })

    # Overall statistics
    overall_stats = {
        'total_sessions': sessions.count(),
        'total_stakes': float(sessions.aggregate(total=Sum('stake'))['total'] or 0),
        'total_payouts': float(sessions.filter(total_winnings__isnull=False).aggregate(
            total=Sum('total_winnings'))['total'] or 0),
    }
    overall_stats['house_profit'] = overall_stats['total_stakes'] - overall_stats['total_payouts']
    overall_stats['house_edge'] = (overall_stats['house_profit'] / overall_stats['total_stakes']) * 100 if overall_stats['total_stakes'] > 0 else 0

    return JsonResponse({
        'combinations': analytics_data,
        'overall': overall_stats,
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
def filtered_analytics_dashboard(request):
    """
    Render the filtered analytics dashboard HTML page

    GET /analytics/filtered/
    """
    return render(request, 'analytics/filtered_dashboard.html')


@api_view(['POST'])
def submit_game_analytics(request):
    """
    Submit a game record for analytics tracking

    POST /analytics/submit/
    Body: {
        "game_type": "bomb_flip",
        "player_name": "PlayerName",
        "session_id": "optional_session_id",
        "stake_amount": 200.00,
        "winning_amount": 240.00,
        "multiplier": 1.20,
        "bomb_rate": 15,
        "cards_flipped": 4,
        "game_outcome": "WIN"
    }
    """
    try:
        # Extract data from request
        data = request.data

        # Validate required fields
        required_fields = ['game_type', 'stake_amount', 'winning_amount', 'multiplier', 'bomb_rate', 'game_outcome']
        for field in required_fields:
            if field not in data:
                return Response({
                    'error': f'Missing required field: {field}'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Create analytics record
        analytics_record = GameAnalytics.objects.create(
            game_type=data['game_type'],
            player_name=data.get('player_name', 'Anonymous'),
            session_id=data.get('session_id'),
            stake_amount=data['stake_amount'],
            winning_amount=data['winning_amount'],
            multiplier=data['multiplier'],
            bomb_rate=data['bomb_rate'],
            cards_flipped=data.get('cards_flipped', 0),
            game_outcome=data['game_outcome']
        )

        return Response({
            'success': True,
            'record_id': str(analytics_record.id),
            'message': 'Game analytics record created successfully'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': f'Failed to create analytics record: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def filtered_analytics_data(request):
    """
    Get filtered analytics data for the dashboard

    GET /analytics/filtered-data/
    Query Parameters:
    - date_range: 'today', 'week', 'month', 'custom' (default: 'month')
    - start_date: YYYY-MM-DD (for custom range)
    - end_date: YYYY-MM-DD (for custom range)
    - game_type: filter by game type (optional)
    - bomb_rate: filter by bomb rate (optional)
    """
    try:
        # Get query parameters
        date_range = request.GET.get('date_range', 'month')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        game_type_filter = request.GET.get('game_type')
        bomb_rate_filter = request.GET.get('bomb_rate')

        # Calculate date range
        now = timezone.now()
        if date_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif date_range == 'week':
            start_date = now - timedelta(days=7)
            end_date = now
        elif date_range == 'month':
            start_date = now - timedelta(days=30)
            end_date = now
        elif date_range == 'custom':
            if start_date_str and end_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            else:
                return Response({
                    'error': 'start_date and end_date required for custom date range'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'error': 'Invalid date_range. Use: today, week, month, or custom'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Base queryset with date filter
        queryset = GameAnalytics.objects.filter(created_at__gte=start_date, created_at__lte=end_date)

        # Apply additional filters
        if game_type_filter:
            queryset = queryset.filter(game_type=game_type_filter)
        if bomb_rate_filter:
            queryset = queryset.filter(bomb_rate=int(bomb_rate_filter))

        # Get unique combinations that actually exist in the filtered data
        combinations = queryset.values('game_type', 'bomb_rate').distinct().order_by('game_type', 'bomb_rate')

        analytics_data = []

        # Process each existing combination
        for combo in combinations:
            game_type = combo['game_type']
            bomb_rate = combo['bomb_rate']
            combo_records = queryset.filter(game_type=game_type, bomb_rate=bomb_rate)

            if combo_records.exists():
                    total_sessions = combo_records.count()
                    wins = combo_records.filter(game_outcome='WIN').count()
                    losses = combo_records.filter(game_outcome='LOSS').count()
                    perfect_games = combo_records.filter(game_outcome='PERFECT').count()

                    total_stakes = float(combo_records.aggregate(total=Sum('stake_amount'))['total'] or 0)
                    total_payouts = float(combo_records.aggregate(total=Sum('winning_amount'))['total'] or 0)
                    avg_multiplier = float(combo_records.aggregate(avg=Avg('multiplier'))['avg'] or 0)
                    avg_cards_flipped = float(combo_records.aggregate(avg=Avg('cards_flipped'))['avg'] or 0)

                    house_profit = total_stakes - total_payouts
                    house_edge = (house_profit / total_stakes) * 100 if total_stakes > 0 else 0
                    win_rate = (wins / total_sessions) * 100 if total_sessions > 0 else 0

                    # Recent sessions (last 10)
                    recent_sessions = []
                    for record in combo_records.order_by('-created_at')[:10]:
                        recent_sessions.append({
                            'id': str(record.id),
                            'player_name': record.player_name or 'Anonymous',
                            'outcome': record.game_outcome,
                            'stake': float(record.stake_amount),
                            'winnings': float(record.winning_amount),
                            'multiplier': float(record.multiplier),
                            'cards_flipped': record.cards_flipped,
                            'created_at': record.created_at.isoformat()
                        })

                    analytics_data.append({
                        'game_type': game_type,
                        'bomb_rate': bomb_rate,
                        'total_sessions': total_sessions,
                        'wins': wins,
                        'losses': losses,
                        'perfect_games': perfect_games,
                        'win_rate': round(win_rate, 2),
                        'avg_multiplier': round(avg_multiplier, 2),
                        'avg_cards_flipped': round(avg_cards_flipped, 1),
                        'total_stakes': total_stakes,
                        'total_payouts': total_payouts,
                        'house_profit': house_profit,
                        'house_edge': f"{house_edge:.2f}",
                        'recent_sessions': recent_sessions
                    })

        # Overall statistics
        overall_stats = {
            'total_sessions': queryset.count(),
            'total_stakes': float(queryset.aggregate(total=Sum('stake_amount'))['total'] or 0),
            'total_payouts': float(queryset.aggregate(total=Sum('winning_amount'))['total'] or 0),
            'total_wins': queryset.filter(game_outcome='WIN').count(),
            'total_losses': queryset.filter(game_outcome='LOSS').count(),
            'total_perfect_games': queryset.filter(game_outcome='PERFECT').count(),
        }
        overall_stats['house_profit'] = overall_stats['total_stakes'] - overall_stats['total_payouts']
        overall_stats['house_edge'] = (overall_stats['house_profit'] / overall_stats['total_stakes']) * 100 if overall_stats['total_stakes'] > 0 else 0
        overall_stats['overall_win_rate'] = (overall_stats['total_wins'] / overall_stats['total_sessions']) * 100 if overall_stats['total_sessions'] > 0 else 0

        return JsonResponse({
            'combinations': analytics_data,
            'overall': overall_stats,
            'filters': {
                'date_range': date_range,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'game_type': game_type_filter,
                'bomb_rate': bomb_rate_filter
            },
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return Response({
            'error': f'Failed to fetch analytics data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def current_profit_stats(request):
    """
    High-performance endpoint to retrieve current profit statistics.
    Optimized for sub-200ms response time.
    """
    try:
        # Single optimized query to get the most recent profit stats
        latest_stats = DailyProfitStats.objects.select_related().order_by('-date').first()

        if not latest_stats:
            return Response({
                'error': 'No profit statistics available'
            }, status=status.HTTP_404_NOT_FOUND)

        # Return pre-calculated data (no complex calculations here)
        return Response({
            'date': latest_stats.date.isoformat(),
            'profit_by_game_type': latest_stats.profit_data,
            'last_updated': latest_stats.updated_at.isoformat()
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to fetch profit statistics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
