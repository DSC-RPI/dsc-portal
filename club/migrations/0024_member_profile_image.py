# Generated by Django 3.0.1 on 2019-12-30 05:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0023_auto_20191226_1807'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='profile_image',
            field=models.ImageField(blank=True, null=True, upload_to='profile-images'),
        ),
    ]
