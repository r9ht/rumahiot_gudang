# from django.contrib import admin
from django.conf.urls import url

from rumahiot_gudang.apps.configure.views import \
    update_user_sensor_detail, \
    add_user_wifi_connection, \
    update_user_wifi_connection, \
    remove_user_wifi_connection

urlpatterns = [
    url(r'^device/sensor/detail/update$', update_user_sensor_detail, name='update_user_sensor_detail'),
    url(r'^user/connection/wifi/add$', add_user_wifi_connection, name='add_user_wifi_connection'),
    url(r'^user/connection/wifi/update$', update_user_wifi_connection, name='update_user_wifi_connection'),
    url(r'^user/connection/wifi/remove/(?P<user_wifi_connection_uuid>.+)$', remove_user_wifi_connection, name='remove_user_wifi_connection'),
]
