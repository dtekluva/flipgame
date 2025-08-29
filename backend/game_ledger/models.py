from django.db import models
from django.utils import timezone
import uuid


class GameSession(models.Model):
    """Model to track individual game sessions"""

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CASHED_OUT', 'Cashed Out'),
        ('BOMB_HIT', 'Bomb Hit'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=100, help_text="Unique identifier for the player")
    username = models.CharField(max_length=50, help_text="Display name for the player")
    starting_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Player's wallet balance at game start"
    )
    stake = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount wagered for this game"
    )
    grid_size = models.IntegerField(help_text="Size of the game grid (e.g., 5 for 5x5)")
    bomb_probability = models.FloatField(help_text="Probability of bombs as percentage (e.g., 20.0 for 20%)")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        help_text="Current status of the game session"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True, help_text="When the game ended")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Game Session"
        verbose_name_plural = "Game Sessions"

    def __str__(self):
        return f"Game {self.id} - {self.username} ({self.status})"

    def save(self, *args, **kwargs):
        # Auto-set ended_at when status changes to terminal state
        if self.status in ['CASHED_OUT', 'BOMB_HIT'] and not self.ended_at:
            self.ended_at = timezone.now()
        super().save(*args, **kwargs)


class GameEvent(models.Model):
    """Model to track individual events within a game session"""

    EVENT_TYPE_CHOICES = [
        ('GAME_STARTED', 'Game Started'),
        ('FLIP', 'Card Flip'),
        ('CASHOUT', 'Cash Out'),
        ('BOMB_HIT', 'Bomb Hit'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name='events',
        help_text="The game session this event belongs to"
    )
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        help_text="Type of event that occurred"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount involved in the event (winnings, stake, etc.)"
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Player's balance after this event"
    )
    multiplier = models.FloatField(
        null=True,
        blank=True,
        help_text="Current multiplier at time of event"
    )
    cell_position = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Grid position of flipped card (e.g., '2-3')"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = "Game Event"
        verbose_name_plural = "Game Events"

    def __str__(self):
        return f"{self.event_type} - {self.session.username}"
