# core/views.py
import re
import csv
import random
import string
import requests
import urllib.parse
import traceback
from decimal import Decimal
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

from .models import (
    NewsPost, Announcement, Leadership, Member, FoundingMember, 
    MembershipTier, Event, SiteSettings, Subscription, Notification,
    Transaction, TransactionCategory, ResearchLink,
    Product, Order, OrderItem
)
from .forms import MemberJoinForm, MemberLoginForm, MemberProfileForm

# ==========================================
# WEB3FORMS EMAIL CONFIGURATION
# ==========================================
WEB3FORMS_ACCESS_KEY = 'f2c217cf-dd95-44ea-b8db-037947e8edce'
WEB3FORMS_API_URL = 'https://api.web3forms.com/submit'
TECH_EMAIL = 'tumusiimekevin3@gmail.com'
FROM_NAME = 'KUSS - Kabale University Surgical Society'

# ==========================================
# WHATSAPP (CallMeBot) CONFIGURATION
# ==========================================
CALLMEBOT_API_KEY = '6245479'
TECH_WHATSAPP = '+256785365538'

# ==========================================
# BACKEND EMAIL HELPER (NON-BLOCKING)
# These will fail on PythonAnywhere FREE but won't crash the site
# The frontend will handle actual email sending
# ==========================================

def send_email_via_web3forms(to_email, subject, message, from_name=None):
    """Send email using Web3Forms API - will fail on PA FREE but won't crash."""
    if from_name is None:
        from_name = FROM_NAME
    
    try:
        payload = {
            'apikey': WEB3FORMS_ACCESS_KEY,
            'subject': subject,
            'from_name': from_name,
            'to': to_email,
            'message': message,
            'botcheck': ''
        }
        
        response = requests.post(WEB3FORMS_API_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Email sent to {to_email} via Web3Forms")
                return True
            else:
                print(f"⚠️ Web3Forms error: {result.get('message')}")
                return False
        else:
            print(f"⚠️ Web3Forms HTTP {response.status_code}")
            return False
            
    except Exception as e:
        # Silently fail - frontend will handle email sending
        print(f"⚠️ Backend email failed (frontend will handle): {e}")
        return False

# ==========================================
# BACKEND WHATSAPP HELPER (NON-BLOCKING)
# ==========================================

def clean_phone_number(phone):
    """Convert phone number to international format for CallMeBot."""
    if not phone:
        return None
    
    clean = re.sub(r'[\s\-\(\)]', '', phone)
    
    if clean.startswith('0'):
        clean = '+256' + clean[1:]
    elif clean.startswith('256'):
        clean = '+' + clean
    elif not clean.startswith('+'):
        clean = '+256' + clean
    
    return clean

def send_whatsapp(phone_number, message):
    """Send WhatsApp message - will fail on PA FREE but won't crash."""
    clean_phone = clean_phone_number(phone_number)
    
    if not clean_phone:
        return False
    
    try:
        encoded_message = urllib.parse.quote(message)
        url = f"https://api.callmebot.com/whatsapp.php?phone={clean_phone.replace('+', '')}&text={encoded_message}&apikey={CALLMEBOT_API_KEY}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            response_text = response.text.lower()
            if 'error' in response_text or 'failed' in response_text:
                return False
            print(f"✅ WhatsApp sent to {clean_phone}")
            return True
        return False
            
    except Exception as e:
        print(f"⚠️ Backend WhatsApp failed (frontend will handle): {e}")
        return False

# ==========================================
# FRONTEND API ENDPOINTS (These work!)
# The frontend JavaScript will use these to send emails from the browser
# ==========================================

@require_GET
def api_get_recipients(request):
    """API: Get all member emails for frontend email sending."""
    member = get_member_from_session(request)
    if not member or not is_leader(member):
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    members = Member.objects.filter(is_active=True).exclude(email='').values(
        'id', 'first_name', 'last_name', 'email', 'phone_number'
    )
    
    return JsonResponse({
        'recipients': list(members),
        'count': len(members)
    })

@require_GET
def api_get_new_member_info(request):
    """API: Get newly registered member info for welcome email (used by join_success page)."""
    # Get the last registered member from session
    member_id = request.session.get('new_member_id')
    password = request.session.get('new_member_password')
    
    if not member_id or not password:
        return JsonResponse({'error': 'No new member data'}, status=404)
    
    try:
        member = Member.objects.get(id=member_id)
        settings = SiteSettings.load()
        
        # Clear the session data after retrieving
        del request.session['new_member_id']
        del request.session['new_member_password']
        
        return JsonResponse({
            'first_name': member.first_name,
            'last_name': member.last_name,
            'email': member.email,
            'password': password,
            'treasurer_name': settings.treasurer_name or 'Treasurer',
            'treasurer_phone': settings.treasurer_phone or '',
            'payment_instructions': settings.payment_instructions or 'Contact the Treasurer for payment details.',
            'contact_email': settings.contact_email or 'kabsurgicalsociety@gmail.com',
        })
    except Member.DoesNotExist:
        return JsonResponse({'error': 'Member not found'}, status=404)

@require_GET
def api_get_news_content(request, news_id):
    """API: Get news post content for frontend email sending."""
    member = get_member_from_session(request)
    if not member or not is_leader(member):
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    try:
        news = NewsPost.objects.get(id=news_id)
        return JsonResponse({
            'title': news.title,
            'content': news.content,
            'author': f"{news.author.first_name} {news.author.last_name}",
            'created_at': news.created_at.strftime('%B %d, %Y'),
        })
    except NewsPost.DoesNotExist:
        return JsonResponse({'error': 'News not found'}, status=404)

@require_GET
def api_get_announcement_content(request, announcement_id):
    """API: Get announcement content for frontend email sending."""
    member = get_member_from_session(request)
    if not member or not is_leader(member):
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    try:
        announcement = Announcement.objects.get(id=announcement_id)
        return JsonResponse({
            'title': announcement.title,
            'description': announcement.description,
            'created_at': announcement.created_at.strftime('%B %d, %Y'),
        })
    except Announcement.DoesNotExist:
        return JsonResponse({'error': 'Announcement not found'}, status=404)

@require_GET
def api_get_event_content(request, event_id):
    """API: Get event content for frontend email sending."""
    member = get_member_from_session(request)
    if not member or not is_leader(member):
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    try:
        event = Event.objects.get(id=event_id)
        return JsonResponse({
            'title': event.title,
            'description': event.description,
            'date': event.date.strftime('%B %d, %Y'),
            'venue': event.venue,
        })
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}, status=404)

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_member_from_session(request):
    """Helper to get the logged-in member from the session."""
    member_id = request.session.get('member_id')
    if member_id:
        try:
            return Member.objects.get(id=member_id, is_active=True)
        except Member.DoesNotExist:
            return None
    return None

def is_treasurer(member):
    """Check if a member is currently assigned as a Treasurer."""
    return Leadership.objects.filter(
        member=member,
        role__in=['EXEC_TREASURER', 'BOARD_TREASURER'],
        is_current=True
    ).exists()

def is_leader(member):
    """Check if member has any current leadership role."""
    return Leadership.objects.filter(member=member, is_current=True).exists()

def get_leader_roles(member):
    """Get all current leadership roles for a member."""
    return list(Leadership.objects.filter(member=member, is_current=True).values_list('role', flat=True))

def has_role(member, role_codes):
    """Check if member has any of the specified roles."""
    if isinstance(role_codes, str):
        role_codes = [role_codes]
    return Leadership.objects.filter(member=member, role__in=role_codes, is_current=True).exists()

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
    """Handle member registration - stores password in session for frontend email."""
    settings = SiteSettings.load()
    tiers = MembershipTier.objects.all()
    
    if request.method == 'POST':
        form = MemberJoinForm(request.POST, request.FILES)
        
        if form.is_valid():
            member = form.save(commit=False)
            
            # Generate random password (10 characters)
            random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            member.password = make_password(random_password)
            member.save()
            
            # Store member info in session for the frontend to send welcome email
            request.session['new_member_id'] = member.id
            request.session['new_member_password'] = random_password
            
            # Try backend email (will fail on PA FREE but that's OK)
            send_email_via_web3forms(TECH_EMAIL, 
                f'✅ New KUSS Member: {member.first_name} {member.last_name}',
                f'New member registered:\n{member.first_name} {member.last_name}\nEmail: {member.email}\nPhone: {member.phone_number}')
            
            return redirect('join_success')
    else:
        form = MemberJoinForm()
    
    return render(request, 'join.html', {
        'form': form,
        'settings': settings,
        'tiers': tiers,
    })

def join_success_view(request):
    """Success page - frontend JS will send welcome email from browser."""
    settings = SiteSettings.load()
    return render(request, 'join_success.html', {'settings': settings})

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
                    request.session['member_id'] = member.id

                    if is_treasurer(member):
                        return redirect('treasurer_dashboard')
                    elif has_role(member, ['CLASS_REP']):
                        return redirect('class_rep_dashboard')
                    elif is_leader(member):
                        return redirect('leadership_portal')
                    else:
                        return redirect('dashboard')
                else:
                    error = "Invalid password. Please contact the General Secretary to set your password."
            except Member.DoesNotExist:
                error = "No active member found with that email address."
    else:
        form = MemberLoginForm()

    return render(request, 'login.html', {'form': form, 'error': error, 'settings': settings})

def logout_view(request):
    if 'member_id' in request.session:
        del request.session['member_id']
    return redirect('home')

def dashboard_view(request):
    settings = SiteSettings.load()
    member = get_member_from_session(request)

    if not member:
        return redirect('login')

    upcoming_events = Event.objects.filter(is_upcoming=True)[:5]
    latest_news = NewsPost.objects.all()[:3]
    latest_announcements = Announcement.objects.all()[:3]
    member_roles = Leadership.objects.filter(member=member, is_current=True)
    notifications = Notification.objects.filter(member=member).order_by('-created_at')[:10]
    member_is_treasurer = is_treasurer(member)

    return render(request, 'dashboard.html', {
        'member': member,
        'upcoming_events': upcoming_events,
        'latest_news': latest_news,
        'latest_announcements': latest_announcements,
        'member_roles': member_roles,
        'notifications': notifications,
        'is_treasurer': member_is_treasurer,
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

# ==========================================
# TREASURER PORTAL VIEWS
# ==========================================

def treasurer_dashboard(request):
    member = get_member_from_session(request)
    if not member:
        return redirect('login')

    if not is_treasurer(member):
        messages.error(request, 'You are not authorized to access the Treasurer dashboard.')
        return redirect('dashboard')

    current_year = datetime.now().year

    total_income = Transaction.objects.filter(transaction_type='INCOME', date__year=current_year).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_expenses = Transaction.objects.filter(transaction_type='EXPENSE', date__year=current_year).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    cash_at_hand = total_income - total_expenses

    monthly_income = list(Transaction.objects.filter(transaction_type='INCOME', date__year=current_year)
                          .annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month'))

    monthly_expenses = list(Transaction.objects.filter(transaction_type='EXPENSE', date__year=current_year)
                            .annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month'))

    income_by_category = list(Transaction.objects.filter(transaction_type='INCOME', date__year=current_year)
                              .values('category__name').annotate(total=Sum('amount')).order_by('-total'))

    expense_by_category = list(Transaction.objects.filter(transaction_type='EXPENSE', date__year=current_year)
                               .values('category__name').annotate(total=Sum('amount')).order_by('-total'))

    recent_transactions = Transaction.objects.select_related('category', 'recorded_by')[:10]

    total_members = Member.objects.filter(is_active=True).count()
    paid_members = Subscription.objects.filter(is_paid=True, member__is_active=True).count()

    all_members = Member.objects.filter(is_active=True).select_related('subscription').order_by('last_name')

    return render(request, 'treasurer_dashboard.html', {
        'member': member,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'cash_at_hand': cash_at_hand,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'recent_transactions': recent_transactions,
        'income_by_category': income_by_category,
        'expense_by_category': expense_by_category,
        'total_members': total_members,
        'paid_members': paid_members,
        'unpaid_members': total_members - paid_members,
        'current_year': current_year,
        'all_members': all_members,
    })

def transaction_list(request):
    member = get_member_from_session(request)
    if not member or not is_treasurer(member):
        return redirect('login')

    transactions = Transaction.objects.select_related('category', 'recorded_by').all()
    categories = TransactionCategory.objects.filter(is_active=True)

    t_type = request.GET.get('type')
    if t_type:
        transactions = transactions.filter(transaction_type=t_type)

    cat_id = request.GET.get('category')
    if cat_id:
        transactions = transactions.filter(category_id=cat_id)

    date_from = request.GET.get('date_from')
    if date_from:
        transactions = transactions.filter(date__gte=date_from)

    date_to = request.GET.get('date_to')
    if date_to:
        transactions = transactions.filter(date__lte=date_to)

    return render(request, 'treasurer_transactions.html', {
        'member': member,
        'transactions': transactions,
        'categories': categories,
        'filters': {'type': t_type, 'category': cat_id, 'date_from': date_from, 'date_to': date_to}
    })

def add_transaction(request):
    member = get_member_from_session(request)
    if not member or not is_treasurer(member):
        return redirect('login')

    if request.method == 'POST':
        Transaction.objects.create(
            transaction_type=request.POST.get('transaction_type'),
            category_id=request.POST.get('category'),
            amount=Decimal(request.POST.get('amount', 0)),
            description=request.POST.get('description'),
            reference_number=request.POST.get('reference_number'),
            date=request.POST.get('date'),
            recorded_by=member
        )
        messages.success(request, 'Transaction recorded successfully.')
        return redirect('transaction_list')

    categories = TransactionCategory.objects.filter(is_active=True)
    return render(request, 'treasurer_add_transaction.html', {
        'member': member,
        'categories': categories
    })

def toggle_subscription(request, member_id):
    member = get_member_from_session(request)
    if not member or not is_treasurer(member):
        return redirect('login')

    target_member = get_object_or_404(Member, id=member_id)
    sub, _ = Subscription.objects.get_or_create(member=target_member)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_paid':
            sub.is_paid = not sub.is_paid
            if sub.is_paid:
                sub.payment_date = timezone.now().date()
                for tier in MembershipTier.objects.all():
                    if tier.name.lower() in target_member.membership_type.lower():
                        sub.amount_paid = tier.subscription_fee
                        break
            else:
                sub.payment_date = None
                sub.amount_paid = Decimal('0')
            sub.save()
            messages.success(request, f'Subscription updated for {target_member.first_name} {target_member.last_name}')

        elif action == 'send_reminder':
            # Create in-app notification
            Notification.objects.create(
                member=target_member,
                notification_type='PAYMENT_REMINDER',
                title='Subscription Fee Reminder',
                message=f'Dear {target_member.first_name}, this is a reminder to pay your subscription fees.'
            )
            
            # Try backend email/WhatsApp (will fail on PA FREE but that's OK)
            send_email_via_web3forms(target_member.email, '💰 Payment Reminder', 
                f'Dear {target_member.first_name}, please pay your KUSS subscription fees.')
            send_whatsapp(target_member.phone_number, 
                f'💰 PAYMENT REMINDER\n\nDear {target_member.first_name}, your KUSS subscription fees are pending.')
            
            sub.last_reminder_sent = timezone.now()
            sub.save()
            messages.success(request, f'Reminder sent to {target_member.first_name} {target_member.last_name}')

    return redirect('treasurer_dashboard')

def export_transactions(request):
    member = get_member_from_session(request)
    if not member or not is_treasurer(member):
        return redirect('login')

    transactions = Transaction.objects.select_related('category', 'recorded_by').all()

    t_type = request.GET.get('type')
    if t_type:
        transactions = transactions.filter(transaction_type=t_type)
    date_from = request.GET.get('date_from')
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    date_to = request.GET.get('date_to')
    if date_to:
        transactions = transactions.filter(date__lte=date_to)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="kuss_transactions_{datetime.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Type', 'Category', 'Amount (UGX)', 'Description', 'Reference', 'Recorded By'])

    for t in transactions:
        writer.writerow([
            t.date.strftime('%Y-%m-%d'),
            t.get_transaction_type_display(),
            t.category.name if t.category else 'N/A',
            t.amount,
            t.description,
            t.reference_number or '',
            f"{t.recorded_by.first_name} {t.recorded_by.last_name}" if t.recorded_by else 'System'
        ])
    return response

def export_members(request):
    member = get_member_from_session(request)
    if not member or not is_treasurer(member):
        return redirect('login')

    members = Member.objects.filter(is_active=True).select_related('subscription')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="kuss_members_{datetime.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Phone', 'Membership Type', 'Reg Number', 'Sub Status', 'Paid Amount', 'Payment Date'])

    for m in members:
        paid = hasattr(m, 'subscription') and m.subscription.is_paid
        writer.writerow([
            f"{m.first_name} {m.last_name}",
            m.email,
            m.phone_number,
            m.get_membership_type_display(),
            m.registration_number or 'N/A',
            'Paid' if paid else 'Unpaid',
            m.subscription.amount_paid if paid else 0,
            m.subscription.payment_date if paid else ''
        ])
    return response

# ==========================================
# LEADERSHIP PORTAL VIEWS
# ==========================================

def leadership_portal(request):
    member = get_member_from_session(request)
    if not member:
        return redirect('login')

    if not is_leader(member):
        messages.error(request, 'You do not have leadership access.')
        return redirect('dashboard')

    roles = get_leader_roles(member)
    settings = SiteSettings.load()

    context = {
        'member': member,
        'roles': roles,
        'role_display': [Leadership(role=r).get_role_display() for r in roles],
        'settings': settings,
    }

    if has_role(member, ['EXEC_CHAIR', 'EXEC_VICE_CHAIR', 'EXEC_GEN_SEC', 'EXEC_PUB_SEC',
                         'BOARD_CHAIR', 'BOARD_TREASURER', 'BOARD_STUDENT_REP', 'BOARD_UNI_ADMIN', 'PATRON']):
        context['total_members'] = Member.objects.filter(is_active=True).count()
        context['recent_members'] = Member.objects.filter(is_active=True).order_by('-date_joined')[:10]
        context['all_leaders'] = Leadership.objects.filter(is_current=True).select_related('member')
        context['upcoming_events'] = Event.objects.filter(is_upcoming=True)[:5]

    if has_role(member, ['EXEC_GEN_SEC']):
        context['all_members'] = Member.objects.filter(is_active=True).order_by('last_name')

    if has_role(member, ['EXEC_PUB_SEC']):
        context['news_posts'] = NewsPost.objects.all()[:10]
        context['announcements'] = Announcement.objects.all()[:10]

    if has_role(member, ['COMM_EDU']):
        context['events'] = Event.objects.all().order_by('-date')[:10]

    if has_role(member, ['COMM_RES']):
        context['research_news'] = NewsPost.objects.all()[:10]

    if has_role(member, ['COMM_MEN']):
        context['mentorship_members'] = Member.objects.filter(is_active=True)[:20]

    if has_role(member, ['CLASS_REP']):
        context['class_members'] = Member.objects.filter(is_active=True, membership_type='FULL')[:50]

    return render(request, 'leadership_portal.html', context)

def create_news_post(request):
    member = get_member_from_session(request)
    if not member or not has_role(member, [
        'EXEC_PUB_SEC', 'COMM_RES', 'COMM_EDU', 'COMM_MEN',
        'EXEC_CHAIR', 'EXEC_VICE_CHAIR', 'EXEC_GEN_SEC'
    ]):
        messages.error(request, 'Not authorized.')
        return redirect('leadership_portal')
    
    if request.method == 'POST':
        news_post = NewsPost.objects.create(
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            image=request.FILES.get('image'),
            author=member
        )
        
        # Note: Frontend will handle sending notifications via JavaScript
        messages.success(request, f'News post created! Use the "Send Notifications" button to email members about this news.')
        return redirect('leadership_portal')
    
    return render(request, 'create_news.html', {'member': member})

def create_announcement(request):
    member = get_member_from_session(request)
    if not member or not has_role(member, [
        'EXEC_GEN_SEC', 'EXEC_PUB_SEC', 'EXEC_CHAIR', 'EXEC_VICE_CHAIR',
        'COMM_EDU', 'COMM_RES', 'COMM_MEN'
    ]):
        messages.error(request, 'Not authorized.')
        return redirect('leadership_portal')
    
    if request.method == 'POST':
        announcement = Announcement.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            document=request.FILES.get('document')
        )
        
        messages.success(request, f'Announcement created! Use the "Send Notifications" button to email members.')
        return redirect('leadership_portal')
    
    return render(request, 'create_announcement.html', {'member': member})

def create_event(request):
    member = get_member_from_session(request)
    if not member or not has_role(member, [
        'COMM_EDU', 'COMM_RES', 'COMM_MEN',
        'EXEC_CHAIR', 'EXEC_VICE_CHAIR', 'EXEC_GEN_SEC', 'EXEC_PUB_SEC'
    ]):
        messages.error(request, 'Not authorized.')
        return redirect('leadership_portal')
    
    if request.method == 'POST':
        event = Event.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            date=request.POST.get('date'),
            venue=request.POST.get('venue'),
            flyer=request.FILES.get('flyer'),
            is_upcoming=True
        )
        
        messages.success(request, f'Event created! Use the "Send Notifications" button to email members.')
        return redirect('leadership_portal')
    
    return render(request, 'create_event.html', {'member': member})

def export_members_csv(request):
    member = get_member_from_session(request)
    if not member or not has_role(member, ['EXEC_GEN_SEC', 'EXEC_CHAIR', 'EXEC_VICE_CHAIR']):
        messages.error(request, 'Not authorized.')
        return redirect('leadership_portal')

    members = Member.objects.filter(is_active=True).order_by('last_name')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="kuss_members_{datetime.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Phone', 'Membership Type', 'Reg Number', 'Date Joined'])

    for m in members:
        writer.writerow([
            f"{m.first_name} {m.last_name}",
            m.email,
            m.phone_number,
            m.get_membership_type_display(),
            m.registration_number or '',
            m.date_joined.strftime('%Y-%m-%d')
        ])
    return response

# ==========================================
# SEND NOTIFICATIONS PAGE (Frontend Email Sending)
# ==========================================

def send_notifications_view(request):
    """Page where leaders can send bulk emails from their browser."""
    member = get_member_from_session(request)
    if not member or not is_leader(member):
        messages.error(request, 'Not authorized.')
        return redirect('dashboard')
    
    settings = SiteSettings.load()
    return render(request, 'send_notifications.html', {
        'member': member,
        'settings': settings,
    })

# ==========================================
# CLASS REP SPECIFIC VIEWS
# ==========================================

def class_rep_dashboard(request):
    member = get_member_from_session(request)
    if not member or not has_role(member, ['CLASS_REP']):
        messages.error(request, 'Not authorized.')
        return redirect('dashboard')

    settings = SiteSettings.load()

    class_members = Member.objects.filter(
        is_active=True,
        membership_type='FULL'
    ).order_by('last_name', 'first_name')

    total_class_members = class_members.count()
    members_this_month = class_members.filter(
        date_joined__month=datetime.now().month,
        date_joined__year=datetime.now().year
    ).count()

    recent_members = class_members.order_by('-date_joined')[:10]
    class_events = Event.objects.filter(is_upcoming=True).order_by('date')[:10]
    class_announcements = Announcement.objects.all()[:10]

    context = {
        'member': member,
        'class_members': class_members,
        'total_class_members': total_class_members,
        'members_this_month': members_this_month,
        'recent_members': recent_members,
        'class_events': class_events,
        'class_announcements': class_announcements,
        'settings': settings,
    }

    return render(request, 'class_rep_dashboard.html', context)

def create_class_announcement(request):
    member = get_member_from_session(request)
    if not member or not has_role(member, ['CLASS_REP']):
        messages.error(request, 'Not authorized.')
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        full_title = f"[Class Announcement] {title}"

        Announcement.objects.create(
            title=full_title,
            description=description,
            document=request.FILES.get('document')
        )
        
        messages.success(request, 'Class announcement created!')
        return redirect('class_rep_dashboard')

    return render(request, 'create_class_announcement.html', {'member': member})

def create_class_event(request):
    member = get_member_from_session(request)
    if not member or not has_role(member, ['CLASS_REP']):
        messages.error(request, 'Not authorized.')
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        date = request.POST.get('date')
        venue = request.POST.get('venue')
        full_title = f"[Class Event] {title}"

        Event.objects.create(
            title=full_title,
            description=description,
            date=date,
            venue=venue,
            flyer=request.FILES.get('flyer'),
            is_upcoming=True
        )
        
        messages.success(request, 'Class event created!')
        return redirect('class_rep_dashboard')

    return render(request, 'create_class_event.html', {'member': member})

def export_class_members(request):
    member = get_member_from_session(request)
    if not member or not has_role(member, ['CLASS_REP']):
        messages.error(request, 'Not authorized.')
        return redirect('dashboard')

    class_members = Member.objects.filter(
        is_active=True,
        membership_type='FULL'
    ).order_by('last_name')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="class_members_{datetime.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Phone', 'Registration Number', 'Date Joined'])

    for m in class_members:
        writer.writerow([
            f"{m.first_name} {m.last_name}",
            m.email,
            m.phone_number,
            m.registration_number or '',
            m.date_joined.strftime('%Y-%m-%d')
        ])
    return response

# ==========================================
# RESEARCH LINKS VIEW
# ==========================================

def research_links_view(request):
    """Display all research paper links."""
    papers = ResearchLink.objects.all()
    settings = SiteSettings.load()
    return render(request, 'research_links.html', {'papers': papers, 'settings': settings})

# ==========================================
# MARKETPLACE VIEWS
# ==========================================

def marketplace_view(request):
    """Display all available products."""
    products = Product.objects.filter(is_active=True, stock__gt=0)
    settings = SiteSettings.load()
    return render(request, 'marketplace.html', {
        'products': products,
        'settings': settings
    })

def product_detail_view(request, product_id):
    """Display product details."""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    settings = SiteSettings.load()
    return render(request, 'product_detail.html', {
        'product': product,
        'settings': settings
    })

def add_to_cart(request, product_id):
    """Add product to cart (stored in session)."""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    if not product.is_in_stock():
        messages.error(request, 'Sorry, this product is out of stock.')
        return redirect('marketplace')
    
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        cart[product_id_str]['quantity'] += 1
    else:
        cart[product_id_str] = {
            'name': product.name,
            'price': str(product.price),
            'quantity': 1,
            'image': product.image.url if product.image else None
        }
    
    request.session['cart'] = cart
    messages.success(request, f'{product.name} added to cart!')
    return redirect('marketplace')

def view_cart(request):
    """Display shopping cart."""
    cart = request.session.get('cart', {})
    settings = SiteSettings.load()
    
    cart_items = []
    total = Decimal('0')
    
    for product_id, item in cart.items():
        quantity = item['quantity']
        price = Decimal(item['price'])
        subtotal = price * quantity
        total += subtotal
        
        cart_items.append({
            'product_id': product_id,
            'name': item['name'],
            'price': price,
            'quantity': quantity,
            'subtotal': subtotal,
            'image': item.get('image')
        })
    
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total,
        'settings': settings
    })

def remove_from_cart(request, product_id):
    """Remove item from cart."""
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        del cart[product_id_str]
        request.session['cart'] = cart
        messages.success(request, 'Item removed from cart.')
    
    return redirect('view_cart')

def update_cart_quantity(request, product_id):
    """Update item quantity in cart."""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            if quantity > 0:
                cart[product_id_str]['quantity'] = quantity
            else:
                del cart[product_id_str]
            request.session['cart'] = cart
        
    return redirect('view_cart')

def checkout(request):
    """Process order and create order record."""
    member = get_member_from_session(request)
    if not member:
        messages.error(request, 'Please login to place an order.')
        return redirect('login')
    
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Your cart is empty.')
        return redirect('marketplace')
    
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        
        order = Order.objects.create(
            member=member,
            notes=notes
        )
        
        total = Decimal('0')
        for product_id, item in cart.items():
            product = get_object_or_404(Product, id=product_id)
            quantity = item['quantity']
            price = Decimal(item['price'])
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=price
            )
            
            product.stock -= quantity
            product.save()
            
            total += price * quantity
        
        order.total_amount = total
        order.save()
        
        request.session['cart'] = {}
        
        # Try backend notification (will fail on PA FREE but that's OK)
        send_email_via_web3forms(TECH_EMAIL, f'🛒 New Order: {order.order_number}',
            f'New order from {order.member.first_name} {order.member.last_name}\nTotal: UGX {order.total_amount:,.0f}')
        
        messages.success(request, f'Order #{order.order_number} placed successfully! Total: UGX {total:,.0f}')
        return redirect('order_success', order_id=order.id)
    
    return render(request, 'checkout.html', {'cart': cart})

def order_success(request, order_id):
    """Display order confirmation."""
    order = get_object_or_404(Order, id=order_id)
    settings = SiteSettings.load()
    return render(request, 'order_success.html', {
        'order': order,
        'settings': settings
    })

def my_orders(request):
    """Display member's order history."""
    member = get_member_from_session(request)
    if not member:
        return redirect('login')
    
    orders = Order.objects.filter(member=member).prefetch_related('items__product')
    settings = SiteSettings.load()
    
    return render(request, 'my_orders.html', {
        'orders': orders,
        'settings': settings
    })
