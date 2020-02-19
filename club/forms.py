from django.conf import settings
from django import forms

from .models import Member, Tag, EventFeedback

class MemberAccountForm(forms.Form):
    first_name = forms.CharField(label='First Name', max_length=200)
    last_name = forms.CharField(label='Last Name', max_length=200)
    school_username = forms.CharField(label=f'{settings.SCHOOL_NAME_SHORT} Username', max_length=100)
    grade = forms.ChoiceField(label='Grade', widget=forms.RadioSelect, choices=Member.GRADE_TYPES)
    bio = forms.CharField(widget=forms.Textarea, max_length=2000, label='Bio', required=False)
    skills = forms.ModelMultipleChoiceField(queryset=Tag.skills.all(), widget=forms.CheckboxSelectMultiple, label='I have experience in', required=False)
    dietary_restrictions = forms.ModelMultipleChoiceField(queryset=Tag.dietary_restrictions.all(), widget=forms.CheckboxSelectMultiple, label='My dietary preferences/restrictions are', required=False)
    profile_image = forms.ImageField(required=False)

class EventFeedbackForm(forms.ModelForm):

    class Meta:
        model = EventFeedback
        exclude = ['event', 'user', 'created_at', 'updated_at']