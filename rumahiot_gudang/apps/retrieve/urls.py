# from django.contrib import admin
from django.conf.urls import url

from rumahiot_gudang.apps.retrieve.views import \
    retrieve_device_list, retrieve_device_data, \
    retrieve_supported_board_list, \
    retrieve_device_data_statistic, \
    retrieve_device_data_statistic_monthly, \
    retrieve_device_device_data_statistic_yearly, \
    retrieve_user_wifi_connection_list, \
    retrieve_master_sensor_reference_list, \
    retrieve_board_pin_options, \
    retrieve_device_data_count_chart, \
    retrieve_device_sensor_status_chart

urlpatterns = [
    url(r'^user/connection/wifi/list$', retrieve_user_wifi_connection_list, name='retrieve_user_wifi_connection_list'),
    url(r'^device/data$', retrieve_device_data, name='retrieve_device_data'),
    url(r'^device/list$', retrieve_device_list, name='retrieve_device_list'),
    url(r'^device/data/count/chart$', retrieve_device_data_count_chart, name='retrieve_device_data_count_chart'),
    url(r'^device/sensor/status/chart$', retrieve_device_sensor_status_chart, name='retrieve_device_sensor_status_chart'),
    url(r'^board/supported/list$', retrieve_supported_board_list, name='retrieve_supported_board_list'),
    url(r'^board/pin/options', retrieve_board_pin_options, name='retrieve_board_pin_options'),
    url(r'^sensor/master/reference/list$', retrieve_master_sensor_reference_list, name='retrieve_master_sensor_reference_list'),
    url(r'^device/data/statistic$', retrieve_device_data_statistic, name='retrieve_device_data_statistic'),
    url(r'^device/data/statistic/monthly$', retrieve_device_data_statistic_monthly, name='retrieve_device_data_statistic_monthly'),
    url(r'^device/data/statistic/yearly$', retrieve_device_device_data_statistic_yearly, name='retrieve_device_data_statistic_yearly'),

]
