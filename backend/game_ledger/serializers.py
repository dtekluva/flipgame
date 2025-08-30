from rest_framework import serializers
from .models import GameSession, GameEvent


class GameEventSerializer(serializers.ModelSerializer):
    """Serializer for GameEvent model"""

    class Meta:
        model = GameEvent
        fields = [
            'id', 'event_type', 'amount', 'balance',
            'multiplier', 'cell_position', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class GameSessionSerializer(serializers.ModelSerializer):
    """Serializer for GameSession model"""

    events = GameEventSerializer(many=True, read_only=True)

    class Meta:
        model = GameSession
        fields = [
            'id', 'user_id', 'username', 'starting_balance', 'stake',
            'grid_size', 'bomb_probability', 'status', 'total_winnings',
            'final_wallet_balance', 'created_at', 'ended_at', 'events'
        ]
        read_only_fields = ['id', 'created_at', 'ended_at']


class StartGameSerializer(serializers.Serializer):
    """Serializer for starting a new game"""

    user_id = serializers.CharField(max_length=100)
    username = serializers.CharField(max_length=50)
    starting_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    grid_size = serializers.IntegerField(min_value=3, max_value=10)
    bomb_probability = serializers.FloatField(min_value=5.0, max_value=50.0)
    stake = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)

    def validate(self, data):
        """Validate that stake doesn't exceed starting balance and username is not empty"""
        if data['stake'] > data['starting_balance']:
            raise serializers.ValidationError(
                "Stake amount cannot exceed starting balance"
            )

        # Validate username
        username = data.get('username', '').strip()
        if not username:
            raise serializers.ValidationError(
                "Username cannot be empty"
            )
        data['username'] = username

        return data


class GameEventCreateSerializer(serializers.Serializer):
    """Serializer for creating game events"""

    session_id = serializers.UUIDField()
    event_type = serializers.ChoiceField(choices=GameEvent.EVENT_TYPE_CHOICES)
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    balance = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    multiplier = serializers.FloatField(required=False, allow_null=True)
    cell_position = serializers.CharField(
        max_length=10,
        required=False,
        allow_blank=True,
        allow_null=True
    )
    total_winnings = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    final_wallet_balance = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True
    )

    def validate_session_id(self, value):
        """Validate that the session exists and is active"""
        try:
            session = GameSession.objects.get(id=value)
            if session.status != 'ACTIVE':
                raise serializers.ValidationError(
                    "Cannot log events for inactive game sessions"
                )
            return value
        except GameSession.DoesNotExist:
            raise serializers.ValidationError("Game session not found")

    def validate(self, data):
        """Additional validation based on event type"""
        event_type = data.get('event_type')

        # FLIP events should have cell_position and multiplier
        if event_type == 'FLIP':
            if not data.get('cell_position'):
                raise serializers.ValidationError(
                    "FLIP events must include cell_position"
                )
            if data.get('multiplier') is None:
                raise serializers.ValidationError(
                    "FLIP events must include multiplier"
                )

        # CASHOUT events should have amount and balance
        if event_type == 'CASHOUT':
            if not data.get('amount'):
                raise serializers.ValidationError(
                    "CASHOUT events must include amount"
                )
            if data.get('balance') is None:
                raise serializers.ValidationError(
                    "CASHOUT events must include balance"
                )

        return data
