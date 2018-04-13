import requests
from rumahiot_gudang.settings import RUMAHIOT_SURAT_API_KEY, RUMAHIOT_SURAT_DEVICE_NOTIFICATION_LOGGER_ENDPOINT

class GudangSuratLoggerModule:

    # Surat service for logging device notification (to be displayed in the panel)
    def log_device_notification(self, user_uuid, user_sensor_uuid,  device_uuid, device_name, user_sensor_name,
                                       threshold_value, latest_value, time_reached,
                                       threshold_direction, unit_symbol,
                                       notification_type, sent, viewed):
        header = {
            'Authorization': 'Bearer {}'.format(RUMAHIOT_SURAT_API_KEY)
        }

        payload = {
            'user_uuid': user_uuid,
            'user_sensor_uuid': user_sensor_uuid ,
            'device_uuid': device_uuid,
            'device_name': device_name,
            'user_sensor_name': user_sensor_name,
            'threshold_value': threshold_value,
            'latest_value': latest_value,
            'time_reached': time_reached,
            'threshold_direction': threshold_direction,
            'unit_symbol': unit_symbol,
            'notification_type': notification_type,
            'sent': sent,
            'viewed': viewed
        }

        return requests.post(url=RUMAHIOT_SURAT_DEVICE_NOTIFICATION_LOGGER_ENDPOINT, data=payload, headers=header)