# Generated by Django 3.2.8 on 2021-10-31 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0004_auto_20211031_1651'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='chat',
            options={'ordering': ['date']},
        ),
        migrations.AlterField(
            model_name='chat',
            name='message',
            field=models.TextField(),
        ),
    ]
