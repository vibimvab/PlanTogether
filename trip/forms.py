from django import forms
from .models import Place, TravelGroup

class GroupForm(forms.ModelForm):
    class Meta:
        model = TravelGroup
        fields = ['name', 'description']

class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = ['name', 'description', 'place_type', 'address', 'lat', 'lng', 'url']
        widgets = {'url': forms.URLInput(attrs={'placeholder': 'https://...'})}
