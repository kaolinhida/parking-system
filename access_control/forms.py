from django import forms

from parkings.models import ParkingLot

from .models import AccessLog


class AccessCodeForm(forms.Form):
    access_token = forms.UUIDField(
        label='Код доступу',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введіть або відскануйте код бронювання',
        })
    )


class AccessLogFilterForm(forms.Form):
    date_from = forms.DateField(
        label='Дата від',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    date_to = forms.DateField(
        label='Дата до',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    action = forms.ChoiceField(
        label='Дія',
        required=False,
        choices=[('', 'Усі дії'), *AccessLog.ACTION_CHOICES],
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    result = forms.ChoiceField(
        label='Результат',
        required=False,
        choices=[('', 'Усі результати'), *AccessLog.RESULT_CHOICES],
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    car_number = forms.CharField(
        label='Номер авто',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Наприклад: AA1234BB',
        })
    )
    parking_lot = forms.ModelChoiceField(
        label='Парковка',
        required=False,
        queryset=ParkingLot.objects.none(),
        empty_label='Усі парковки',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parking_lot'].queryset = ParkingLot.objects.all().order_by('name')
