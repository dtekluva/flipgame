from django.contrib import admin
from .models import GameSession, GameEvent, GameAnalytics


class GameEventInline(admin.TabularInline):
    """Inline admin for GameEvent within GameSession"""
    model = GameEvent
    extra = 0
    readonly_fields = ('event_type', 'amount', 'balance', 'multiplier', 'cell_position', 'timestamp')
    fields = ('event_type', 'amount', 'balance', 'multiplier', 'cell_position', 'timestamp')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    """Admin interface for GameSession"""

    list_display = ('id', 'username', 'user_id', 'stake', 'total_winnings', 'final_wallet_balance', 'status', 'created_at', 'ended_at')
    list_filter = ('status', 'created_at', 'grid_size', 'bomb_probability')
    search_fields = ('username', 'user_id', 'id')
    readonly_fields = ('id', 'created_at', 'ended_at')

    fieldsets = (
        ('Player Information', {
            'fields': ('id', 'username', 'user_id', 'status')
        }),
        ('Game Settings', {
            'fields': ('grid_size', 'bomb_probability', 'stake', 'starting_balance')
        }),
        ('Game Results', {
            'fields': ('total_winnings', 'final_wallet_balance')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'ended_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [GameEventInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('events')


@admin.register(GameEvent)
class GameEventAdmin(admin.ModelAdmin):
    """Admin interface for GameEvent"""

    list_display = ('event_type', 'session', 'amount', 'balance', 'timestamp')
    list_filter = ('event_type', 'timestamp', 'session__status')
    search_fields = ('session__user_id', 'session__id')
    readonly_fields = ('id', 'timestamp')

    fieldsets = (
        ('Event Information', {
            'fields': ('id', 'session', 'event_type', 'timestamp')
        }),
        ('Game Data', {
            'fields': ('amount', 'balance', 'multiplier', 'cell_position')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session')

    def session(self, obj):
        return f"{obj.session.username} - {obj.session.status}"
    session.short_description = "Session"


@admin.register(GameAnalytics)
class GameAnalyticsAdmin(admin.ModelAdmin):
    """Admin interface for GameAnalytics"""

    list_display = (
        'player_name',
        'game_type',
        'bomb_rate',
        'stake_amount',
        'winning_amount',
        'multiplier',
        'cards_flipped',
        'game_outcome',
        'created_at'
    )

    list_filter = (
        'game_type',
        'bomb_rate',
        'game_outcome',
        'created_at'
    )

    search_fields = (
        'player_name',
        'session_id',
        'id'
    )

    readonly_fields = (
        'id',
        'created_at'
    )

    fieldsets = (
        ('Game Information', {
            'fields': ('id', 'game_type', 'player_name', 'session_id', 'created_at')
        }),
        ('Game Settings', {
            'fields': ('bomb_rate', 'stake_amount')
        }),
        ('Game Results', {
            'fields': ('game_outcome', 'winning_amount', 'multiplier', 'cards_flipped')
        }),
    )

    # Custom display methods
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')

    def colored_outcome(self, obj):
        """Display game outcome with color coding"""
        colors = {
            'WIN': 'green',
            'LOSS': 'red',
            'PERFECT': 'blue'
        }
        color = colors.get(obj.game_outcome, 'black')
        return f'<span style="color: {color}; font-weight: bold;">{obj.game_outcome}</span>'
    colored_outcome.allow_tags = True
    colored_outcome.short_description = 'Outcome'

    def profit_loss(self, obj):
        """Display profit/loss with color coding"""
        profit = obj.winning_amount - obj.stake_amount
        color = 'green' if profit > 0 else 'red' if profit < 0 else 'black'
        return f'<span style="color: {color}; font-weight: bold;">₦{profit:,.2f}</span>'
    profit_loss.allow_tags = True
    profit_loss.short_description = 'Profit/Loss'

    def house_edge_contribution(self, obj):
        """Calculate house edge contribution for this game"""
        house_profit = obj.stake_amount - obj.winning_amount
        return f'₦{house_profit:,.2f}'
    house_edge_contribution.short_description = 'House Profit'

    # Add custom columns to list display
    list_display = list_display + ('colored_outcome', 'profit_loss', 'house_edge_contribution')

    # Enable date hierarchy for easy filtering
    date_hierarchy = 'created_at'

    # Set default ordering
    ordering = ['-created_at']

    # Add actions
    actions = ['export_as_csv']

    def export_as_csv(self, request, queryset):
        """Export selected records as CSV"""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="game_analytics.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Player Name', 'Game Type', 'Bomb Rate', 'Stake Amount',
            'Winning Amount', 'Multiplier', 'Cards Flipped', 'Game Outcome',
            'Created At', 'Session ID'
        ])

        for obj in queryset:
            writer.writerow([
                obj.id, obj.player_name, obj.game_type, obj.bomb_rate,
                obj.stake_amount, obj.winning_amount, obj.multiplier,
                obj.cards_flipped, obj.game_outcome, obj.created_at,
                obj.session_id
            ])

        return response
    export_as_csv.short_description = "Export selected records as CSV"
