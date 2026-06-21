# core/models.py
from django.db import models

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
    
    contact_email = models.EmailField(default="info@kuss.ac.ug")
    contact_phone = models.CharField(max_length=20, blank=True, null=True, help_text="e.g., +256 700 123 456")
    contact_location = models.CharField(max_length=200, default="Kabale, Uganda")
    
    facebook_url = models.URLField(blank=True, null=True, help_text="Full URL to Facebook page")
    twitter_url = models.URLField(blank=True, null=True, help_text="Full URL to X/Twitter profile")
    instagram_url = models.URLField(blank=True, null=True, help_text="Full URL to Instagram profile")
    linkedin_url = models.URLField(blank=True, null=True, help_text="Full URL to LinkedIn page")
    
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