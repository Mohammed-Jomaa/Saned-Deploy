# Generated by Django 2.2.4 on 2025-07-16 08:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('saned_app', '0005_notifications'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='region',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.DeleteModel(
            name='Notifications',
        ),
    ]
