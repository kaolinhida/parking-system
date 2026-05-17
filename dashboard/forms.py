from django import forms

from parkings.models import ParkingLot, ParkingSpace, ParkingSpaceType, Tariff


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


class ParkingSpaceEditForm(forms.ModelForm):
    class Meta:
        model = ParkingSpace
        fields = (
            'number',
            'row',
            'column',
            'space_type',
            'is_active',
        )
        labels = {
            'number': 'Номер місця',
            'row': 'Ряд',
            'column': 'Колонка',
            'space_type': 'Тип місця',
            'is_active': 'Активне місце',
        }
        widgets = {
            'number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Наприклад: A1',
            }),
            'row': forms.NumberInput(attrs={
                'class': 'form-control',
            }),
            'column': forms.NumberInput(attrs={
                'class': 'form-control',
            }),
            'space_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['space_type'].queryset = ParkingSpaceType.objects.filter(
            is_active=True
        ).order_by('name')


class TariffForm(forms.ModelForm):
    class Meta:
        model = Tariff
        fields = (
            'parking_lot',
            'space_type',
            'price_per_hour',
            'is_active',
        )
        labels = {
            'parking_lot': 'Парковка',
            'space_type': 'Тип паркомісця',
            'price_per_hour': 'Ціна за годину',
            'is_active': 'Активний тариф',
        }
        widgets = {
            'parking_lot': forms.Select(attrs={
                'class': 'form-select',
            }),
            'space_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'price_per_hour': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Наприклад: 30.00',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['parking_lot'].queryset = ParkingLot.objects.all().order_by('name')
        self.fields['space_type'].queryset = ParkingSpaceType.objects.all().order_by('name')

    def clean_price_per_hour(self):
        price_per_hour = self.cleaned_data['price_per_hour']

        if price_per_hour < 0:
            raise forms.ValidationError('Ціна за годину не може бути від’ємною.')

        return price_per_hour
