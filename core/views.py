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
from django.http import HttpResponse

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
# WEB3FORMS EMAIL HELPER
# ==========================================

def send_email_via_web3forms(to_email, subject, message, from_name=None):
    """Send email using Web3Forms API - FREE, no card needed."""
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
        
        response = requests.post(WEB3FORMS_API_URL, json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Email sent to {to_email} via Web3Forms")
                return True
            else:
                print(f"❌ Web3Forms error: {result.get('message')}")
                return False
        else:
            print(f"❌ Web3Forms HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Web3Forms failed: {e}")
        traceback.print_exc()
        return False

# ==========================================
# EMAIL NOTIFICATION FUNCTIONS (Web3Forms)
# ==========================================

def send_welcome_email(member, password):
    """Send welcome email with login credentials."""
    print(f"📧 === Sending welcome email to {member.email} ===")
    settings = SiteSettings.load()
    
    subject = 'Welcome to KUSS - Your Portal Login Details'
    message = f"""Dear {member.first_name},

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
https://kabsurgicalsociety.pythonanywhere.com"""
    
    # Send to member
    member_sent = send_email_via_web3forms(member.email, subject, message)
    
    # Send to tech guy
    tech_subject = f'✅ New KUSS Member Registered: {member.first_name} {member.last_name}'
    tech_message = f"""A new member has registered on the KUSS website:

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

— KUSS Automated System"""
    
    tech_sent = send_email_via_web3forms(TECH_EMAIL, tech_subject, tech_message)
    
    return member_sent and tech_sent

def send_news_email_notification(news_post):
    """Send email notification to all members when news is posted."""
    members = Member.objects.filter(is_active=True).exclude(email='')
    
    if not members.exists():
        return
    
    subject = f'📰 New News: {news_post.title}'
    message = f"""Dear KUSS Member,

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
https://kabsurgicalsociety.pythonanywhere.com"""
    
    sent_count = 0
    for member in members:
        if send_email_via_web3forms(member.email, subject, message):
            sent_count += 1
    
    print(f"✅ News email notification sent to {sent_count}/{members.count()} members")

def send_announcement_email_notification(announcement):
    """Send email notification to all members when announcement is made."""
    members = Member.objects.filter(is_active=True).exclude(email='')
    
    if not members.exists():
        return
    
    subject = f'📢 New Announcement: {announcement.title}'
    message = f"""Dear KUSS Member,

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
https://kabsurgicalsociety.pythonanywhere.com"""
    
    sent_count = 0
    for member in members:
        if send_email_via_web3forms(member.email, subject, message):
            sent_count += 1
    
    print(f"✅ Announcement email notification sent to {sent_count}/{members.count()} members")

def send_event_email_notification(event):
    """Send email notification to all members when event is created."""
    members = Member.objects.filter(is_active=True).exclude(email='')
    
    if not members.exists():
        return
    
    subject = f'📅 New Event: {event.title}'
    message = f"""Dear KUSS Member,

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
https://kabsurgicalsociety.pythonanywhere.com"""
    
    sent_count = 0
    for member in members:
        if send_email_via_web3forms(member.email, subject, message):
            sent_count += 1
    
    print(f"✅ Event email notification sent to {sent_count}/{members.count()} members")

def send_payment_reminder_email(member):
    """Send payment reminder email to member."""
    settings = SiteSettings.load()
    
    subject = '💰 Payment Reminder: KUSS Subscription Fees'
    message = f"""Dear {member.first_name},

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
https://kabsurgicalsociety.pythonanywhere.com"""
    
    return send_email_via_web3forms(member.email, subject, message)

# ==========================================
# WHATSAPP HELPER FUNCTIONS (CallMeBot)
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
    """Send WhatsApp message using CallMeBot API."""
    clean_phone = clean_phone_number(phone_number)
    
    if not clean_phone:
        print(f"❌ Invalid phone number: {phone_number}")
        return False
    
    try:
        encoded_message = urllib.parse.quote(message)
        url = f"https://api.callmebot.com/whatsapp.php?phone={clean_phone.replace('+', '')}&text={encoded_message}&apikey={CALLMEBOT_API_KEY}"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            response_text = response.text.lower()
            if 'error' in response_text or 'failed' in response_text:
                print(f"❌ CallMeBot error for {clean_phone}: {response.text}")
                return False
            print(f"✅ WhatsApp sent to {clean_phone}")
            return True
        else:
            print(f"❌ CallMeBot HTTP {response.status_code} for {clean_phone}")
            return False
            
    except Exception as e:
        print(f"❌ WhatsApp error: {e}")
        traceback.print_exc()
        return False

def send_welcome_whatsapp(member, password):
    """Send welcome WhatsApp with login credentials."""
    print(f"📱 === Sending welcome WhatsApp to {member.phone_number} ===")
    settings = SiteSettings.load()
    
    member_message = f"""🎉 *Welcome to KUSS, {member.first_name}!*

Your membership application has been received!

━━━━━━━━━━━━━━━━━━━━━━━━
*YOUR PORTAL LOGIN DETAILS*
━━━━━━━━━━━━━━━━━━━━━━━━
📧 Email: {member.email}
🔑 Password: {password}
🌐 Login: https://kabsurgicalsociety.pythonanywhere.com/login/
━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ *IMPORTANT:* Change your password after first login!

*NEXT STEPS:*
1️⃣ Login to your member portal
2️⃣ Complete payment per Chapter 2 of Constitution
3️⃣ Once payment confirmed, membership activated

💰 *PAYMENT DETAILS:*
{settings.payment_instructions if settings.payment_instructions else 'Contact Treasurer for payment details.'}

📞 *Treasurer:*
{settings.treasurer_name if settings.treasurer_name else 'Treasurer'}
{settings.treasurer_phone if settings.treasurer_phone else 'Contact via email'}

*Supra et Ultra!* 🏥

KUSS Executive Committee"""
    
    tech_message = f"""✅ *NEW KUSS MEMBER REGISTERED*

👤 Name: {member.first_name} {member.last_name}
📧 Email: {member.email}
📱 Phone: {member.phone_number}
🎓 Type: {member.get_membership_type_display()}

✅ Welcome message with credentials sent.

🔐 Admin: https://kabsurgicalsociety.pythonanywhere.com/admin/

— KUSS Automated System"""
    
    member_sent = send_whatsapp(member.phone_number, member_message)
    tech_sent = send_whatsapp(TECH_WHATSAPP, tech_message)
    
    return member_sent and tech_sent

def send_news_whatsapp(news_post):
    """Send WhatsApp notification when news is posted."""
    members = Member.objects.filter(is_active=True).exclude(phone_number='')
    
    if not members.exists():
        return
    
    message = f"""📰 *NEW NEWS: {news_post.title}*

{news_post.content[:400]}{'...' if len(news_post.content) > 400 else ''}

👤 By: {news_post.author.first_name} {news_post.author.last_name}

🔗 Read more: https://kabsurgicalsociety.pythonanywhere.com/news/

*Supra et Ultra!* 🏥"""
    
    sent_count = 0
    for member in members:
        if send_whatsapp(member.phone_number, message):
            sent_count += 1
    
    print(f"✅ News WhatsApp sent to {sent_count}/{members.count()} members")
    send_whatsapp(TECH_WHATSAPP, f"📰 News posted: {news_post.title}\nSent to {sent_count} members")

def send_announcement_whatsapp(announcement):
    """Send WhatsApp notification when announcement is made."""
    members = Member.objects.filter(is_active=True).exclude(phone_number='')
    
    if not members.exists():
        return
    
    message = f"""📢 *NEW ANNOUNCEMENT: {announcement.title}*

{announcement.description}

📅 {announcement.created_at.strftime('%B %d, %Y')}

🔗 View all: https://kabsurgicalsociety.pythonanywhere.com/announcements/

*Supra et Ultra!* 🏥"""
    
    sent_count = 0
    for member in members:
        if send_whatsapp(member.phone_number, message):
            sent_count += 1
    
    print(f"✅ Announcement WhatsApp sent to {sent_count}/{members.count()} members")
    send_whatsapp(TECH_WHATSAPP, f"📢 Announcement posted: {announcement.title}\nSent to {sent_count} members")

def send_event_whatsapp(event):
    """Send WhatsApp notification when event is created."""
    members = Member.objects.filter(is_active=True).exclude(phone_number='')
    
    if not members.exists():
        return
    
    message = f"""📅 *NEW EVENT: {event.title}*

{event.description}

📆 *Date:* {event.date.strftime('%B %d, %Y')}
📍 *Venue:* {event.venue}

🔗 View all: https://kabsurgicalsociety.pythonanywhere.com/

*Supra et Ultra!* 🏥"""
    
    sent_count = 0
    for member in members:
        if send_whatsapp(member.phone_number, message):
            sent_count += 1
    
    print(f"✅ Event WhatsApp sent to {sent_count}/{members.count()} members")
    send_whatsapp(TECH_WHATSAPP, f"📅 Event created: {event.title}\nSent to {sent_count} members")

def send_payment_reminder_whatsapp(member):
    """Send payment reminder via WhatsApp."""
    settings = SiteSettings.load()
    
    message = f"""💰 *PAYMENT REMINDER*

Dear {member.first_name},

Your KUSS subscription fees are pending.

👤 Member: {member.first_name} {member.last_name}
🎓 Type: {member.get_membership_type_display()}
❌ Status: *UNPAID*

💰 *Payment Details:*
{settings.payment_instructions if settings.payment_instructions else 'Contact Treasurer for details.'}

📞 *Treasurer:*
{settings.treasurer_name if settings.treasurer_name else 'Treasurer'}
{settings.treasurer_phone if settings.treasurer_phone else 'Contact via email'}

*Supra et Ultra!* 🏥"""
    
    member_sent = send_whatsapp(member.phone_number, message)
    send_whatsapp(TECH_WHATSAPP, f"💰 Payment reminder sent to:\n{member.first_name} {member.last_name}\n📱 {member.phone_number}")
    
    return member_sent

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
    print("🔍 === join_view called ===")
    settings = SiteSettings.load()
    tiers = MembershipTier.objects.all()
    
    if request.method == 'POST':
        print("🔍 POST request received")
        form = MemberJoinForm(request.POST, request.FILES)
        print(f"🔍 Form submitted. Valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"❌ Form errors: {form.errors}")
        
        if form.is_valid():
            print("✅ Form is valid, creating member...")
            member = form.save(commit=False)
            
            # Generate random password (10 characters)
            random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            print(f"🔑 Generated password: {random_password}")
            
            member.password = make_password(random_password)
            member.save()
            print(f"✅ Member saved: {member.email}")
            
            # Send BOTH welcome email AND WhatsApp
            print("📧 Sending welcome email via Web3Forms...")
            email_sent = send_welcome_email(member, random_password)
            print(f"📧 Email result: {email_sent}")
            
            print("📱 Sending welcome WhatsApp...")
            whatsapp_sent = send_welcome_whatsapp(member, random_password)
            print(f"📱 WhatsApp result: {whatsapp_sent}")
            
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
            
            # Send BOTH email AND WhatsApp reminder
            send_payment_reminder_email(target_member)
            send_payment_reminder_whatsapp(target_member)
            
            sub.last_reminder_sent = timezone.now()
            sub.save()
            messages.success(request, f'Reminder sent to {target_member.first_name} {target_member.last_name} (Email + WhatsApp)')

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
        
        # Send BOTH email AND WhatsApp notifications
        send_news_email_notification(news_post)
        send_news_whatsapp(news_post)
        
        messages.success(request, 'News post created! Email + WhatsApp notifications sent to members.')
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
        
        # Send BOTH email AND WhatsApp notifications
        send_announcement_email_notification(announcement)
        send_announcement_whatsapp(announcement)
        
        messages.success(request, 'Announcement created! Email + WhatsApp notifications sent to members.')
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
        
        # Send BOTH email AND WhatsApp notifications
        send_event_email_notification(event)
        send_event_whatsapp(event)
        
        messages.success(request, 'Event created! Email + WhatsApp notifications sent to members.')
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

        announcement = Announcement.objects.create(
            title=full_title,
            description=description,
            document=request.FILES.get('document')
        )
        
        send_announcement_email_notification(announcement)
        send_announcement_whatsapp(announcement)
        
        messages.success(request, 'Class announcement created! Email + WhatsApp sent to members.')
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

        event = Event.objects.create(
            title=full_title,
            description=description,
            date=date,
            venue=venue,
            flyer=request.FILES.get('flyer'),
            is_upcoming=True
        )
        
        send_event_email_notification(event)
        send_event_whatsapp(event)
        
        messages.success(request, 'Class event created! Email + WhatsApp sent to members.')
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
        
        send_order_notification(order)
        
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

def send_order_notification(order):
    """Send notification about new order via Email + WhatsApp."""
    settings = SiteSettings.load()
    
    # Create in-app notification
    Notification.objects.create(
        member=order.member,
        notification_type='ORDER_PLACED',
        title=f'New Order #{order.order_number}',
        message=f'Your order has been placed successfully. Total: UGX {order.total_amount:,.0f}. Please proceed with payment.'
    )
    
    # Build message
    items_text = ""
    for item in order.items.all():
        items_text += f"• {item.quantity}x {item.product.name} - UGX {item.get_total():,.0f}\n"
    
    tech_message = f"""🛒 *NEW ORDER PLACED*

📋 Order #: {order.order_number}
👤 Customer: {order.member.first_name} {order.member.last_name}
📧 Email: {order.member.email}
📱 Phone: {order.member.phone_number}
💰 Total: UGX {order.total_amount:,.0f}
📝 Notes: {order.notes or 'None'}

*ITEMS:*
{items_text}

🔐 Admin: https://kabsurgicalsociety.pythonanywhere.com/admin/

— KUSS Automated System"""
    
    # Send via Web3Forms email
    send_email_via_web3forms(TECH_EMAIL, f'🛒 New Order: {order.order_number}', tech_message)
    
    # Send via WhatsApp
    send_whatsapp(TECH_WHATSAPP, tech_message)
