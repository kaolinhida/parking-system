from django import forms


class ReservationForm(forms.Form):
    car_number = forms.CharField(
        label='Номер автомобіля',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Наприклад: BK1234AB',
        })
    )