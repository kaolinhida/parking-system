from django import forms

from .models import ParkingSpaceType


class ParkingAvailabilityForm(forms.Form):
    date = forms.DateField(
        label='Дата',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )

    start_time = forms.TimeField(
        label='Час початку',
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control',
        })
    )

    end_time = forms.TimeField(
        label='Час завершення',
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control',
        })
    )

    space_type = forms.ModelChoiceField(
        label='Тип паркомісця',
        queryset=ParkingSpaceType.objects.filter(is_active=True),
        required=False,
        empty_label='Усі типи',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError(
                'Час завершення має бути пізніше часу початку.'
            )

        return cleaned_data