# Generated by Django 5.0.11 on 2025-03-15 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sensors', '0010_alter_spectralreading_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='spectralreading',
            name='temperature',
            field=models.FloatField(default=0.0),
        ),
    ]
