from django import forms
from accounts.models.Users import Users

class AccountForm(forms.ModelForm):
    class Meta:
        model = Users
        fields = ('first_name', 'last_name', 'email', 'phone', 'gender', 'birth_date')