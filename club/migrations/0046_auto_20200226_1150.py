# Generated by Django 3.0.2 on 2020-02-26 16:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0045_auto_20200226_1131'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='advertised_on_social_media',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event',
            name='posted_review_to_social_media',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event',
            name='recorded_session',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event',
            name='registered_with_google',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event',
            name='reported_to_google',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event',
            name='sent_club_email',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event',
            name='took_photos',
            field=models.BooleanField(default=False),
        ),
    ]
