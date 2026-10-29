from django import forms
from django.utils import timezone

from .models import FoodPost, MealMateUser


class SignupForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'Full name'}),
    )
    email = forms.EmailField(
        max_length=255,
        widget=forms.EmailInput(attrs={'class': 'auth-input', 'placeholder': 'Email address'}),
    )
    phone = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'Phone number (optional)'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'auth-input', 'placeholder': 'Password'}),
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'auth-input', 'placeholder': 'Confirm password'}),
    )

    def clean_full_name(self):
        value = self.cleaned_data['full_name'].strip()
        if len(value) < 2:
            raise forms.ValidationError('Please enter a valid name.')
        return value

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if MealMateUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if password and len(password) < 8:
            self.add_error('password', 'Password must contain at least 8 characters.')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned


class LoginForm(forms.Form):
    email = forms.EmailField(
        max_length=255,
        widget=forms.EmailInput(attrs={'class': 'auth-input', 'placeholder': 'Email address'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'auth-input', 'placeholder': 'Password'}),
    )

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()


class FoodPostForm(forms.ModelForm):
    class Meta:
        model = FoodPost
        fields = [
            'food_name', 'description', 'quantity', 'pickup_address',
            'pickup_start', 'pickup_end',
        ]
        widgets = {
            'food_name': forms.TextInput(attrs={'class': 'business-input', 'placeholder': 'Example: Chicken Pasta'}),
            'description': forms.Textarea(attrs={'class': 'business-input', 'placeholder': 'Describe the food...', 'rows': 4}),
            'quantity': forms.NumberInput(attrs={'class': 'business-input', 'min': 1}),
            'pickup_address': forms.TextInput(attrs={'class': 'business-input', 'placeholder': 'Full pickup address or postcode'}),
            'pickup_start': forms.DateTimeInput(attrs={'class': 'business-input', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'pickup_end': forms.DateTimeInput(attrs={'class': 'business-input', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pickup_start'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['pickup_end'].input_formats = ['%Y-%m-%dT%H:%M']

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity < 1:
            raise forms.ValidationError('Quantity must be at least 1.')
        return quantity

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('pickup_start')
        end = cleaned.get('pickup_end')
        now = timezone.now()
        if start and start < now:
            self.add_error('pickup_start', 'Pickup start must be in the future.')
        if start and end and end <= start:
            self.add_error('pickup_end', 'Pickup end must be after pickup start.')
        return cleaned


class ProfileForm(forms.Form):
    full_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'account-input'}))
    phone = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'account-input'}))

    def clean_full_name(self):
        value = self.cleaned_data['full_name'].strip()
        if len(value) < 2:
            raise forms.ValidationError('Please enter a valid name.')
        return value


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'account-input'}))
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'account-input'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'account-input'}))

    def clean(self):
        cleaned = super().clean()
        new_password = cleaned.get('new_password')
        confirm = cleaned.get('confirm_password')
        if new_password and len(new_password) < 8:
            self.add_error('new_password', 'Password must contain at least 8 characters.')
        if new_password and confirm and new_password != confirm:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned
