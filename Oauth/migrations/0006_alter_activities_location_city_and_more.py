# Generated by Django 4.2.2 on 2023-10-02 00:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Oauth', '0005_alter_activities_activity_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activities',
            name='location_city',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='activities',
            name='location_country',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='activities',
            name='location_state',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
