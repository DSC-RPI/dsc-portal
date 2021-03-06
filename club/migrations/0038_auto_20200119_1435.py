# Generated by Django 3.0.2 on 2020-01-19 19:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0037_eventfeedback_tag'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tag',
            options={'ordering': ['tag_type', 'title']},
        ),
        migrations.AlterModelManagers(
            name='tag',
            managers=[
            ],
        ),
        migrations.RemoveField(
            model_name='tag',
            name='members',
        ),
        migrations.AddField(
            model_name='member',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='members', to='club.Tag'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='tag_type',
            field=models.CharField(choices=[('D', 'Dietary Restriction'), ('S', 'Skill')], help_text='The type of tag.', max_length=5),
        ),
        migrations.AlterField(
            model_name='tag',
            name='title',
            field=models.CharField(help_text='The title of the tag.', max_length=50),
        ),
    ]
