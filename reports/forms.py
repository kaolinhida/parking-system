from django import forms

from parkings.models import ParkingLot
from reservations.models import Reservation


class ReportFilterForm(forms.Form):
    date_from = forms.DateField(
        label='Дата від',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )

    date_to = forms.DateField(
        label='Дата до',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )

    parking_lot = forms.ModelChoiceField(
        label='Парковка',
        queryset=ParkingLot.objects.filter(is_active=True),
        required=False,
        empty_label='Усі парковки',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    status = forms.ChoiceField(
        label='Статус',
        required=False,
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['status'].choices = [
            ('', 'Усі статуси'),
            *Reservation.STATUS_CHOICES,
        ]

    def clean(self):
        cleaned_data = super().clean()

        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_to < date_from:
            raise forms.ValidationError('Дата завершення не може бути раніше дати початку.')

        return cleaned_data