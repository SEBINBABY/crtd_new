# Generated by Django 5.1.4 on 2024-12-16 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_dashboard', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='has_paid',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]