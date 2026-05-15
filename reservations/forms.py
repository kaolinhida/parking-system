from django import forms

from vehicles.models import Vehicle


class ReservationForm(forms.Form):
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
            ).order_by('brand', 'model')