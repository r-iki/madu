# Generated by Django 5.0.11 on 2025-02-13 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sensors', '0006_alter_spectralreading_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='spectralreading',
            name='timestamp',
            field=models.DateTimeField(),
        ),
    ]
