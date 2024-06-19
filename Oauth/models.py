from django.db import models

# Create your models here.
class Activities(models.Model):
    athlete_id = models.CharField(max_length=200)
    activity_id = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    distance = models.FloatField()
    total_elevation_gain = models.FloatField()
    type = models.CharField(max_length=200)
    location_city = models.CharField(max_length=200, null=True)
    location_state = models.CharField(max_length=200, null=True)
    location_country = models.CharField(max_length=200, null=True)
    mapid = models.CharField(max_length=200)
    mappolyline = models.TextField(max_length=3000)
    mapresource_state = models.IntegerField()
    upload_id = models.CharField(max_length=200, null=True)
    
    class Meta:
        unique_together = ('athlete_id', 'activity_id')