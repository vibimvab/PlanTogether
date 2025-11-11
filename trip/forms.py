from django import forms
from .models import Place, TravelGroup
from django.db import transaction
from .models import TravelGroupPlace, Place


class GroupForm(forms.ModelForm):
    class Meta:
        model = TravelGroup
        fields = ['name', 'description']


class PlaceNameQueryForm(forms.Form):
    place_name = forms.CharField(label="장소 이름", max_length=200)


class PlaceAddressQueryForm(forms.Form):
    address = forms.CharField(label="주소", max_length=255)


class PlaceSearchResultForm(forms.Form):
    # existing place 선택 or "new" 선택
    choice = forms.ChoiceField(label="결과 선택", choices=[])  # 뷰에서 동적으로 채움
    # 새로 만들 때 필요한 데이터는 hidden으로 전달
    new_name = forms.CharField(required=False, widget=forms.HiddenInput)
    new_address = forms.CharField(required=False, widget=forms.HiddenInput)
    new_lat = forms.DecimalField(required=False, max_digits=9, decimal_places=6, widget=forms.HiddenInput)
    new_lng = forms.DecimalField(required=False, max_digits=9, decimal_places=6, widget=forms.HiddenInput)


class TravelGroupPlaceForm(forms.ModelForm):
    # 검색 단계에서 결정된 선택 결과를 받아옴
    place_id = forms.IntegerField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = TravelGroupPlace
        fields = ["place_type", "nickname", "description"]