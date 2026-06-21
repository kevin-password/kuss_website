# core/forms.py
from django import forms
from .models import Member

class MemberJoinForm(forms.ModelForm):
    agree_to_constitution = forms.BooleanField(
        label="I agree to abide by the KUSS Constitution, uphold its objectives, and pay the required membership/subscription fees.",
        required=True,
        error_messages={'required': 'You must agree to the constitution and fees to join KUSS.'}
    )

    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'registration_number', 
            'email', 'phone_number', 'membership_type', 
            'bio', 'profile_picture'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us a bit about yourself and your interest in surgery...'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'John'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Doe'}),
            'registration_number': forms.TextInput(attrs={'placeholder': 'e.g., 23-0000-00'}),
            'email': forms.EmailInput(attrs={'placeholder': 'john.doe@student.ku.ac.ug'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '+256 7XX XXX XXX'}),
        }

class MemberLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'john.doe@student.ku.ac.ug'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'})
    )

class MemberProfileForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'phone_number', 'bio', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'first_name': forms.TextInput(),
            'last_name': forms.TextInput(),
            'phone_number': forms.TextInput(),
        }