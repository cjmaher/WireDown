from datetime import date
from django import forms


class EventForm(forms.Form):
    start_date = forms.DateField(label='Start Date', widget=forms.DateInput(attrs={'type': 'date'}),
                                 initial=date.today())
    end_date = forms.DateField(label='End Date', widget=forms.DateInput(attrs={'type': 'date'}))

