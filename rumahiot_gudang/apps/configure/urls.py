# from django.contrib import admin
from django.conf.urls import url

from rumahiot_gudang.apps.configure.views import \
    update_user_sensor_detail, \
    remove_user_device, \
    update_device_detail, \
    remove_supported_board, \
    update_supported_board, \
    remove_supported_sensor, \
    update_supported_sensor

urlpatterns = [
    url(r'^device/sensor/detail/update$', update_user_sensor_detail, name='update_user_sensor_detail'),
    url(r'^device/remove/(?P<device_uuid>.+)$', remove_user_device, name='remove_user_device'),
    url(r'^device/update$', update_device_detail, name='update_device_detail'),
    url(r'^board/supported/remove/(?P<board_uuid>.+)$', remove_supported_board, name='remove_supported_board'),
    url(r'^sensor/supported/remove/(?P<master_sensor_reference_uuid>.+)$', remove_supported_sensor, name='remove_supported_sensor'),
    url(r'^board/supported/update$', update_supported_board, name='update_supported_board'),
    url(r'^sensor/supported/update$', update_supported_sensor, name='update_supported_sensor')
]
