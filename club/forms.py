from django.forms import ModelForm, TextInput, EmailInput

from django.contrib.auth.models import User

class UserAccountForm(ModelForm):
    class Meta:
        model = User

        fields = ('first_name', 'last_name', 'email')

        widgets = {
            'first_name': TextInput(attrs={'class': 'input'}),
            'last_name': TextInput(attrs={'class': 'input'}),
            'email': EmailInput(attrs={'class': 'input'}),
        }