# Generated by Django 4.1.3 on 2023-04-01 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bb_finance_api', '0007_bbfinancestory_disable_ads_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bbfinancestory',
            name='created_at',
            field=models.IntegerField(default=1680353798.554514),
        ),
    ]
