# Generated by Django 3.2 on 2021-04-28 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0002_log'),
    ]

    operations = [
        migrations.AddField(
            model_name='useractionlog',
            name='text',
            field=models.TextField(blank=True, null=True),
        ),
    ]