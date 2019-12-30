from django import forms
from .models import Member

from .models import Member

class MemberAccountForm(forms.Form):
    first_name = forms.CharField(label='First Name', max_length=200)
    last_name = forms.CharField(label='Last Name', max_length=200)
    grade = forms.ChoiceField(label='Grade', widget=forms.RadioSelect, choices=Member.GRADE_TYPES)
    profile_image = forms.ImageField(required=False)