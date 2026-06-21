# core/views.py
import re
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from .models import NewsPost, Announcement, Leadership, Member, FoundingMember, MembershipTier, Event, SiteSettings
from .forms import MemberJoinForm, MemberLoginForm, MemberProfileForm

def get_member_from_session(request):
    """Helper to get the logged-in member from the session."""
    member_id = request.session.get('member_id')
    if member_id:
        try:
            return Member.objects.get(id=member_id, is_active=True)
        except Member.DoesNotExist:
            return None
    return None

# ==========================================
# PUBLIC VIEWS
# ==========================================

def home_view(request):
    latest_news = NewsPost.objects.all()[:3] 
    upcoming_events = Event.objects.filter(is_upcoming=True)[:3] 
    settings = SiteSettings.load()
    return render(request, 'home.html', {
        'latest_news': latest_news,
        'upcoming_events': upcoming_events,
        'settings': settings
    })

def about_view(request):
    founders = FoundingMember.objects.all()
    tiers = MembershipTier.objects.all()
    settings = SiteSettings.load()
    current_leaders = Leadership.objects.filter(is_current=True).select_related('member')
    return render(request, 'about.html', {
        'founders': founders,
        'tiers': tiers,
        'settings': settings,
        'leaders': current_leaders,
    })

def news_view(request):
    news_posts = NewsPost.objects.all()
    settings = SiteSettings.load()
    return render(request, 'news.html', {'news_posts': news_posts, 'settings': settings})

def announcements_view(request):
    announcements = Announcement.objects.all()
    settings = SiteSettings.load()
    return render(request, 'announcements.html', {'announcements': announcements, 'settings': settings})

def leadership_view(request):
    current_leaders = Leadership.objects.filter(is_current=True).select_related('member')
    settings = SiteSettings.load()
    return render(request, 'leadership.html', {'leaders': current_leaders, 'settings': settings})

def join_view(request):
    settings = SiteSettings.load()
    if request.method == 'POST':
        form = MemberJoinForm(request.POST, request.FILES)
        if form.is_valid():
            form.save() 
            return redirect('join_success') 
    else:
        form = MemberJoinForm()
    return render(request, 'join.html', {'form': form, 'settings': settings})

def join_success_view(request):
    settings = SiteSettings.load()
    treasurer_phone = "256785365538"
    treasurer = Leadership.objects.filter(role='EXEC_TREASURER', is_current=True).first()
    if treasurer and treasurer.member.phone_number:
        clean_phone = re.sub(r'\D', '', treasurer.member.phone_number)
        treasurer_phone = clean_phone
    return render(request, 'join_success.html', {
        'treasurer_phone': treasurer_phone,
        'settings': settings
    })

# ==========================================
# MEMBER PORTAL VIEWS
# ==========================================

def login_view(request):
    settings = SiteSettings.load()
    error = None
    
    if request.method == 'POST':
        form = MemberLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            try:
                member = Member.objects.get(email=email, is_active=True)
                if member.password and check_password(password, member.password):
                    # Login successful! Store member ID in session
                    request.session['member_id'] = member.id
                    return redirect('dashboard')
                else:
                    error = "Invalid password. Please contact the General Secretary to set your password."
            except Member.DoesNotExist:
                error = "No active member found with that email address."
    else:
        form = MemberLoginForm()
    
    return render(request, 'login.html', {'form': form, 'error': error, 'settings': settings})

def logout_view(request):
    # Clear the session
    if 'member_id' in request.session:
        del request.session['member_id']
    return redirect('home')

def dashboard_view(request):
    settings = SiteSettings.load()
    member = get_member_from_session(request)
    
    if not member:
        return redirect('login')
    
    # Get data for the dashboard
    upcoming_events = Event.objects.filter(is_upcoming=True)[:5]
    latest_news = NewsPost.objects.all()[:3]
    latest_announcements = Announcement.objects.all()[:3]
    
    # Get member's leadership roles if any
    member_roles = Leadership.objects.filter(member=member, is_current=True)
    
    return render(request, 'dashboard.html', {
        'member': member,
        'upcoming_events': upcoming_events,
        'latest_news': latest_news,
        'latest_announcements': latest_announcements,
        'member_roles': member_roles,
        'settings': settings
    })

def profile_view(request):
    settings = SiteSettings.load()
    member = get_member_from_session(request)
    
    if not member:
        return redirect('login')
    
    if request.method == 'POST':
        form = MemberProfileForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = MemberProfileForm(instance=member)
    
    return render(request, 'profile.html', {
        'member': member,
        'form': form,
        'settings': settings
    })