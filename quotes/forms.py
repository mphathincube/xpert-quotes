from django import forms
from .models import Client, Quote, Car


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone']


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['client', 'car', 'service', 'price']
        widgets = {
            'service': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically filter cars based on the selected client
        if 'client' in self.data:
            try:
                client_id = int(self.data.get('client'))
                self.fields['car'].queryset = Car.objects.filter(
                    client_id=client_id)
            except (ValueError, TypeError):
                self.fields['car'].queryset = Car.objects.none()
        elif self.instance.pk and self.instance.client:
            self.fields['car'].queryset = Car.objects.filter(
                client=self.instance.client)
        else:
            self.fields['car'].queryset = Car.objects.none()


class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['car_reg']
