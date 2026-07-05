# core/views.py
import re
import csv
import random
import string
from decimal import Decimal
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.core.mail import send_mail

from .models import (
    NewsPost, Announcement, Leadership, Member, FoundingMember, 
    MembershipTier, Event, SiteSettings, Subscription, Notification,
    Transaction, TransactionCategory, ResearchLink
)
from .forms import MemberJoinForm, MemberLoginForm, MemberProfileForm

# Email configuration
TECH_EMAIL = 'tumusiimekevin3@gmail.com'
FROM_EMAIL = 'KUSS <tumusiimekevin3@gmail.com>'

# ==========================================
# EMAIL HELPER FUNCTIONS
# ==========================================

def send_welcome_email(member, password):
    """Send welcome email with login credentials to new member."""
    settings = SiteSettings.load()
    
    subject = 'Welcome to KUSS - Your Portal Login Details'
    message = f'''Dear {member.first_name},

Welcome to the Kabale University Surgical Society (KUSS)!

Your membership application has been received successfully.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR PORTAL LOGIN DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Email: {member.email}
Password: {password}
Login URL: https://kabsurgicalsociety.pythonanywhere.com/login/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPORTANT: Please change your password after first login for security.

NEXT STEPS:
1. Login to your member portal using the credentials above
2. Complete your payment as per Chapter 2 of the Constitution
3. Once payment is confirmed by the Treasurer, your membership will be fully activated

PAYMENT DETAILS:
{settings.payment_instructions if settings.payment_instructions else 'Contact the Treasurer for payment details.'}

Treasurer Contact:
{settings.treasurer_name if settings.treasurer_name else 'Treasurer'}
{settings.treasurer_phone if settings.treasurer_phone else 'Contact via email'}

If you have any questions, contact:
- General Secretary: {settings.contact_email or 'kabsurgicalsociety@gmail.com'}
- IT Support: {settings.whatsapp_number or 'Contact via email'}

Supra et Ultra!

The KUSS Executive Committee
Kabale University Surgical Society
https://kabsurgicalsociety.pythonanywhere.com'''
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=FROM_EMAIL,
            recipient_list=[member.email],
            fail_silently=False,
        )
        print(f"✅ Welcome email sent to {member.email}")
        
        # Notify tech guy
        send_mail(
            subject=f'✅ New KUSS Member Registered: {member.first_name} {member.last_name}',
            message=f'''A new member has registered on the KUSS website:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MEMBER DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: {member.first_name} {member.last_name}
Email: {member.email}
Phone: {member.phone_number}
Membership Type: {member.get_membership_type_display()}
Registration Number: {member.registration_number or 'Not provided'}
Date: {member.date_joined}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Welcome email with login credentials has been sent automatically.

ACTION REQUIRED:
- Monitor payment status in Treasurer Dashboard
- Activate membership once payment is confirmed

Admin Panel: https://kabsurgicalsociety.pythonanywhere.com/admin/

— KUSS Automated System''',
            from_email=FROM_EMAIL,
            recipient_list=[TECH_EMAIL],
            fail_silently=True,
        )
        return True
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False

def send_news_notification(news_post):
    """Send email notification to all members when news is posted."""
    members = Member.objects.filter(is_active=True).exclude(email='')
    
    if not members.exists():
        return
    
    subject = f'📰 New News: {news_post.title}'
    message = f'''Dear KUSS Member,

A new news article has been posted on the KUSS website:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{news_post.title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{news_post.content[:500]}{'...' if len(news_post.content) > 500 else ''}

Posted by: {news_post.author.first_name} {news_post.author.last_name}
Date: {news_post.created_at.strftime('%B %d, %Y')}

Read the full article: https://kabsurgicalsociety.pythonanywhere.com/news/

Stay updated with the latest from KUSS!

Supra et Ultra!

The KUSS Executive Committee
https://kabsurgicalsociety.pythonanywhere.com'''
    
    # Send to all members using BCC
    recipient_emails = list(members.values_list('email', flat=True))
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=FROM_EMAIL,
            recipient_list=[],  # Empty To field
            bcc=recipient_emails,  # Use BCC to protect privacy
            fail_silently=True,
        )
        print(f"✅ News notification sent to {len(recipient_emails)} members")
        
        # Notify tech guy
        send_mail(
            subject=f'📰 News Posted: {news_post.title}',
            message=f'''A new news article has been posted:

Title: {news_post.title}
Author: {news_post.author.first_name} {news_post.author.last_name}
Date: {news_post.created_at}

Notification sent to {len(recipient_emails)} members.

View article: https://kabsurgicalsociety.pythonanywhere.com/news/

— KUSS Automated System''',
            from_email=FROM_EMAIL,
            recipient_list=[TECH_EMAIL],
            fail_silently=True,
        )
    except Exception as e:
        print(f"❌ News notification failed: {e}")

def send_announcement_notification(announcement):
    """Send email notification to all members when announcement is made."""
    members = Member.objects.filter(is_active=True).exclude(email='')
    
    if not members.exists():
        return
    
    subject = f'📢 New Announcement: {announcement.title}'
    message = f'''Dear KUSS Member,

A new announcement has been posted:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{announcement.title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{announcement.description}

Date: {announcement.created_at.strftime('%B %d, %Y')}

View all announcements: https://kabsurgicalsociety.pythonanywhere.com/announcements/

Please take note of this important information.

Supra et Ultra!

The KUSS Executive Committee
https://kabsurgicalsociety.pythonanywhere.com'''
    
    recipient_emails = list(members.values_list('email', flat=True))
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=FROM_EMAIL,
            recipient_list=[],
            bcc=recipient_emails,
            fail_silently=True,
        )
        print(f"✅ Announcement notification sent to {len(recipient_emails)} members")
        
        # Notify tech guy
        send_mail(
            subject=f'📢 Announcement Posted: {announcement.title}',
            message=f'''A new announcement has been posted:

Title: {announcement.title}
Date: {announcement.created_at}

Notification sent to {len(recipient_emails)} members.

View announcement: https://kabsurgicalsociety.pythonanywhere.com/announcements/

— KUSS Automated System''',
            from_email=FROM_EMAIL,
            recipient_list=[TECH_EMAIL],
            fail_silently=True,
        )
    except Exception as e:
        print(f"❌ Announcement notification failed: {e}")

def send_event_notification(event):
    """Send email notification to all members when event is created."""
    members = Member.objects.filter(is_active=True).exclude(email='')
    
    if not members.exists():
        return
    
    subject = f'📅 New Event: {event.title}'
    message = f'''Dear KUSS Member,

A new event has been scheduled:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{event.title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{event.description}

Date: {event.date.strftime('%B %d, %Y')}
Venue: {event.venue}

View all events: https://kabsurgicalsociety.pythonanywhere.com/

Don't miss out! Mark your calendar and attend.

Supra et Ultra!

The KUSS Executive Committee
https://kabsurgicalsociety.pythonanywhere.com'''
    
    recipient_emails = list(members.values_list('email', flat=True))
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=FROM_EMAIL,
            recipient_list=[],
            bcc=recipient_emails,
            fail_silently=True,
        )
        print(f"✅ Event notification sent to {len(recipient_emails)} members")
        
        # Notify tech guy
        send_mail(
            subject=f'📅 Event Created: {event.title}',
            message=f'''A new event has been created:

Title: {event.title}
Date: {event.date}
Venue: {event.venue}

Notification sent to {len(recipient_emails)} members.

View event: https://kabsurgicalsociety.pythonanywhere.com/

— KUSS Automated System''',
            from_email=FROM_EMAIL,
            recipient_list=[TECH_EMAIL],
            fail_silently=True,
        )
    except Exception as e:
        print(f"❌ Event notification failed: {e}")

def send_payment_reminder_email(member):
    """Send payment reminder email to member."""
    settings = SiteSettings.load()
    
    subject = '💰 Payment Reminder: KUSS Subscription Fees'
    message = f'''Dear {member.first_name},

This is a friendly reminder that your KUSS subscription fees are pending.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAYMENT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Member: {member.first_name} {member.last_name}
Email: {member.email}
Membership Type: {member.get_membership_type_display()}
Status: UNPAID
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

As per Chapter 2 of the KUSS Constitution, all members are required to pay their subscription fees to maintain active membership status.

{settings.payment_instructions if settings.payment_instructions else 'Please contact the Treasurer for payment details.'}

Treasurer Contact:
{settings.treasurer_name if settings.treasurer_name else 'Treasurer'}
{settings.treasurer_phone if settings.treasurer_phone else 'Contact via email'}

IMPORTANT:
- Members with unpaid fees may lose voting rights and access to society activities
- Please clear your dues at your earliest convenience
- Once payment is confirmed, your membership will be fully activated

If you have already made payment, please contact the Treasurer with your payment confirmation.

Thank you for your prompt attention to this matter.

Supra et Ultra!

The KUSS Executive Committee
Kabale University Surgical Society
https://kabsurgicalsociety.pythonanywhere.com'''
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=FROM_EMAIL,
            recipient_list=[member.email],
            fail_silently=True,
        )
        print(f"✅ Payment reminder sent to {member.email}")
        
        # Notify tech guy
        send_mail(
            subject=f'💰 Payment Reminder Sent: {member.first_name} {member.last_name}',
            message=f'''A payment reminder has been sent to:

Member: {member.first_name} {member.last_name}
Email: {member.email}
Phone: {member.phone_number}

— KUSS Automated System''',
            from_email=FROM_EMAIL,
            recipient_list=[TECH_EMAIL],
            fail_silently=True,
        )
        return True
    except Exception as e:
        print(f"❌ Payment reminder email failed: {e}")
        return False

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
            
            # Send welcome email with credentials
            send_welcome_email(member, random_password)
            
            return redirect('join_success')
    else:
        form = MemberJoinForm()
    
    return render(request, 'join.html', {
        'form': form,
        'settings': settings,
        'tiers': tiers,
    })

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

                    # Redirect based on role
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

    # Get notifications for this member
    notifications = Notification.objects.filter(member=member).order_by('-created_at')[:10]

    # Check if this member is a Treasurer
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

    # Get all members for subscription management table
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

    # Filtering
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
                message=f'Dear {target_member.first_name}, this is a reminder to pay your subscription fees. Please check the Treasurer portal or contact us for payment details.'
            )
            
            # Send email notification
            send_payment_reminder_email(target_member)
            
            sub.last_reminder_sent = timezone.now()
            sub.save()
            messages.success(request, f'Reminder sent to {target_member.first_name} {target_member.last_name} (Email + In-app notification)')

    return redirect('treasurer_dashboard')

def export_transactions(request):
    member = get_member_from_session(request)
    if not member or not is_treasurer(member):
        return redirect('login')

    transactions = Transaction.objects.select_related('category', 'recorded_by').all()

    # Apply same filters as list view
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
    """Main portal for all leaders (except Treasurer who has their own dashboard)."""
    member = get_member_from_session(request)
    if not member:
        return redirect('login')

    if not is_leader(member):
        messages.error(request, 'You do not have leadership access.')
        return redirect('dashboard')

    roles = get_leader_roles(member)
    settings = SiteSettings.load()

    # Gather data based on roles
    context = {
        'member': member,
        'roles': roles,
        'role_display': [Leadership(role=r).get_role_display() for r in roles],
        'settings': settings,
    }

    # Data for Executive roles
    if has_role(member, ['EXEC_CHAIR', 'EXEC_VICE_CHAIR', 'EXEC_GEN_SEC', 'EXEC_PUB_SEC',
                         'BOARD_CHAIR', 'BOARD_TREASURER', 'BOARD_STUDENT_REP', 'BOARD_UNI_ADMIN', 'PATRON']):
        context['total_members'] = Member.objects.filter(is_active=True).count()
        context['recent_members'] = Member.objects.filter(is_active=True).order_by('-date_joined')[:10]
        context['all_leaders'] = Leadership.objects.filter(is_current=True).select_related('member')
        context['upcoming_events'] = Event.objects.filter(is_upcoming=True)[:5]

    # Data for General Secretary
    if has_role(member, ['EXEC_GEN_SEC']):
        context['all_members'] = Member.objects.filter(is_active=True).order_by('last_name')

    # Data for Publicity Secretary
    if has_role(member, ['EXEC_PUB_SEC']):
        context['news_posts'] = NewsPost.objects.all()[:10]
        context['announcements'] = Announcement.objects.all()[:10]

    # Data for Education Chair
    if has_role(member, ['COMM_EDU']):
        context['events'] = Event.objects.all().order_by('-date')[:10]

    # Data for Research Chair
    if has_role(member, ['COMM_RES']):
        context['research_news'] = NewsPost.objects.all()[:10]

    # Data for Mentorship Chair
    if has_role(member, ['COMM_MEN']):
        context['mentorship_members'] = Member.objects.filter(is_active=True)[:20]

    # Data for Class Rep
    if has_role(member, ['CLASS_REP']):
        context['class_members'] = Member.objects.filter(is_active=True, membership_type='FULL')[:50]

    return render(request, 'leadership_portal.html', context)

def create_news_post(request):
    """Publicity Secretary, Research Chair, and all Committee Chairs can create news."""
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
        
        # Send email notification to all members
        send_news_notification(news_post)
        
        messages.success(request, 'News post created successfully! Email notification sent to all members.')
        return redirect('leadership_portal')
    
    return render(request, 'create_news.html', {'member': member})

def create_announcement(request):
    """General Secretary, Publicity Secretary, and all Committee Chairs can create announcements."""
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
        
        # Send email notification to all members
        send_announcement_notification(announcement)
        
        messages.success(request, 'Announcement created successfully! Email notification sent to all members.')
        return redirect('leadership_portal')
    
    return render(request, 'create_announcement.html', {'member': member})

def create_event(request):
    """All Committee Chairs and executives can create events."""
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
        
        # Send email notification to all members
        send_event_notification(event)
        
        messages.success(request, 'Event created successfully! Email notification sent to all members.')
        return redirect('leadership_portal')
    
    return render(request, 'create_event.html', {'member': member})

def export_members_csv(request):
    """General Secretary and Chair can export member list."""
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
# CLASS REP SPECIFIC VIEWS
# ==========================================

def class_rep_dashboard(request):
    """Enhanced dashboard for Class Representatives."""
    member = get_member_from_session(request)
    if not member or not has_role(member, ['CLASS_REP']):
        messages.error(request, 'Not authorized.')
        return redirect('dashboard')

    settings = SiteSettings.load()

    # Get all class members (Full Members only)
    class_members = Member.objects.filter(
        is_active=True,
        membership_type='FULL'
    ).order_by('last_name', 'first_name')

    # Statistics
    total_class_members = class_members.count()
    members_this_month = class_members.filter(
        date_joined__month=datetime.now().month,
        date_joined__year=datetime.now().year
    ).count()

    # Recent joiners
    recent_members = class_members.order_by('-date_joined')[:10]

    # Class events
    class_events = Event.objects.filter(is_upcoming=True).order_by('date')[:10]

    # Class announcements
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
    """Class Reps can create announcements for their class."""
    member = get_member_from_session(request)
    if not member or not has_role(member, ['CLASS_REP']):
        messages.error(request, 'Not authorized.')
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')

        # Add class rep identifier to title
        full_title = f"[Class Announcement] {title}"

        announcement = Announcement.objects.create(
            title=full_title,
            description=description,
            document=request.FILES.get('document')
        )
        
        # Send email notification to all members
        send_announcement_notification(announcement)
        
        messages.success(request, 'Class announcement created successfully! Email notification sent to all members.')
        return redirect('class_rep_dashboard')

    return render(request, 'create_class_announcement.html', {'member': member})

def create_class_event(request):
    """Class Reps can create events for their class."""
    member = get_member_from_session(request)
    if not member or not has_role(member, ['CLASS_REP']):
        messages.error(request, 'Not authorized.')
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        date = request.POST.get('date')
        venue = request.POST.get('venue')

        # Add class identifier to title
        full_title = f"[Class Event] {title}"

        event = Event.objects.create(
            title=full_title,
            description=description,
            date=date,
            venue=venue,
            flyer=request.FILES.get('flyer'),
            is_upcoming=True
        )
        
        # Send email notification to all members
        send_event_notification(event)
        
        messages.success(request, 'Class event created successfully! Email notification sent to all members.')
        return redirect('class_rep_dashboard')

    return render(request, 'create_class_event.html', {'member': member})

def export_class_members(request):
    """Class Reps can export their class member list."""
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

def research_links_view(request):
    """Display all research paper links."""
    papers = ResearchLink.objects.all()
    settings = SiteSettings.load()
    return render(request, 'research_links.html', {'papers': papers, 'settings': settings})
