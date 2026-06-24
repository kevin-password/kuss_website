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

    # Class Rep portal
    path('class-rep/dashboard/', views.class_rep_dashboard, name='class_rep_dashboard'),
    path('class-rep/announcement/create/', views.create_class_announcement, name='create_class_announcement'),
    path('class-rep/event/create/', views.create_class_event, name='create_class_event'),
    path('class-rep/members/export/', views.export_class_members, name='export_class_members'),




    
    path('treasurer/dashboard/', views.treasurer_dashboard, name='treasurer_dashboard'),
    path('treasurer/transactions/', views.transaction_list, name='transaction_list'),
    path('treasurer/transactions/add/', views.add_transaction, name='add_transaction'),
    path('treasurer/toggle/<int:member_id>/', views.toggle_subscription, name='toggle_subscription'),
    path('treasurer/export/transactions/', views.export_transactions, name='export_transactions'),
    path('treasurer/export/members/', views.export_members, name='export_members'),

    path('leadership-portal/', views.leadership_portal, name='leadership_portal'),
    path('leadership-portal/news/create/', views.create_news_post, name='create_news'),
    path('leadership-portal/announcement/create/', views.create_announcement, name='create_announcement'),
    path('leadership-portal/event/create/', views.create_event, name='create_event'),
    path('leadership-portal/members/export/', views.export_members_csv, name='export_members_csv'),


    
]
