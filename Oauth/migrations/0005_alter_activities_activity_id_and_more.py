# Generated by Django 4.2.2 on 2023-10-01 23:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Oauth', '0004_alter_activities_athlete_id_alter_activities_mapid_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activities',
            name='activity_id',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='activities',
            name='athlete_id',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='activities',
            name='mapid',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='activities',
            name='upload_id',
            field=models.CharField(max_length=200),
        ),
    ]
