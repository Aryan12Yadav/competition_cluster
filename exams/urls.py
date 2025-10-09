# FILE: exams/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Main public pages
    path('', views.home_view, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('search/', views.search_view, name='search'),

    # Test flow pages
    path('category/<slug:category_slug>/', views.category_detail_view, name='category_detail'),
    path('tests/<slug:category_slug>/', views.test_list_view, name='test_list'),
    path('test/<int:test_id>/instructions/', views.test_instructions_view, name='test_instructions'),
    path('test/start/<int:test_id>/', views.start_test_view, name='start_test'),
    
    # API-like endpoint for submission
    path('test/submit/<int:test_id>/', views.submit_test_view, name='submit_test'),

    # Result, Review, and Leaderboard pages
    path('test/results/<int:result_id>/', views.results_view, name='test_results'),
    path('test/review/<int:result_id>/', views.answer_review_view, name='answer_review'),
    path('test/<int:test_id>/leaderboard/', views.leaderboard_view, name='leaderboard'),

    # User-specific dashboard pages
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/categories/', views.category_dashboard_view, name='category_dashboard'),
]

