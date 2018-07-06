# Define device resource model in here so the structure can be verified

# Add new supported sensor resouce
class NewSupportedSensorResource(object):
    def __init__(self, library_dependencies, library_variable_initialization, library_initialization_command, sensor_pin_mappings,
                 sensor_model, sensor_image_url, sensor_image_source, master_sensors):
        self.library_dependencies = library_dependencies
        self.library_variable_initialization = library_variable_initialization
        self.library_initialization_command = library_initialization_command
        self.sensor_pin_mappings = sensor_pin_mappings
        self.sensor_model = sensor_model
        self.sensor_image_url = sensor_image_url
        self.sensor_image_source = sensor_image_source
        self.master_sensors = master_sensors

# Sensor pin mapping resource for adding new supported sensor
class NewSupportedSensorMappingResource(object):
    def __init__(self, pin, function, pin_name):
        self.pin = pin
        self.function = function
        self.pin_name = pin_name


# Library variable initalization resource
class LibraryVariableInitializationResource(object):
    def __init__(self, code, code_filler):
        self.code = code
        self.code_filler = code_filler

# Master sensor for adding new supported sensor
class MasterSensorResource(object):
    def __init__(self, master_sensor_name, master_sensor_default_unit_name,
                 master_sensor_default_unit_symbol, master_sensor_library_function,
                 master_sensor_reference_uuid):

        self.master_sensor_name = master_sensor_name
        self.master_sensor_default_unit_name = master_sensor_default_unit_name
        self.master_sensor_default_unit_symbol = master_sensor_default_unit_symbol
        self.master_sensor_library_function = master_sensor_library_function
        self.master_sensor_reference_uuid = master_sensor_reference_uuid

# Add new board resource
class NewSupportedBoardResource(object):
    def __init__(self, board_name, chip, manufacturer, board_specification, board_image,
                 board_image_source, board_pins, version, s3_path):
        self.board_name = board_name
        self.chip = chip
        self.manufacturer = manufacturer
        self.board_specification = board_specification
        self.board_image = board_image
        self.board_image_source = board_image_source
        self.board_pins = board_pins
        self.version = version
        self.s3_path = s3_path

# Update board resource
class UpdateSupportedBoardResource(object):
    def __init__(self, board_uuid, board_name, chip, manufacturer, board_specification, board_image,
                 board_image_source, board_pins, version, s3_path):
        self.board_uuid = board_uuid
        self.board_name = board_name
        self.chip = chip
        self.manufacturer = manufacturer
        self.board_specification = board_specification
        self.board_image = board_image
        self.board_image_source = board_image_source
        self.board_pins = board_pins
        self.version = version
        self.s3_path = s3_path

# New board pin resource
class NewSupportedBoardPinResource(object):
    def __init__(self, name, functions, pin, arduino_pin):
        self.name = name
        # Dont forget to make sure it is a list consist of strings
        self.functions = functions
        self.pin = pin
        self.arduino_pin = arduino_pin

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
    def __init__(self, device_uuid, device_name, position, user_wifi_connection_uuid, location_text, device_data_sending_interval):
        self.device_uuid = device_uuid
        self.device_name = device_name
        self.position = position
        self.user_wifi_connection_uuid = user_wifi_connection_uuid
        self.location_text = location_text
        self.device_data_sending_interval = device_data_sending_interval