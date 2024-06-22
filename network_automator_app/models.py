from django.db import models

class Host(models.Model):
    hostname = models.CharField(max_length=32)
    description = models.CharField(max_length=200)
    vendor = models.CharField(max_length=32, blank=True, null=True)
    model = models.CharField(max_length=32, blank=True, null=True)
    ipv4_address = models.GenericIPAddressField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    street_address = models.CharField(max_length=200, blank=True, null=True)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.hostname