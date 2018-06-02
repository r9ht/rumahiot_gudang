# This file should contain interface for generating device code from user device data using jinja2 template engine
from jinja2 import Template
from rumahiot_gudang.apps.store.s3 import GudangS3
from datetime import datetime
from rumahiot_gudang.apps.store.mongodb import GudangMongoDB
from rumahiot_gudang.apps.store.utils import GudangUtils

class GudangTemplateMaster:

    def __init__(self, device, wifi_connection, tls_fingerprint):
        self.s3 = GudangS3()
        self.db = GudangMongoDB()
        self.gutils = GudangUtils()
        self.device = device
        self.wifi_connection = wifi_connection
        self.tls_fingerprint = tls_fingerprint
        self.library_dependencies = []
        self.sensor_configurations = []
        # For differentiating between each sensor
        user_sensor_mapping_uuid_temp = []
        master_sensor_reference_uuid_temp = []

        for user_sensor_uuid in self.device['user_sensor_uuids']:
            # Todo : Find a better way to optimize the query
            user_sensor = self.db.get_user_sensor_by_uuid(user_sensor_uuid=user_sensor_uuid)
            user_sensor_mapping = self.db.get_sensor_mapping_by_uuid(user_sensor_mapping_uuid=user_sensor['user_sensor_mapping_uuid'])
            master_sensor = self.db.get_master_sensor_by_uuid(master_sensor_uuid=user_sensor['master_sensor_uuid'])
            master_sensor_reference = self.db.get_master_sensor_reference_by_uuid(master_sensor_reference_uuid=master_sensor['master_sensor_reference_uuid'])
            # Added library
            # Iterate through library dependencies inside master sensor referece
            for library_dependency in master_sensor_reference['library_dependencies']:
                if library_dependency not in self.library_dependencies:
                    # only add it it if it's haven't been added earlier
                    self.library_dependencies.append(library_dependency)

            # Mark sensor mapping and master sensor reference
            if user_sensor_mapping['user_sensor_mapping_uuid'] not in user_sensor_mapping_uuid_temp:
                user_sensor_mapping_uuid_temp.append(user_sensor_mapping['user_sensor_mapping_uuid'])
                master_sensor_reference_uuid_temp.append(master_sensor_reference['master_sensor_reference_uuid'])

        # Library variable initialization
        for mapping_index in range(0,len(user_sensor_mapping_uuid_temp)):
            master_sensor_reference = self.db.get_master_sensor_reference_by_uuid(master_sensor_reference_uuid=master_sensor_reference_uuid_temp[mapping_index])
            user_sensor_mapping = self.db.get_sensor_mapping_by_uuid(user_sensor_mapping_uuid=user_sensor_mapping_uuid_temp[mapping_index])
            # Retrieve the user sensor back
            user_sensors = self.db.get_user_sensor_by_mapping_uuid(user_sensor_mapping_uuid=user_sensor_mapping_uuid_temp[mapping_index])
            # Random varname for each sensor
            sensor_varname = self.gutils.generate_random_id(8)
            # List for sensor code formatting
            code_filler_list = []
            # List for sensor configuration for each physical sensor
            sensor_json_configuration_format_list = []

            for code_filler in master_sensor_reference['library_variable_initialization']['code_filler']:
                # Generate the variable name
                if code_filler == 'VARNAME':
                    code_filler_list.append(sensor_varname)
                else:
                    for sensor_pin_mapping in user_sensor_mapping['sensor_pin_mappings']:
                        if sensor_pin_mapping['function'] == code_filler:
                            code_filler_list.append(sensor_pin_mapping['device_arduino_pin'])

            # Iterate through each sensor value for each physical sensor
            for sensor in user_sensors:
                sensor_value_varname = self.gutils.generate_random_id(8)
                master_sensor = self.db.get_master_sensor_by_uuid(master_sensor_uuid=sensor['master_sensor_uuid'])
                # Generate the json configuration for each sensor value
                sensor_json_configuration_format_list.append('\t\tJsonObject& {} = sensor_datas.createNestedObject();\n\t\t{}["user_sensor_uuid"] = "{}";\n\t\t{}["user_sensor_value"] = {}.{}'.format(sensor_value_varname, sensor_value_varname, sensor['user_sensor_uuid'], sensor_value_varname, sensor_varname, master_sensor['master_sensor_library_function']))

            # Configuration for each physical sensor
            sensor_configuration = {
                'sensor_var_name': sensor_varname,
                'library_variable_initialization_code' : master_sensor_reference['library_variable_initialization']['code'].format(*code_filler_list),
                'library_initialization_commands':  master_sensor_reference['library_initialization_command'].format(sensor_varname),
                'sensor_configuration_datas': sensor_json_configuration_format_list
            }
            self.sensor_configurations.append(sensor_configuration)


    # Generate arduino code using template and user provided data
    def generate_gampang_template(self):
        # Grab the latest template
        latest_gampang_template = Template(self.s3.get_latest_gampang_template_string(self.device['supported_board_uuid']))
        # Prepare the parameters
        write_key = self.device['write_key']
        ssid = self.wifi_connection['ssid']
        # Wifi password
        if (self.wifi_connection['security_enabled']):
            wifi_password = self.wifi_connection['password']
        else:
            wifi_password = ''
        time_generated = datetime.now().timestamp()
        # TLS Fingerprint
        tls_fingerprint = self.tls_fingerprint['tls_fingerprint']
        # Library variable initialization
        library_variable_initialization_codes = []
        # Library initialization
        library_initialization_commands = []
        # Variable initializations for json payload data
        sensor_configuration_datas = []
        # Data sending interval
        sending_interval = self.device['device_data_sending_interval'] * 1000 * 60

        for sensor_configuration in self.sensor_configurations:
            library_variable_initialization_codes.append(sensor_configuration['library_variable_initialization_code'])
            library_initialization_commands.append(sensor_configuration['library_initialization_commands'])
            for sensor_configuration_data in sensor_configuration['sensor_configuration_datas']:
                sensor_configuration_datas.append(sensor_configuration_data)

        # print(library_variable_initialization_codes)
        # print(library_initialization_commands)
        # print(sensor_configuration_datas)
        print(latest_gampang_template.render(ssid=ssid,
                                             wifi_password=wifi_password,
                                             time_generated=time_generated,
                                             write_key=write_key,
                                             tls_fingerprint=tls_fingerprint,
                                             added_library =self.gutils.list_to_delimited_string(self.library_dependencies),
                                             library_variable_initialization=self.gutils.list_to_delimited_string(library_variable_initialization_codes),
                                             library_initialization_commands=self.gutils.list_to_delimited_string(library_initialization_commands),
                                             user_sensor_configuration=self.gutils.list_to_delimited_string(sensor_configuration_datas),
                                             sending_interval=sending_interval
                                             ))

        # print(self.sensor_configurations)


        # for sensor_configuration in self.sensor_configurations:
        #     print(sensor_configuration)
        # rendered = template.render(library="Mantap gan")
        # print(rendered)



