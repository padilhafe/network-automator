from rest_framework.response import Response
from rest_framework.decorators import api_view
from network_automator_app.models import Host
from network_automator_app.api.serializers import DeviceSerializer

@api_view(['GET', 'POST'])
def index(request):
    if request.method == 'GET':
        hosts = Host.objects.all()
        serializer = DeviceSerializer(hosts, many=True)
        return Response(serializer.data)
    
    if request.method == 'POST':
        serializer = DeviceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

@api_view(['GET', 'PUT', 'DELETE'])
def device_detail(request, pk):
    if request.method == 'GET':
        try:
            host = Host.objects.get(pk=pk)
        except Host.DoesNotExist:
            return Response({'Error': 'Host not found'}, status=404)
        serializer = DeviceSerializer(host)
        return Response(serializer.data)
    
    if request.method == 'PUT':
        host = Host.objects.get(pk=pk)
        serializer = DeviceSerializer(host, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    if request.method == 'DELETE':
        host = Host.objects.get(pk=pk)
        host.delete()
        return Response(status=204)
    