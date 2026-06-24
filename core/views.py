# core/views.py
import re
import csv
from decimal import Decimal
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncMonth
from django.http import HttpResponse

from .models import (
    NewsPost, Announcement, Leadership, Member, FoundingMember, 
    MembershipTier, Event, SiteSettings, Subscription, Notification,
    Transaction, TransactionCategory
)
from .forms import MemberJoinForm, MemberLoginForm, MemberProfileForm

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
    
    # Get latest notifications for the member
    notifications = Notification.objects.filter(member=member)[:10]
    
    return render(request, 'dashboard.html', {
        'member': member,
        'upcoming_events': upcoming_events,
        'latest_news': latest_news,
        'latest_announcements': latest_announcements,
        'member_roles': member_roles,
        'notifications': notifications,
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

def treasurer_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            member = Member.objects.get(email=email)
            if is_treasurer(member) and member.password and check_password(password, member.password):
                request.session['treasurer_id'] = member.id
                return redirect('treasurer_dashboard')
            messages.error(request, 'Invalid credentials or not authorized as Treasurer.')
        except Member.DoesNotExist:
            messages.error(request, 'Invalid credentials.')
            
    return render(request, 'treasurer_login.html')

def treasurer_logout(request):
    if 'treasurer_id' in request.session:
        del request.session['treasurer_id']
    return redirect('home')

def treasurer_dashboard(request):
    treasurer_id = request.session.get('treasurer_id')
    if not treasurer_id:
        return redirect('treasurer_login')
    
    treasurer = get_object_or_404(Member, id=treasurer_id)
    if not is_treasurer(treasurer):
        messages.error(request, 'You are not authorized to access the Treasurer dashboard.')
        return redirect('dashboard')
    
    current_year = datetime.now().year
    
    # Financial Summary
    total_income = Transaction.objects.filter(transaction_type='INCOME', date__year=current_year).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_expenses = Transaction.objects.filter(transaction_type='EXPENSE', date__year=current_year).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    cash_at_hand = total_income - total_expenses
    
    # Monthly Data for Charts
    monthly_income = list(Transaction.objects.filter(transaction_type='INCOME', date__year=current_year)
                          .annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month'))
    
    monthly_expenses = list(Transaction.objects.filter(transaction_type='EXPENSE', date__year=current_year)
                            .annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month'))
    
    # Category Breakdowns
    income_by_category = list(Transaction.objects.filter(transaction_type='INCOME', date__year=current_year)
                              .values('category__name').annotate(total=Sum('amount')).order_by('-total'))
    
    expense_by_category = list(Transaction.objects.filter(transaction_type='EXPENSE', date__year=current_year)
                               .values('category__name').annotate(total=Sum('amount')).order_by('-total'))
    
    # Recent Transactions
    recent_transactions = Transaction.objects.select_related('category', 'recorded_by')[:10]
    
    # Membership Subscription Stats
    total_members = Member.objects.filter(is_active=True).count()
    paid_members = Subscription.objects.filter(is_paid=True, member__is_active=True).count()
    
    return render(request, 'treasurer_dashboard.html', {
        'treasurer': treasurer,
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
    })

def transaction_list(request):
    treasurer_id = request.session.get('treasurer_id')
    if not treasurer_id or not is_treasurer(get_object_or_404(Member, id=treasurer_id)):
        return redirect('treasurer_login')
    
    transactions = Transaction.objects.select_related('category', 'recorded_by').all()
    categories = TransactionCategory.objects.filter(is_active=True)
    
    # Filtering
    t_type = request.GET.get('type')
    if t_type: transactions = transactions.filter(transaction_type=t_type)
    
    cat_id = request.GET.get('category')
    if cat_id: transactions = transactions.filter(category_id=cat_id)
    
    date_from = request.GET.get('date_from')
    if date_from: transactions = transactions.filter(date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to: transactions = transactions.filter(date__lte=date_to)
    
    return render(request, 'treasurer_transactions.html', {
        'transactions': transactions,
        'categories': categories,
        'filters': {'type': t_type, 'category': cat_id, 'date_from': date_from, 'date_to': date_to}
    })

def add_transaction(request):
    treasurer_id = request.session.get('treasurer_id')
    if not treasurer_id: return redirect('treasurer_login')
    treasurer = get_object_or_404(Member, id=treasurer_id)
    if not is_treasurer(treasurer): return redirect('dashboard')
    
    if request.method == 'POST':
        Transaction.objects.create(
            transaction_type=request.POST.get('transaction_type'),
            category_id=request.POST.get('category'),
            amount=Decimal(request.POST.get('amount', 0)),
            description=request.POST.get('description'),
            reference_number=request.POST.get('reference_number'),
            date=request.POST.get('date'),
            recorded_by=treasurer
        )
        messages.success(request, 'Transaction recorded successfully.')
        return redirect('transaction_list')
    
    categories = TransactionCategory.objects.filter(is_active=True)
    return render(request, 'treasurer_add_transaction.html', {'categories': categories})

def toggle_subscription(request, member_id):
    treasurer_id = request.session.get('treasurer_id')
    if not treasurer_id: return redirect('treasurer_login')
    if not is_treasurer(get_object_or_404(Member, id=treasurer_id)): return redirect('dashboard')
    
    member = get_object_or_404(Member, id=member_id)
    sub, _ = Subscription.objects.get_or_create(member=member)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_paid':
            sub.is_paid = not sub.is_paid
            if sub.is_paid:
                sub.payment_date = timezone.now().date()
                for tier in MembershipTier.objects.all():
                    if tier.name.lower() in member.membership_type.lower():
                        sub.amount_paid = tier.subscription_fee
                        break
            else:
                sub.payment_date = None
                sub.amount_paid = Decimal('0')
            sub.save()
            messages.success(request, f'Subscription updated for {member.first_name} {member.last_name}')
            
        elif action == 'send_reminder':
            Notification.objects.create(
                member=member,
                notification_type='PAYMENT_REMINDER',
                title='Subscription Fee Reminder',
                message=f'Dear {member.first_name}, this is a reminder to pay your subscription fees. Please check the Treasurer portal or contact us for payment details.'
            )
            sub.last_reminder_sent = timezone.now()
            sub.save()
            messages.success(request, f'Reminder sent to {member.first_name} {member.last_name}')
            
    return redirect('treasurer_dashboard')

# ==========================================
# EXPORT VIEWS
# ==========================================

def export_transactions(request):
    treasurer_id = request.session.get('treasurer_id')
    if not treasurer_id: return redirect('treasurer_login')
    if not is_treasurer(get_object_or_404(Member, id=treasurer_id)): return redirect('dashboard')
    
    transactions = Transaction.objects.select_related('category', 'recorded_by').all()
    
    # Apply same filters as list view
    t_type = request.GET.get('type')
    if t_type: transactions = transactions.filter(transaction_type=t_type)
    date_from = request.GET.get('date_from')
    if date_from: transactions = transactions.filter(date__gte=date_from)
    date_to = request.GET.get('date_to')
    if date_to: transactions = transactions.filter(date__lte=date_to)
    
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
    treasurer_id = request.session.get('treasurer_id')
    if not treasurer_id: return redirect('treasurer_login')
    if not is_treasurer(get_object_or_404(Member, id=treasurer_id)): return redirect('dashboard')
    
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
