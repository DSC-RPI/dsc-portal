# Generated by Django 3.0.1 on 2019-12-26 22:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0021_auto_20191226_1715'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='presentation_id',
        ),
        migrations.AddField(
            model_name='event',
            name='slideshow_id',
            field=models.CharField(blank=True, help_text='(optional) The ID of the Google Slides slideshow.', max_length=300, null=True),
        ),
    ]