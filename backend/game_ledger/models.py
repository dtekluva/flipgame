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
    total_winnings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total amount won (0 if bomb hit, stake * multiplier if cashed out)"
    )
    final_wallet_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Player's wallet balance after the game ended"
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


class GameAnalytics(models.Model):
    """Model to track individual game records for analytics (separate from session tracking)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game_type = models.CharField(
        max_length=50,
        help_text="Type/variant of the game (e.g., 'bomb_flip', 'classic', etc.)"
    )
    player_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Player's display name"
    )
    session_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Optional session identifier from external systems"
    )
    stake_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount wagered for this game"
    )
    winning_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Amount won (0 for losses, stake * multiplier for wins)"
    )
    multiplier = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=1.00,
        help_text="Final multiplier achieved in the game"
    )
    bomb_rate = models.IntegerField(
        help_text="Bomb rate percentage used (e.g., 15 for 15%)"
    )
    cards_flipped = models.IntegerField(
        default=0,
        help_text="Number of safe cards flipped before cashout/bomb"
    )
    game_outcome = models.CharField(
        max_length=20,
        choices=[
            ('WIN', 'Win (Cashed Out)'),
            ('LOSS', 'Loss (Bomb Hit)'),
            ('PERFECT', 'Perfect Game'),
        ],
        help_text="Final outcome of the game"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Game Analytics Record"
        verbose_name_plural = "Game Analytics Records"
        indexes = [
            models.Index(fields=['game_type', 'bomb_rate']),
            models.Index(fields=['created_at']),
            models.Index(fields=['game_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.game_type} - {self.player_name or 'Anonymous'} - {self.game_outcome}"

    @property
    def profit_loss(self):
        """Calculate profit/loss for this game"""
        return self.winning_amount - self.stake_amount


class DailyProfitStats(models.Model):
    """High-performance model for storing pre-calculated daily profit statistics"""

    date = models.DateField(
        unique=True,
        db_index=True,
        help_text="Date for which profit stats are calculated"
    )
    profit_data = models.JSONField(
        help_text="Profit percentages by game type, e.g., {'bomb_flip': 20.5, 'quick_cash': 15.3}"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was first created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated"
    )

    class Meta:
        db_table = 'game_ledger_daily_profit_stats'
        verbose_name = "Daily Profit Stats"
        verbose_name_plural = "Daily Profit Stats"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['-date'], name='daily_profit_date_desc_idx'),
        ]

    def __str__(self):
        return f"Profit Stats for {self.date}"
