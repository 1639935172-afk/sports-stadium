from django import forms
from django.utils import timezone

from .models import Field, Stadium, TimeSlot


FIELD_TYPE_OTHER = '__other__'
FIELD_TYPE_CHOICES = [
    ('足球', '足球'),
    ('篮球', '篮球'),
    ('羽毛球', '羽毛球'),
    ('乒乓球', '乒乓球'),
    ('网球', '网球'),
    ('排球', '排球'),
    ('游泳', '游泳'),
    ('健身', '健身'),
    (FIELD_TYPE_OTHER, '其他类型'),
]


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


class BulkTimeSlotGenerationForm(forms.Form):
    field_scope = forms.ChoiceField(
        label='选择场地',
        choices=[
            ('current', '当前场地'),
            ('all', '全部启用场地'),
        ],
        initial='current',
    )
    start_date = forms.DateField(label='开始日期', widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(label='结束日期', widget=forms.DateInput(attrs={'type': 'date'}))
    start_time = forms.TimeField(label='每日开始时间', widget=forms.TimeInput(attrs={'type': 'time'}))
    end_time = forms.TimeField(label='每日结束时间', widget=forms.TimeInput(attrs={'type': 'time'}))
    slot_minutes = forms.IntegerField(label='单个时段长度（分钟）', min_value=15, max_value=240, initial=60)
    price_per_hour = forms.DecimalField(label='每小时价格', max_digits=8, decimal_places=2, min_value=0)
    is_available = forms.BooleanField(label='生成后可预约', required=False, initial=True)
    skip_existing = forms.BooleanField(label='跳过已有时段', required=False, initial=True)
    use_weekend_rule = forms.BooleanField(label='周末使用不同开放时间', required=False, initial=False)
    weekend_start_time = forms.TimeField(
        label='周末开始时间',
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time'}),
    )
    weekend_end_time = forms.TimeField(
        label='周末结束时间',
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate().isoformat()
        self.fields['start_date'].widget.attrs['min'] = today
        self.fields['end_date'].widget.attrs['min'] = today

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        use_weekend_rule = cleaned_data.get('use_weekend_rule')
        weekend_start_time = cleaned_data.get('weekend_start_time')
        weekend_end_time = cleaned_data.get('weekend_end_time')
        today = timezone.localdate()

        if start_date and start_date < today:
            self.add_error('start_date', '开始日期不能早于今天')
        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', '结束日期不能早于开始日期')
        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', '每日结束时间必须晚于开始时间')
        if use_weekend_rule:
            if not weekend_start_time:
                self.add_error('weekend_start_time', '启用周末规则时请填写周末开始时间')
            if not weekend_end_time:
                self.add_error('weekend_end_time', '启用周末规则时请填写周末结束时间')
            if weekend_start_time and weekend_end_time and weekend_start_time >= weekend_end_time:
                self.add_error('weekend_end_time', '周末结束时间必须晚于开始时间')
        return cleaned_data


class FieldForm(forms.ModelForm):
    custom_field_type = forms.CharField(
        label='其他场地类型',
        required=False,
        max_length=50,
        help_text='选择“其他类型”时填写',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        known_field_types = {value for value, _label in FIELD_TYPE_CHOICES if value != FIELD_TYPE_OTHER}
        current_field_type = self.instance.field_type if self.instance and self.instance.pk else ''
        if current_field_type and current_field_type not in known_field_types:
            self.initial['field_type'] = FIELD_TYPE_OTHER
            self.initial['custom_field_type'] = current_field_type
        self.fields['field_type'].widget = forms.Select(choices=FIELD_TYPE_CHOICES)
        self.order_fields([
            'field_type',
            'custom_field_type',
            'number',
            'is_active',
            'price_per_hour',
        ])
        self.fields['is_active'].widget = forms.Select(
            choices=[
                (True, '启用'),
                (False, '停用'),
            ]
        )

    def clean(self):
        cleaned_data = super().clean()
        field_type = (cleaned_data.get('field_type') or '').strip()
        custom_field_type = (cleaned_data.get('custom_field_type') or '').strip()

        if field_type == FIELD_TYPE_OTHER:
            if not custom_field_type:
                self.add_error('custom_field_type', '选择其他类型时，请填写场地类型')
            else:
                cleaned_data['field_type'] = custom_field_type
        elif not field_type:
            self.add_error('field_type', '请选择场地类型')

        return cleaned_data

    class Meta:
        model = Field
        fields = ['field_type', 'number', 'is_active', 'price_per_hour']
        labels = {
            'field_type': '场地类型',
            'number': '场地名称',
            'is_active': '启用状态',
            'price_per_hour': '预约单价/小时',
        }
