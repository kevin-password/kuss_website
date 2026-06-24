# core/admin.py
from django.contrib import admin
from django.contrib.auth.hashers import make_password
from .models import (
    Member, Leadership, NewsPost, Announcement, FoundingMember, 
    MembershipTier, Event, SiteSettings, Subscription, Notification,
    TransactionCategory, Transaction, Budget, FinancialReport
)

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone_number', 'membership_type', 'is_active', 'has_password')
    list_filter = ('membership_type', 'is_active', 'date_joined')
    search_fields = ('first_name', 'last_name', 'email', 'registration_number', 'phone_number')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'profile_picture', 'bio')
        }),
        ('Contact & Account Details', {
            'fields': ('email', 'phone_number', 'registration_number', 'membership_type', 'is_active')
        }),
        ('Portal Access', {
            'fields': ('password',),
            'description': 'Set a password so this member can log into the Member Portal. Type the plain password here — it will be automatically encrypted when saved.'
        }),
    )

    @admin.display(description='Has Password', boolean=True)
    def has_password(self, obj):
        return bool(obj.password)

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data and obj.password:
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)

@admin.register(Leadership)
class LeadershipAdmin(admin.ModelAdmin):
    list_display = ('member', 'get_member_phone', 'role', 'term_start', 'is_current')
    list_filter = ('role', 'is_current')
    search_fields = ('member__first_name', 'member__last_name', 'member__phone_number')

    @admin.display(description='Phone Number', ordering='member__phone_number')
    def get_member_phone(self, obj):
        return obj.member.phone_number

@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'content')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'description')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'venue', 'is_upcoming')
    list_filter = ('is_upcoming', 'date')
    search_fields = ('title', 'description', 'venue')

@admin.register(FoundingMember)
class FoundingMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'role_in_commission')
    search_fields = ('name', 'role_in_commission')

@admin.register(MembershipTier)
class MembershipTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'entrance_fee', 'subscription_fee')
    search_fields = ('name',)

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'contact_email', 'contact_phone')
    fieldsets = (
        ('General Site Information', {
            'fields': ('site_name', 'logo', 'motto')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'contact_location')
        }),
        ('Social Media Links', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url'),
            'description': 'Enter full URLs (e.g., https://facebook.com/kuss)'
        }),
        ('WhatsApp & IT Support', {
            'fields': ('whatsapp_number', 'it_support_message'),
            'description': 'Configure IT support contact for member portal issues'
        }),
        ('Treasurer & Payment Information', {
            'fields': ('treasurer_name', 'treasurer_phone', 'payment_instructions'),
            'description': 'Display payment instructions on the Join page'
        }),
        ('Join Success Page Customization', {
            'fields': ('success_message', 'success_button_text', 'success_button_url'),
            'description': 'Customize what users see after successful registration'
        }),
    )
    
    def has_add_permission(self, request):
        if SiteSettings.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return False


# ============================================
# NEW FINANCIAL MANAGEMENT ADMIN REGISTRATIONS
# ============================================

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('member', 'is_paid', 'payment_date', 'amount_paid', 'last_reminder_sent')
    list_filter = ('is_paid', 'payment_date')
    search_fields = ('member__first_name', 'member__last_name', 'member__email')
    list_editable = ('is_paid', 'amount_paid')
    date_hierarchy = 'payment_date'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('member', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('member__first_name', 'member__last_name', 'title', 'message')
    date_hierarchy = 'created_at'

@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'is_active')
    list_filter = ('category_type', 'is_active')
    search_fields = ('name', 'description')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'transaction_type', 'category', 'amount', 'description', 'recorded_by')
    list_filter = ('transaction_type', 'category', 'date')
    search_fields = ('description', 'reference_number')
    date_hierarchy = 'date'
    list_editable = ('amount',)

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('category', 'year', 'month', 'planned_amount', 'actual_amount', 'variance')
    list_filter = ('year', 'month', 'category')
    search_fields = ('category__name', 'notes')

@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'start_date', 'end_date', 'generated_by', 'created_at')
    list_filter = ('report_type', 'created_at')
    date_hierarchy = 'created_at'# core/admin.py
from django.contrib import admin
from django.contrib.auth.hashers import make_password
from .models import Member, Leadership, NewsPost, Announcement, FoundingMember, MembershipTier, Event, SiteSettings

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone_number', 'membership_type', 'is_active', 'has_password')
    list_filter = ('membership_type', 'is_active', 'date_joined')
    search_fields = ('first_name', 'last_name', 'email', 'registration_number', 'phone_number')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'profile_picture', 'bio')
        }),
        ('Contact & Account Details', {
            'fields': ('email', 'phone_number', 'registration_number', 'membership_type', 'is_active')
        }),
        ('Portal Access', {
            'fields': ('password',),
            'description': 'Set a password so this member can log into the Member Portal. Type the plain password here — it will be automatically encrypted when saved.'
        }),
    )

    @admin.display(description='Has Password', boolean=True)
    def has_password(self, obj):
        return bool(obj.password)

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data and obj.password:
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)

@admin.register(Leadership)
class LeadershipAdmin(admin.ModelAdmin):
    list_display = ('member', 'get_member_phone', 'role', 'term_start', 'is_current')
    list_filter = ('role', 'is_current')
    search_fields = ('member__first_name', 'member__last_name', 'member__phone_number')

    @admin.display(description='Phone Number', ordering='member__phone_number')
    def get_member_phone(self, obj):
        return obj.member.phone_number

@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'content')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'description')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'venue', 'is_upcoming')
    list_filter = ('is_upcoming', 'date')
    search_fields = ('title', 'description', 'venue')

@admin.register(FoundingMember)
class FoundingMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'role_in_commission')
    search_fields = ('name', 'role_in_commission')

@admin.register(MembershipTier)
class MembershipTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'entrance_fee', 'subscription_fee')
    search_fields = ('name',)

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'contact_email', 'contact_phone')
    fieldsets = (
        ('General Site Information', {
            'fields': ('site_name', 'logo', 'motto')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'contact_location')
        }),
        ('Social Media Links', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url'),
            'description': 'Enter full URLs (e.g., https://facebook.com/kuss)'
        }),
        ('WhatsApp & IT Support', {
            'fields': ('whatsapp_number', 'it_support_message'),
            'description': 'Configure IT support contact for member portal issues'
        }),
        ('Treasurer & Payment Information', {
            'fields': ('treasurer_name', 'treasurer_phone', 'payment_instructions'),
            'description': 'Display payment instructions on the Join page'
        }),
        ('Join Success Page Customization', {
            'fields': ('success_message', 'success_button_text', 'success_button_url'),
            'description': 'Customize what users see after successful registration'
        }),
    )
    
    def has_add_permission(self, request):
        if SiteSettings.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return False
