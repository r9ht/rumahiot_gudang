# Define device resource model in here so the structure can be verified

# Sensor resource
class SensorDataResource(object):
    def __init__(self, user_sensor_uuid, user_sensor_value):
        self.user_sensor_uuid = user_sensor_uuid
        self.user_sensor_value = user_sensor_value

# Store device data resource
class DeviceDataResource(object):
    def __init__(self, write_key, sensor_datas):
        self.write_key = write_key
        self.sensor_datas = sensor_datas

# Store new device resource
class NewDeviceResource(object):
    def __init__(self, position, location_text, device_name, supported_board_uuid,
                 added_sensors, user_wifi_connection_uuid, device_data_sending_interval):
        self.position = position
        self.location_text = location_text
        self.device_name = device_name
        self.supported_board_uuid = supported_board_uuid
        self.added_sensors = added_sensors
        self.user_wifi_connection_uuid = user_wifi_connection_uuid
        self.device_data_sending_interval = device_data_sending_interval

# Device position resource
class DevicePositionResource(object):
    def __init__(self, lat, lng):
        self.lat = lat
        self.lng = lng

# Added Sensor resource
class AddedSensorResource(object):
    def __init__(self, added_sensor_name, master_sensor_reference_uuid, sensor_pin_mappings):
        self.added_sensor_name = added_sensor_name
        self.master_sensor_reference_uuid = master_sensor_reference_uuid
        self.sensor_pin_mappings = sensor_pin_mappings

# Sensor pin mapping resource
class SensorPinMappingResource(object):
    def __init__(self, sensor_pin, device_pin, device_arduino_pin, device_pin_name,
                 function):
        self.sensor_pin = sensor_pin
        self.device_pin = device_pin
        self.device_arduino_pin = device_arduino_pin
        self.device_pin_name = device_pin_name
        self.function = function

# Update device detail resource
class UpdateDeviceDetailResource(object):
    def __init__(self, device_uuid, device_name, position, user_wifi_connection_uuid):
        self.device_uuid = device_uuid
        self.device_name = device_name
        self.position = position
        self.user_wifi_connection_uuid = user_wifi_connection_uuid