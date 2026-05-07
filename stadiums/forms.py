from django import forms

from .models import Field, Stadium, TimeSlot


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


class TimeSlotForm(forms.ModelForm):
    def __init__(self, *args, field=None, **kwargs):
        super().__init__(*args, **kwargs)
        if field is not None:
            self.instance.field = field

    class Meta:
        model = TimeSlot
        fields = ['date', 'start_time', 'end_time', 'is_available']
        labels = {
            'date': '开放日期',
            'start_time': '开始时间',
            'end_time': '结束时间',
            'is_available': '可约状态',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class FieldForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = ['field_type', 'number', 'is_active', 'price_per_hour']
        labels = {
            'field_type': '场地类型',
            'number': '场地编号',
            'is_active': '启用状态',
            'price_per_hour': '预约单价/小时',
        }
