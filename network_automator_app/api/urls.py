from django.urls import path, include
from network_automator_app.api.views import index, device_detail

urlpatterns = [
    path('hosts/', index, name='index'),
    path('hosts/<int:pk>', device_detail, name='device_detail'),
]
