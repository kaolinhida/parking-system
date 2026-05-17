from django import forms


class AccessCodeForm(forms.Form):
    access_token = forms.UUIDField(
        label='Код доступу',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введіть або відскануйте код бронювання',
        })
    )