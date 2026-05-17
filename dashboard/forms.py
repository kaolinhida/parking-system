from django import forms

from parkings.models import ParkingSpaceType


class ParkingGridForm(forms.Form):
    name = forms.CharField(
        label='Назва парковки',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Наприклад: Parking №3',
        })
    )

    address = forms.CharField(
        label='Адреса',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Наприклад: вул. Центральна, 10',
        })
    )

    description = forms.CharField(
        label='Опис',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Короткий опис парковки',
        })
    )

    latitude = forms.DecimalField(
        label='Широта',
        required=False,
        max_digits=9,
        decimal_places=6,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.000001',
            'placeholder': 'Наприклад: 50.747232',
        })
    )

    longitude = forms.DecimalField(
        label='Довгота',
        required=False,
        max_digits=9,
        decimal_places=6,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.000001',
            'placeholder': 'Наприклад: 25.325383',
        })
    )

    rows = forms.IntegerField(
        label='Кількість рядів',
        min_value=1,
        max_value=26,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Наприклад: 3',
        })
    )

    columns = forms.IntegerField(
        label='Кількість колонок',
        min_value=1,
        max_value=30,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Наприклад: 4',
        })
    )

    default_space_type = forms.ModelChoiceField(
        label='Тип місць за замовчуванням',
        queryset=ParkingSpaceType.objects.filter(is_active=True),
        empty_label='Оберіть тип місця',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    price_per_hour = forms.DecimalField(
        label='Тариф за годину',
        min_value=0,
        max_digits=8,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Наприклад: 30.00',
        })
    )