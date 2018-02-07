# from django.contrib import admin
from django.conf.urls import url
from rumahiot_gudang.apps.store.views import store_device_data

urlpatterns = [
    url(r'^device/data$',store_device_data,name='store_device_data')
]
