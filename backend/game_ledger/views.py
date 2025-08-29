from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404

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

    # Create the game event
    game_event = GameEvent.objects.create(
        session=game_session,
        **validated_data
    )

    # Update session status if this is a terminal event
    if validated_data['event_type'] in ['CASHOUT', 'BOMB_HIT']:
        game_session.status = validated_data['event_type']
        game_session.ended_at = timezone.now()
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
