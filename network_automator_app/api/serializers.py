from rest_framework import serializers
from network_automator_app.models import Host

class DeviceSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    hostname = serializers.CharField()
    description = serializers.CharField()
    vendor = serializers.CharField()
    model = serializers.CharField()
    ipv4_address = serializers.IPAddressField()
    location = serializers.CharField()
    street_address = serializers.CharField()
    active = serializers.BooleanField()
    
    def create(self, validated_data):
        return Host.objects.create(**validated_data)
        
    def update(self, instance, validated_data):
        instance.hostname = validated_data.get('hostname', instance.hostname)
        instance.description = validated_data.get('description', instance.description)
        instance.vendor = validated_data.get('vendor', instance.vendor)
        instance.model = validated_data.get('model', instance.model)
        instance.ipv4_address = validated_data.get('ipv4_address', instance.ipv4_address)
        instance.location = validated_data.get('location', instance.location)
        instance.street_address = validated_data.get('street_address', instance.street_address)
        instance.active = validated_data.get('active', instance.active)
        instance.save()
        return instance