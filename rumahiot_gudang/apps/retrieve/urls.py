# from django.contrib import admin
from django.conf.urls import url

from rumahiot_gudang.apps.retrieve.views import \
    retrieve_device_list, retrieve_device_data, \
    retrieve_supported_board_list, \
    retrieve_device_data_statistic, \
    retrieve_device_data_statistic_monthly, \
    retrieve_device_device_data_statistic_yearly, \
    retrieve_master_sensor_reference_list, \
    retrieve_board_pin_options, \
    retrieve_device_data_count_chart, \
    retrieve_device_sensor_status_chart, \
    retrieve_simple_device_list, \
    retrieve_timezone_list, \
    retrieve_device_arduino_code, \
    retrieve_user_sensor_mapping, \
    retrieve_device_detail

urlpatterns = [
    url(r'^timezone/list$', retrieve_timezone_list, name='retrieve_timezone_list'),
    url(r'^device/data$', retrieve_device_data, name='retrieve_device_data'),
    url(r'^device/detail/(?P<device_uuid>.+)$', retrieve_device_detail, name='retrieve_device_detail'),
    url(r'^device/list$', retrieve_device_list, name='retrieve_device_list'),
    url(r'^device/list/simple$', retrieve_simple_device_list, name='retrieve_simple_device_list'),
    url(r'^device/arduino/code/(?P<device_uuid>.+)$', retrieve_device_arduino_code, name='retrieve_device_arduino_code'),
    url(r'^device/data/count/chart$', retrieve_device_data_count_chart, name='retrieve_device_data_count_chart'),
    url(r'^device/sensor/status/chart$', retrieve_device_sensor_status_chart, name='retrieve_device_sensor_status_chart'),
    url(r'^board/supported/list$', retrieve_supported_board_list, name='retrieve_supported_board_list'),
    url(r'^board/pin/options', retrieve_board_pin_options, name='retrieve_board_pin_options'),
    url(r'^sensor/master/reference/list$', retrieve_master_sensor_reference_list, name='retrieve_master_sensor_reference_list'),
    url(r'^sensor/mapping/(?P<device_uuid>.+)$', retrieve_user_sensor_mapping, name='retrieve_user_sensor_mapping'),
    url(r'^device/data/statistic$', retrieve_device_data_statistic, name='retrieve_device_data_statistic'),
    url(r'^device/data/statistic/monthly$', retrieve_device_data_statistic_monthly, name='retrieve_device_data_statistic_monthly'),
    url(r'^device/data/statistic/yearly$', retrieve_device_device_data_statistic_yearly, name='retrieve_device_data_statistic_yearly'),

]
