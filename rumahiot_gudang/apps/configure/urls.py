# from django.contrib import admin
from django.conf.urls import url

from rumahiot_gudang.apps.configure.views import update_user_sensor_detail

urlpatterns = [
    url(r'^device/sensor/detail/update$', update_user_sensor_detail, name='update_user_sensor_detail'),
]
