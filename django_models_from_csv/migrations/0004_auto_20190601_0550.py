# Generated by Django 2.2 on 2019-06-01 05:50

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_models_from_csv', '0003_auto_20190524_0335'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dynamicmodel',
            name='name',
            field=models.CharField(max_length=255, validators=[django.core.validators.MinLengthValidator(1)]),
        ),
    ]
