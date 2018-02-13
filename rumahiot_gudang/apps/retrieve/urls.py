# from django.contrib import admin
from django.conf.urls import url
from rumahiot_gudang.apps.retrieve.views import retrieve_device_list,retrieve_device_data,retrieve_sensor_data
urlpatterns = [
    url(r'^device/data$',retrieve_device_data,name='retrieve_device_data'),
    url(r'^device/list$',retrieve_device_list,name='retrieve_device_list'),
    url(r'^sensor/data$',retrieve_sensor_data,name='retrieve_sensor_data'),
]
