from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('stadiums', '0003_timeslot'),
    ]

    operations = [
        migrations.AddField(
            model_name='stadium',
            name='cover_image',
            field=models.FileField(
                blank=True,
                upload_to='stadium_covers/',
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])],
                verbose_name='场馆照片',
            ),
        ),
    ]
