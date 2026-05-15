from django import forms

from .models import Vehicle


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = (
            'brand',
            'model',
            'license_plate',
            'year',
            'vehicle_type',
            'color',
            'photo',
        )
        labels = {
            'brand': 'Марка автомобіля',
            'model': 'Модель',
            'license_plate': 'Номерний знак',
            'year': 'Рік випуску',
            'vehicle_type': 'Тип транспорту',
            'color': 'Колір',
            'photo': 'Фото автомобіля',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if field_name in ['vehicle_type', 'color']:
                field.widget.attrs.update({'class': 'form-select'})
            elif field_name == 'photo':
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

        self.fields['brand'].widget.attrs.update({'placeholder': 'Наприклад: Toyota'})
        self.fields['model'].widget.attrs.update({'placeholder': 'Наприклад: Corolla'})
        self.fields['license_plate'].widget.attrs.update({'placeholder': 'Наприклад: BK1234AB'})
        self.fields['year'].widget.attrs.update({'placeholder': 'Наприклад: 2018'})

    def clean_license_plate(self):
        license_plate = self.cleaned_data['license_plate']
        return license_plate.upper().replace(' ', '')