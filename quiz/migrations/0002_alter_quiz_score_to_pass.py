# Generated by Django 5.1.4 on 2025-01-05 16:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quiz',
            name='score_to_pass',
            field=models.IntegerField(blank=True, help_text='Minimum score(%) to pass', null=True),
        ),
    ]
