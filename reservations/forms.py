from datetime import datetime

from django import forms
from django.utils import timezone

from vehicles.models import Vehicle


class ReservationForm(forms.Form):
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

    vehicle = forms.ModelChoiceField(
        label='Автомобіль',
        queryset=Vehicle.objects.none(),
        empty_label='Оберіть автомобіль',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(
                user=user,
                is_active=True
            ).order_by('brand', 'model', 'license_plate')

    def clean(self):
        cleaned_data = super().clean()

        selected_date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if selected_date and start_time and end_time:
            start_datetime = timezone.make_aware(
                datetime.combine(selected_date, start_time)
            )
            end_datetime = timezone.make_aware(
                datetime.combine(selected_date, end_time)
            )

            if end_datetime <= start_datetime:
                raise forms.ValidationError(
                    'Час завершення має бути пізніше часу початку.'
                )

            if start_datetime < timezone.now():
                raise forms.ValidationError(
                    'Не можна створити бронювання на минулий час.'
                )

            cleaned_data['start_datetime'] = start_datetime
            cleaned_data['end_datetime'] = end_datetime

        return cleaned_data