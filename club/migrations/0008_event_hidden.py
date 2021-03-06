# Generated by Django 2.2.6 on 2019-11-28 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0007_member'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='hidden',
            field=models.BooleanField(default=False, help_text='If true then the event will not be shown anywhere. Use this to create event drafts.'),
        ),
    ]
