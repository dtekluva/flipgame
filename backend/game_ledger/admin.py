from django.contrib import admin
from .models import GameSession, GameEvent


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

    list_display = ('id', 'username', 'user_id', 'stake', 'status', 'created_at', 'ended_at')
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
