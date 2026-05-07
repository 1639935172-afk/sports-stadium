from django import forms

from .models import Stadium


class StadiumForm(forms.ModelForm):
    class Meta:
        model = Stadium
        fields = ['name', 'address', 'phone_number', 'information']
        labels = {
            'name': '场馆名称',
            'address': '场馆地址',
            'phone_number': '联系电话',
            'information': '场馆简介',
        }
