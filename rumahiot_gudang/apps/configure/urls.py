# from django.contrib import admin
from django.conf.urls import url

from rumahiot_gudang.apps.configure.views import \
    update_user_sensor_detail, \
    remove_user_device, \
    update_device_detail

urlpatterns = [
    url(r'^device/sensor/detail/update$', update_user_sensor_detail, name='update_user_sensor_detail'),
    url(r'^device/remove/(?P<device_uuid>.+)$', remove_user_device, name='remove_user_device'),
    url(r'^device/update', update_device_detail, name='update_device_detail'),
]
