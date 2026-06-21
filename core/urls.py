# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('news/', views.news_view, name='news'),
    path('announcements/', views.announcements_view, name='announcements'),
    path('leadership/', views.leadership_view, name='leadership'),
    path('join/', views.join_view, name='join'),
    path('join/success/', views.join_success_view, name='join_success'),
    
    # MEMBER PORTAL ROUTES
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
]