# Generated by Django 5.1.6 on 2025-03-08 18:32

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('genrate_bill', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bill',
            options={'ordering': ['-date']},
        ),
        migrations.AlterField(
            model_name='bill',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
