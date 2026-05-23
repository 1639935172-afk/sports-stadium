from django import forms

from .models import Field, Stadium, TimeSlot


class StadiumForm(forms.ModelForm):
    def clean_cover_image(self):
        image = self.cleaned_data.get('cover_image')
        if image is None:
            return image

        content_type = getattr(image, 'content_type', '')
        if content_type and not content_type.startswith('image/'):
            raise forms.ValidationError('请上传 jpg、jpeg、png 或 webp 格式的图片')
        return image

    class Meta:
        model = Stadium
        fields = ['name', 'address', 'phone_number', 'information', 'cover_image']
        labels = {
            'name': '场馆名称',
            'address': '场馆地址',
            'phone_number': '联系电话',
            'information': '场馆简介',
            'cover_image': '场馆照片',
        }
        widgets = {
            'cover_image': forms.ClearableFileInput(attrs={'accept': '.jpg,.jpeg,.png,.webp,image/*'}),
        }


class StadiumCoverForm(forms.ModelForm):
    def clean_cover_image(self):
        image = self.cleaned_data.get('cover_image')
        if image is None:
            raise forms.ValidationError('请选择一张图片后再保存')

        content_type = getattr(image, 'content_type', '')
        if content_type and not content_type.startswith('image/'):
            raise forms.ValidationError('请上传 jpg、jpeg、png 或 webp 格式的图片')
        return image

    class Meta:
        model = Stadium
        fields = ['cover_image']
        labels = {
            'cover_image': '场馆照片',
        }
        widgets = {
            'cover_image': forms.ClearableFileInput(attrs={'accept': '.jpg,.jpeg,.png,.webp,image/*'}),
        }


class TimeSlotForm(forms.ModelForm):
    def __init__(self, *args, field=None, **kwargs):
        super().__init__(*args, **kwargs)
        if field is not None:
            self.instance.field = field
        self.fields['is_available'].widget = forms.Select(
            choices=[
                (True, '可预约'),
                (False, '不可预约'),
            ]
        )

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'].widget = forms.Select(
            choices=[
                (True, '启用'),
                (False, '停用'),
            ]
        )

    class Meta:
        model = Field
        fields = ['field_type', 'number', 'is_active', 'price_per_hour']
        labels = {
            'field_type': '场地类型',
            'number': '场地编号',
            'is_active': '启用状态',
            'price_per_hour': '预约单价/小时',
        }
