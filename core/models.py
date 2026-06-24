# core/models.py
from django.db import models
from django.db.models import Sum, Count, Q
from decimal import Decimal


class Member(models.Model):
    MEMBERSHIP_CHOICES = [
        ('FULL', 'Full Member (MBChB Student)'),
        ('HONORARY', 'Honorary Member (Medical Practitioner)'),
        ('ASSOCIATE', 'Associate Member (Non-medical/Well-wisher)'),
        ('CORPORATE', 'Corporate Member (Organization/Donor)'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=50, unique=True, blank=True, null=True) 
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    password = models.CharField(max_length=128, blank=True, null=True, help_text="Set a password for portal access.")
    bio = models.TextField(blank=True, null=True, help_text="Short biography or interests.")
    profile_picture = models.FileField(upload_to='member_pics/', blank=True, null=True)
    
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_CHOICES, default='FULL')
    date_joined = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True, help_text="Uncheck to mark as resigned/suspended.")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_membership_type_display()})"


class Leadership(models.Model):
    ROLE_CHOICES = [
        ('PATRON', 'Patron'),
        ('BOARD_CHAIR', 'Board of Governors - Chairperson'),
        ('BOARD_TREASURER', 'Board of Governors - Treasurer'),
        ('BOARD_STUDENT_REP', 'Board of Governors - Student Rep'),
        ('BOARD_UNI_ADMIN', 'Board of Governors - University Admin'),
        ('EXEC_CHAIR', 'Executive - Chairperson'),
        ('EXEC_VICE_CHAIR', 'Executive - Vice Chairperson'),
        ('EXEC_GEN_SEC', 'Executive - General Secretary'),
        ('EXEC_TREASURER', 'Executive - Treasurer'),
        ('EXEC_PUB_SEC', 'Executive - Publicity Secretary'),
        ('COMM_EDU', 'Standing Committee - Education Chair'),
        ('COMM_RES', 'Standing Committee - Research Chair'),
        ('COMM_MEN', 'Standing Committee - Mentorship & Advocacy Chair'),
        ('CLASS_REP', 'Class Representative'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='leadership_roles')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    term_start = models.DateField()
    term_end = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=True, help_text="Check if they are currently in office.")

    class Meta:
        ordering = ['role']

    def __str__(self):
        return f"{self.member.first_name} {self.member.last_name} - {self.get_role_display()}"


class NewsPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.FileField(upload_to='news_images/', help_text="Upload the main image for the news post.")
    author = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, help_text="Who wrote this?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True, help_text="Brief context about the document.")
    document = models.FileField(upload_to='announcements_docs/', help_text="Upload PDF, Word, or Image.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class FoundingMember(models.Model):
    name = models.CharField(max_length=200)
    role_in_commission = models.CharField(max_length=100, help_text="e.g., Patron, Vision Bearer, Commissioner")
    bio_or_contribution = models.TextField(blank=True, null=True, help_text="Their specific role or contribution to founding KUSS.")
    picture = models.FileField(upload_to='founders/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Founding Members"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.role_in_commission})"


class MembershipTier(models.Model):
    name = models.CharField(max_length=50, help_text="e.g., Full Member, Honorary Member")
    entrance_fee = models.DecimalField(max_digits=10, decimal_places=2, help_text="Once-off fee in UGX")
    subscription_fee = models.DecimalField(max_digits=10, decimal_places=2, help_text="Per semester fee in UGX")
    eligibility = models.TextField(help_text="Who qualifies for this membership? (e.g., Registered MBChB students)")

    class Meta:
        verbose_name_plural = "Membership Tiers & Fees"
        ordering = ['name']

    def __str__(self):
        return self.name


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField(blank=True, null=True)
    venue = models.CharField(max_length=200)
    flyer = models.FileField(upload_to='event_flyers/', blank=True, null=True, help_text="Upload event flyer or poster")
    is_upcoming = models.BooleanField(default=True, help_text="Uncheck if the event has already passed.")

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.title} ({self.date})"


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default="Kabale University Surgical Society")
    logo = models.FileField(upload_to='site_logos/', blank=True, null=True, help_text="Upload the official KUSS logo")
    motto = models.CharField(max_length=200, default="Supra et Ultra - Above and Beyond")
    
    # Contact Info
    contact_email = models.EmailField(default="info@kuss.ac.ug")
    contact_phone = models.CharField(max_length=20, blank=True, null=True, help_text="e.g., +256 700 123 456")
    contact_location = models.CharField(max_length=200, default="Kabale, Uganda")
    
    # Social Media
    facebook_url = models.URLField(blank=True, null=True, help_text="Full URL to Facebook page")
    twitter_url = models.URLField(blank=True, null=True, help_text="Full URL to X/Twitter profile")
    instagram_url = models.URLField(blank=True, null=True, help_text="Full URL to Instagram profile")
    linkedin_url = models.URLField(blank=True, null=True, help_text="Full URL to LinkedIn page")
    
    # WhatsApp & IT Support
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True, help_text="WhatsApp number with country code, e.g., +256772123456")
    it_support_message = models.TextField(blank=True, null=True, default="For member portal passwords and technical support, contact IT via WhatsApp")
    
    # Treasurer & Payment Info
    treasurer_name = models.CharField(max_length=100, blank=True, null=True, help_text="Name of the current Treasurer")
    treasurer_phone = models.CharField(max_length=20, blank=True, null=True, help_text="Treasurer's phone/Mobile Money number for fees")
    payment_instructions = models.TextField(blank=True, null=True, help_text="Bank account details, Mobile Money instructions, etc.")
    
    # Join Success Page Customization
    success_message = models.TextField(blank=True, null=True, default="Thank you for joining KUSS! Your membership application has been received. We will review your details and contact you soon.")
    success_button_text = models.CharField(max_length=50, blank=True, null=True, default="Return to Home")
    success_button_url = models.CharField(max_length=200, blank=True, null=True, default="home", help_text="URL name (e.g., 'home', 'dashboard') or full URL")
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return "Site Settings"
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


# ============================================
# NEW FINANCIAL MANAGEMENT MODELS
# ============================================

class Subscription(models.Model):
    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='subscription')
    is_paid = models.BooleanField(default=False, help_text="Check if member has paid their subscription")
    payment_date = models.DateField(blank=True, null=True, help_text="Date when subscription was paid")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Amount paid in UGX")
    notes = models.TextField(blank=True, null=True, help_text="Any notes about the payment")
    last_reminder_sent = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
    
    def __str__(self):
        status = "Paid" if self.is_paid else "Unpaid"
        return f"{self.member.first_name} {self.member.last_name} - {status}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('PAYMENT_REMINDER', 'Payment Reminder'),
        ('GENERAL', 'General Notification'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='GENERAL')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.member.first_name} - {self.title}"


class TransactionCategory(models.Model):
    CATEGORY_TYPES = [
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
    ]
    
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Transaction Categories"
        ordering = ['category_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
    ]
    
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    category = models.ForeignKey(TransactionCategory, on_delete=models.SET_NULL, null=True, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    reference_number = models.CharField(max_length=50, blank=True, null=True, help_text="Receipt number, transaction ID, etc.")
    date = models.DateField()
    recorded_by = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, related_name='recorded_transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.amount} - {self.description[:50]}"


class Budget(models.Model):
    category = models.ForeignKey(TransactionCategory, on_delete=models.CASCADE, related_name='budgets')
    year = models.IntegerField()
    month = models.IntegerField(blank=True, null=True, help_text="Leave blank for annual budget")
    planned_amount = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['category', 'year', 'month']
        ordering = ['-year', '-month']
    
    def __str__(self):
        period = f"{self.year}-{self.month:02d}" if self.month else str(self.year)
        return f"{self.category.name} - {period}: {self.planned_amount}"
    
    @property
    def actual_amount(self):
        transactions = self.category.transactions.filter(
            date__year=self.year
        )
        if self.month:
            transactions = transactions.filter(date__month=self.month)
        
        return transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    @property
    def variance(self):
        return self.planned_amount - self.actual_amount
    
    @property
    def variance_percentage(self):
        if self.planned_amount == 0:
            return 0
        return ((self.planned_amount - self.actual_amount) / self.planned_amount) * 100


class FinancialReport(models.Model):
    REPORT_TYPES = [
        ('MONTHLY', 'Monthly Summary'),
        ('QUARTERLY', 'Quarterly Summary'),
        ('ANNUAL', 'Annual Summary'),
        ('CUSTOM', 'Custom Period'),
    ]
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    generated_by = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.start_date} to {self.end_date})"
