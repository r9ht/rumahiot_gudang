
# Define device resource model in here so the structure can be verified

class SensorDataResource(object):
    def __init__(self, device_sensor_uuid, device_sensor_value):
        self.device_sensor_uuid = device_sensor_uuid
        self.device_sensor_value = device_sensor_value

class DeviceDataResource(object):
    def __init__(self, write_key, sensor_datas):
        self.write_key = write_key
        self.sensor_datas = sensor_datas