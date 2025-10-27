from django.urls import path
from . import views

app_name = 'game_ledger'

urlpatterns = [
    # Game session management
    path('game/start/', views.start_game, name='start_game'),
    path('game/event/', views.log_game_event, name='log_game_event'),
    path('game/session/<uuid:session_id>/', views.get_game_session, name='get_game_session'),
    path('game/user/<str:user_id>/sessions/', views.get_user_sessions, name='get_user_sessions'),

    # Analytics (Original)
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/data/', views.analytics_data, name='analytics_data'),

    # Analytics (New Filtered System)
    path('analytics/filtered/', views.filtered_analytics_dashboard, name='filtered_analytics_dashboard'),
    path('analytics/filtered-data/', views.filtered_analytics_data, name='filtered_analytics_data'),
    path('analytics/submit/', views.submit_game_analytics, name='submit_game_analytics'),

    # High-Performance Profit Stats
    path('analytics/current-profit/', views.current_profit_stats, name='current_profit_stats'),
]
