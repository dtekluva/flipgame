from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.db.models import Count, Avg, Sum, Q
from django.http import JsonResponse

from .models import GameSession, GameEvent
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
    # Get all sessions
    sessions = GameSession.objects.all()

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
