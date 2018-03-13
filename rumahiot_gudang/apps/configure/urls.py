# from django.contrib import admin
from django.conf.urls import url
from rumahiot_gudang.apps.configure.views import update_device_sensor_threshold

urlpatterns = [
    url(r'^device/sensor/threshold/update$',update_device_sensor_threshold,name='update_device_sensor_threshold'),
]
