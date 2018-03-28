# Define device resource model in here so the structure can be verified

class SensorDataResource(object):
    def __init__(self, user_sensor_uuid, user_sensor_value):
        self.user_sensor_uuid = user_sensor_uuid
        self.user_sensor_value = user_sensor_value


class DeviceDataResource(object):
    def __init__(self, write_key, sensor_datas):
        self.write_key = write_key
        self.sensor_datas = sensor_datas
