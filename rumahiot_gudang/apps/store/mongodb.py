from pymongo import MongoClient
from uuid import uuid4
import pymongo

from rumahiot_gudang.settings import RUMAHIOT_GUDANG_MONGO_HOST, \
    RUMAHIOT_GUDANG_MONGO_PASSWORD, \
    RUMAHIOT_GUDANG_MONGO_USERNAME, \
    RUMAHIOT_GUDANG_DATABASE, \
    RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION, \
    RUMAHIOT_GUDANG_DEVICE_DATA_COLLECTION, \
    RUMAHIOT_GUDANG_SENSOR_DETAIL_COLLECTION, \
    RUMAHIOT_GUDANG_MASTER_SENSORS_COLLECTION, \
    RUMAHIOT_GUDANG_USER_SENSORS_COLLECTION, \
    RUMAHIOT_GUDANG_SUPPORTED_BOARD_COLLECTION, \
    RUMAHIOT_GUDANG_MASTER_SENSOR_REFERENCES_COLLECTION, \
    RUMAHIOT_GUDANG_USER_SENSOR_MAPPINGS_COLLECTIONS, \
    MATERIAL_COLORS_COLLECTION, \
    RUMAHIOT_LEMARI_USER_WIFI_CONNECTIONS_COLLECTION, \
    RUMAHIOT_LEMARI_USER_EXPORTED_XLSX_COLLECTION, \
    RUMAHIOT_GUDANG_GAMPANG_TEMPLATES_COLLECTION, \
    RUMAHIOT_GUDANG_TLS_FINGERPRINTS_COLLECTION, \
    RUMAHIOT_LEMARI_USER_DASHBOARD_CHARTS_COLLECTION

from bson.json_util import dumps
import json, datetime


class GudangMongoDB:

    # initiate the client
    def __init__(self):
        self.client = MongoClient(RUMAHIOT_GUDANG_MONGO_HOST,
                                  username=RUMAHIOT_GUDANG_MONGO_USERNAME,
                                  password=RUMAHIOT_GUDANG_MONGO_PASSWORD,
                                  )

    # get device data count by device uuid
    def get_device_data_count_by_uuid(self, device_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_DEVICE_DATA_COLLECTION]
        return col.find({
            'device_uuid': device_uuid
        }).count(True)

    # Get user device by user_uuid
    def get_user_device_list_by_user_uuid(self, user_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION]
        return col.find({
            'user_uuid': user_uuid,
            'removed': False
        })

    # Get material color document from db
    def get_material_color_document(self):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[MATERIAL_COLORS_COLLECTION]
        return col.find_one()

    # Put data into specified database and collection
    # input parameter : database(string), collection(string), data(dictionary)
    # return : result(dict)
    def put_data(self, database, collection, data):
        db = self.client[database]
        col = db[collection]
        result = col.insert_one(data)
        return result

    # Get all device data
    # return : result(dict)
    def get_all_user_device_data(self):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION]
        result = col.find({})
        return result

    # Get device data using write_key or read_key
    # Input parameter : key(string), key_type(string)
    # return : result(dict)
    def get_user_device_data(self, key, key_type):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION]
        # w for write_key , r for read_key
        if key_type == "w":
            result = col.find_one({'write_key': key, 'removed': False})
        elif key_type == "r":
            result = col.find_one({'read_key': key, 'removed': False})
        else:
            result = None
        return result

    # Get user device list using user_uuid
    # Input parameter : user_uuid(string), skip(int), limit(int), text(string), direction(int)
    # return : result(dict)
    # Default value for skip, limit, and text will be set on view instead
    def get_user_device_list(self, user_uuid, skip, limit, text, direction):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION]
        # The user_uuid match is a must , the device_name and location_text are added field
        # For direction 1 is ascending, and -1 is descending
        # -i Indicate insensitive case for the parameter
        results = col.find({'$and': [{'user_uuid': user_uuid}, {
            '$or': [{'device_name': {'$regex': text, '$options': '-i'}},
                    {"location_text": {'$regex': text, '$options': '-i'}}]}, {'removed': False}]}).sort([("_id", direction)]).skip(
            skip).limit(limit)
        return results

    # Get device data using device uuid and time filter
    # All date using unix timestamp format
    # Input parameter : device_uuid(string), skip(int), limit(int), direction(int),from_date(float), to_date(float)
    # For direction 1 is ascending, and -1 is descending
    # Todo: change date to time
    def get_device_data(self, device_uuid, skip, limit, direction, from_date, to_date):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_DEVICE_DATA_COLLECTION]
        # lt operator stand for less than
        # gt operator stand for greater than
        # Filter using specified time range, limit, skip, and direction
        results = col.find({'$and': [{'device_uuid': device_uuid}, {'time_added': {'$lte': to_date}},
                                     {'time_added': {'$gte': from_date}}]}).sort([("time_added", direction)]).skip(skip).limit(limit)
        return results

    # Get device sensor average, min, and maximum sensor value from certain range
    # Input parameter : from_time(float, unix timestamp), to_time(float, unix_timestamp), device_uuid(string), user_sensor_uuid (string)
    # from time -> greater than , to_time -> less than equal
    def user_sensor_statistic_data(self, from_time, to_time, device_uuid, user_sensor_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_DEVICE_DATA_COLLECTION]
        results = col.aggregate(
            [    # Unwind the data so the calculation can be done
                {
                    '$unwind': '$sensor_datas'
                },
                {
                    '$match': {'$and': [{'time_added': {'$gt': from_time, '$lte': to_time}}, {'device_uuid': device_uuid}, {'sensor_datas.user_sensor_uuid': user_sensor_uuid}]}
                },
                {
                    '$group': {
                        '_id': {'user_sensor_uuid': '$sensor_datas.user_sensor_uuid', 'device_uuid': '$device_uuid'},
                        'user_sensor_value_average': { '$avg': '$sensor_datas.user_sensor_value'},
                        'user_sensor_value_max': { '$max': '$sensor_datas.user_sensor_value'},
                        'user_sensor_value_min': { '$min': '$sensor_datas.user_sensor_value'},
                        'data_count': { '$sum': 1}
                    }
                },
                {
                    '$sort': {'time_added' : 1}
                }
            ]
        )
        # bson dumps will take empty list as a string
        return json.loads(dumps(results))

    # Get sensor detail using sensor_uuid
    # input parameter : sensor_uuid(string)
    def get_sensor_detail(self, sensor_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_SENSOR_DETAIL_COLLECTION]
        result = col.find_one({'sensor_uuid': sensor_uuid})
        return result

    # Get device detail using device_uuid
    # input parameter : device_uuid(string)
    def get_device_by_uuid(self, device_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION]
        result = col.find_one({'device_uuid': device_uuid, 'removed': False})
        return result

    # get user sensor using user_sensor_uuid
    # input parameter: user_sensor_uuid(string)
    def get_user_sensor_by_uuid(self, user_sensor_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USER_SENSORS_COLLECTION]
        result = col.find_one({'user_sensor_uuid': user_sensor_uuid})
        return result

    # get user sensor by master sensor
    def get_user_sensor_by_master_sensor(self, master_sensor_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USER_SENSORS_COLLECTION]
        result = col.find_one({'master_sensor_uuid': master_sensor_uuid})
        return result

    # get master sensor using master_sensor_uuid
    # input parameter: mster_sensor_uuid(string)
    def get_master_sensor_by_uuid(self, master_sensor_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_MASTER_SENSORS_COLLECTION]
        result = col.find_one({'master_sensor_uuid': master_sensor_uuid})
        return result

    # Update device detail data
    # device_name, user_wifi_connection_uuid, and location
    def update_device_detail(self, device_uuid, device_name, user_wifi_connection_uuid, position, location_text, device_data_sending_interval):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION]
        col.update_one({'device_uuid': device_uuid}, {'$set': {'device_name': device_name,
                                                     'user_wifi_connection_uuid': user_wifi_connection_uuid,
                                                     'position': position, 'location_text': location_text, 'device_data_sending_interval': device_data_sending_interval
                                                     }})

    # get n latest device data
    # input parameter : device_uuid(string), n (integer)
    # Datas are in descending order
    def get_n_latest_device_data(self, device_uuid, n):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_DEVICE_DATA_COLLECTION]
        results = col.find({'device_uuid': device_uuid}).sort([("time_added", -1)]).limit(n)
        return results

    # update user sensor detail
    # input parameter : object_id (string, mongodb object id), new_threshold_value(float), new_sensor_name(string), threshold_direction (string),threshold_enabled (boolean)
    def update_user_sensor_detail(self, object_id, new_threshold_value, new_user_sensor_name, threshold_direction, threshold_enabled):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USER_SENSORS_COLLECTION]
        col.update_one({'_id': object_id}, {'$set': {'sensor_threshold': new_threshold_value,
                                                     'threshold_direction': threshold_direction,
                                                     'threshold_enabled': threshold_enabled,
                                                     'user_sensor_name':new_user_sensor_name}})

    # get all supported board list
    def get_all_supported_board(self):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_SUPPORTED_BOARD_COLLECTION]
        result = col.find({})
        return result

    # Update sensor currently_above_threshold status
    # input parameter : object_id (string, mongodb object id), new currently_above_threshold status (boolean)
    def update_currently_over_threshold(self, object_id, new_status):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USER_SENSORS_COLLECTION]
        col.update_one({'_id': object_id},
                       {'$set': {'currently_over_threshold': new_status}})

    # Find supported board by board_uuid
    # Input parameter : board_id (string)
    def get_supported_board_by_uuid(self, board_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_SUPPORTED_BOARD_COLLECTION]
        result = col.find_one({
                'board_uuid': board_uuid
            })
        return result

    # Put user sensor into db
    # Input parameter : user_sensor (dict)
    def put_user_sensor(self, user_sensor):
        result = self.put_data(database=RUMAHIOT_GUDANG_DATABASE, collection=RUMAHIOT_GUDANG_USER_SENSORS_COLLECTION, data=user_sensor)
        return result

    # Put user sensor mapping into db
    # Input parameter : user_sensor_mapping(dict)
    def put_user_sensor_mapping(self, user_sensor_mapping):
        result = self.put_data(database=RUMAHIOT_GUDANG_DATABASE, collection=RUMAHIOT_GUDANG_USER_SENSOR_MAPPINGS_COLLECTIONS, data=user_sensor_mapping)
        return result

    # Put user device into db
    # Input parameter : user_device (dict)
    def put_user_device(self, user_device):
        result = self.put_data(database=RUMAHIOT_GUDANG_DATABASE, collection=RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION, data=user_device)
        return result

    # Get all master sensor reference (For adding and configuring new device
    def get_all_master_sensor_reference(self):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_MASTER_SENSOR_REFERENCES_COLLECTION]
        result = col.find({})
        return result

    # Get master_sensor_reference by uuid
    # Input : master_sensor_reference_uuid (string)
    def get_master_sensor_reference_by_uuid(self, master_sensor_reference_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_MASTER_SENSOR_REFERENCES_COLLECTION]
        result = col.find_one({
            'master_sensor_reference_uuid': master_sensor_reference_uuid
        })
        return result

    # Get all sensor mappings
    def get_all_user_sensor_mappings(self):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USER_SENSOR_MAPPINGS_COLLECTIONS]
        result = col.find({})
        return result

    # Get sensor mapping by user_sensor_mapping_uuid
    def get_sensor_mapping_by_uuid(self, user_sensor_mapping_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USER_SENSOR_MAPPINGS_COLLECTIONS]
        result = col.find_one({
            'user_sensor_mapping_uuid': user_sensor_mapping_uuid
        })
        return result

    # Get user_wifi_connection using user_wifi_connection_uuid and user_uuid
    # Input parameter : user_wifi_connection_uuid (string), user_uuid(string)
    def get_user_wifi_connection_by_uuid(self, user_wifi_connection_uuid, user_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_LEMARI_USER_WIFI_CONNECTIONS_COLLECTION]
        result = col.find_one({
            'user_uuid': user_uuid,
            'user_wifi_connection_uuid': user_wifi_connection_uuid
        })
        return result

    # Get raw device sensor data with the specified interval
    # Input parameter : device_uuid(string), user_sensor_uuid(string), from_time(float, unix timestamp), to_time(float, unix timestamp)
    def get_device_sensor_data_interval(self, device_uuid, user_sensor_uuid, from_time, to_time):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_DEVICE_DATA_COLLECTION]
        results = col.aggregate(
            [  # Unwind the data so the calculation can be done
                {
                    '$unwind': '$sensor_datas'
                },
                {
                    '$match': {'$and': [{'time_added': {'$gt': from_time, '$lte': to_time}}, {'device_uuid': device_uuid}, {'sensor_datas.user_sensor_uuid': user_sensor_uuid}]}
                },
                {
                    '$sort': {'time_added': 1}
                }
            ]
        )

        # bson dumps will take empty list as a string
        return json.loads(dumps(results))

    # Get device data by uuid
    # Input : user_uuid(string), device_uuid(string)
    def get_device_data_by_uuid(self, user_uuid, device_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION]
        result = col.find_one({'user_uuid': user_uuid, 'device_uuid': device_uuid, 'removed': False})
        return result

    # Put new user exported xlsx document
    def put_user_exported_xlsx(self, user_uuid, user_exported_xlsx_uuid, device_uuid, from_time, to_time):
        data = {
            'user_uuid': user_uuid,
            'device_uuid': device_uuid,
            'from_time': float(from_time),
            'to_time': float(to_time),
            'user_exported_xlsx_uuid': user_exported_xlsx_uuid,
            'document_ready': False,
            'document_link': '',
            'time_updated': datetime.datetime.now().timestamp()
        }
        self.put_data(database=RUMAHIOT_GUDANG_DATABASE, collection=RUMAHIOT_LEMARI_USER_EXPORTED_XLSX_COLLECTION, data=data)

    # Update user exported xlsx document
    def update_user_exported_xlsx(self, user_exported_xlsx_uuid, document_link):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_LEMARI_USER_EXPORTED_XLSX_COLLECTION]
        col.update_one({'user_exported_xlsx_uuid': user_exported_xlsx_uuid}, {'$set': {'document_ready': True,'document_link': document_link,'time_updated': datetime.datetime.now().timestamp()}})


    # Get the latest gampang arduino code
    def get_latest_gampang_template_document(self, supported_board_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_GAMPANG_TEMPLATES_COLLECTION]
        return col.find_one({'supported_board_uuid': supported_board_uuid}, sort=[("time_added", pymongo.DESCENDING)])

    # Get the latest rumahiot TLS fingerprint
    def get_latest_tls_fingerprint(self, algorithm, domain):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_TLS_FINGERPRINTS_COLLECTION]
        return col.find_one({'algorithm': algorithm, 'domain': domain}, sort=[("time_issued", pymongo.DESCENDING)])

    # Get user sensor by user sensor mapping uuid
    def get_user_sensor_by_mapping_uuid(self, user_sensor_mapping_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USER_SENSORS_COLLECTION]
        result = col.find({
            'user_sensor_mapping_uuid': user_sensor_mapping_uuid
        })
        return result

    def get_user_sensor_mapping_by_uuid(self, user_sensor_mapping_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USER_SENSOR_MAPPINGS_COLLECTIONS]
        result = col.find_one({
            'user_sensor_mapping_uuid': user_sensor_mapping_uuid
        })
        return result

    # Remove user_device
    # Input : device_uuid (string)
    def remove_user_device(self, device_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION]
        col.update_one({'device_uuid': device_uuid, 'removed': False}, {'$set': {'removed': True}})
        # Remove the dashboard chart
        col = db[RUMAHIOT_LEMARI_USER_DASHBOARD_CHARTS_COLLECTION]
        col.remove({
            'device_uuid': device_uuid
        })

        # (self, board_name, chip, manufacturer, board_specification, board_image,
        #  board_image_source, board_pins, version, s3_path):

    # Add new supported board
    def put_new_supported_board(self, board_name, chip, manufacturer, board_specification, board_image, board_image_source, board_pins, version, s3_path):
        # UUIDs
        board_uuid = uuid4().hex

        # Datas
        supported_board_data = {
            'board_uuid': board_uuid,
            'board_name': board_name,
            'chip': chip,
            'manufacturer': manufacturer,
            'board_specification' : board_specification,
            'board_image': board_image,
            'board_image_source': board_image_source,
            'board_pins': board_pins
        }

        gampang_template_data = {
            'gampang_template_uuid': uuid4().hex,
            'supported_board_uuid': board_uuid,
            'time_added': datetime.datetime.now().timestamp(),
            'version': version,
            's3_path': s3_path

        }

        # Create supported board
        self.put_data(database=RUMAHIOT_GUDANG_DATABASE, collection=RUMAHIOT_GUDANG_SUPPORTED_BOARD_COLLECTION, data = supported_board_data)
        # Create gampang template mapping
        self.put_data(database=RUMAHIOT_GUDANG_DATABASE, collection=RUMAHIOT_GUDANG_GAMPANG_TEMPLATES_COLLECTION, data=gampang_template_data)

    # Remove supported board and it's template mapping
    def remove_supported_board(self, board_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]

        board_col = db[RUMAHIOT_GUDANG_SUPPORTED_BOARD_COLLECTION]
        template_col = db[RUMAHIOT_GUDANG_GAMPANG_TEMPLATES_COLLECTION]

        # Remove the board and template
        board_col.remove({
            'board_uuid': board_uuid
        })
        template_col.remove({
            'supported_board_uuid': board_uuid
        })

    # Get device by board_uuid
    def get_device_by_board_uuid(self, board_uuid):

        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION]
        result = col.find({
            'supported_board_uuid': board_uuid
        })

        return result

    # Update supported board configuration
    def update_supported_board(self, board_uuid, board_name, chip, manufacturer, board_specification, board_image, board_image_source, board_pins, version, s3_path):

        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        board_col = db[RUMAHIOT_GUDANG_SUPPORTED_BOARD_COLLECTION]
        template_col = db[RUMAHIOT_GUDANG_GAMPANG_TEMPLATES_COLLECTION]

        # Update the board
        board_col.update_one({'board_uuid' : board_uuid}, {'$set': {
            'board_name': board_name,
            'chip': chip,
            'manufacturer': manufacturer,
            'board_specification': board_specification,
            'board_image': board_image,
            'board_image_source': board_image_source,
            'board_pins': board_pins
        }})

        # Update the template
        template_col.update_one({'supported_board_uuid': board_uuid}, {'$set': {
            'version': version,
            's3_path': s3_path
        }})


    def get_all_detailed_supported_board(self):

        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        board_col = db[RUMAHIOT_GUDANG_SUPPORTED_BOARD_COLLECTION]
        template_col = db[RUMAHIOT_GUDANG_GAMPANG_TEMPLATES_COLLECTION]

        # Detailed supported board object
        detailed_supported_boards = []

        # Find board and template
        board_results = board_col.find({})
        for board_result in board_results:
            # Get the template
            template = template_col.find_one({
                'supported_board_uuid' : board_result['board_uuid']
            })

            detailed_supported_board = {
                'board_uuid' : board_result['board_uuid'],
                'board_name' : board_result['board_name'],
                'chip' : board_result['chip'],
                'manufacturer' : board_result['manufacturer'],
                'board_specification' : board_result['board_specification'],
                'board_image' : board_result['board_image'],
                'board_image_source' : board_result['board_image_source'],
                'board_pins' : board_result['board_pins'],
                'gampang_template_uuid' : template['gampang_template_uuid'],
                'time_added' : template['time_added'],
                'version' : template['version'],
                's3_path' : template['s3_path']
            }

            # Append to the main object
            detailed_supported_boards.append(detailed_supported_board)

        return detailed_supported_boards

    # Add new supported sensor
    def put_new_supported_sensor(self, library_dependencies, library_variable_initialization,
                                 library_initialization_command, sensor_pin_mappings, sensor_model,
                                 sensor_image_url, sensor_image_source, master_sensors):

        # Master uuid
        master_sensor_reference_uuid = uuid4().hex
        # Uuids for master sensor
        master_sensor_uuids = []

        for master_sensor in master_sensors:
            # Uuid for master sensor
            master_sensor_uuid = uuid4().hex
            master_sensor_data = {
                'master_sensor_uuid': master_sensor_uuid,
                'master_sensor_name': master_sensor['master_sensor_name'],
                'master_sensor_default_unit_name': master_sensor['master_sensor_default_unit_name'],
                'master_sensor_default_unit_symbol': master_sensor['master_sensor_default_unit_symbol'],
                'master_sensor_library_function': master_sensor['master_sensor_library_function'],
                'master_sensor_reference_uuid': master_sensor_reference_uuid
            }
            # Put master sensor
            self.put_data(database=RUMAHIOT_GUDANG_DATABASE, collection=RUMAHIOT_GUDANG_MASTER_SENSORS_COLLECTION, data=master_sensor_data)
            master_sensor_uuids.append(master_sensor_uuid)

        master_sensor_reference_data = {
            'master_sensor_reference_uuid' : master_sensor_reference_uuid,
            'library_dependencies': library_dependencies,
            'library_variable_initialization': library_variable_initialization,
            'library_initialization_command': library_initialization_command,
            'sensor_pin_mappings': sensor_pin_mappings,
            'sensor_model': sensor_model,
            'sensor_image_url': sensor_image_url,
            'master_sensor_uuids': master_sensor_uuids,
            'sensor_image_source': sensor_image_source
        }

        # Put master sensor reference
        self.put_data(database=RUMAHIOT_GUDANG_DATABASE, collection=RUMAHIOT_GUDANG_MASTER_SENSOR_REFERENCES_COLLECTION, data=master_sensor_reference_data)

    # Remove supported sensor
    def remove_supported_sensor(self, master_sensor_reference_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]

        master_sensor = db[RUMAHIOT_GUDANG_MASTER_SENSORS_COLLECTION]
        master_sensor_reference = db[RUMAHIOT_GUDANG_MASTER_SENSOR_REFERENCES_COLLECTION]

        # Remove master sensor
        master_sensor.remove({
            'master_sensor_reference_uuid': master_sensor_reference_uuid
        })
        # Remove master sensor reference
        master_sensor_reference.remove({
            'master_sensor_reference_uuid': master_sensor_reference_uuid
        })

    # Get supported sensor
    def get_all_detailed_supported_sensor(self):

        # Supported sensor main object
        supported_sensors = []

        master_sensor_references = self.get_all_master_sensor_reference()
        # Iterate through master sensor references
        for master_sensor_reference in master_sensor_references :
            sensor_reference = {
                'master_sensor_reference_uuid': master_sensor_reference['master_sensor_reference_uuid'],
                'library_dependencies': master_sensor_reference['library_dependencies'],
                'library_variable_initialization': master_sensor_reference['library_variable_initialization'],
                'library_initialization_command': master_sensor_reference['library_initialization_command'],
                'sensor_pin_mappings': master_sensor_reference['sensor_pin_mappings'],
                'sensor_model': master_sensor_reference['sensor_model'],
                'sensor_image_url': master_sensor_reference['sensor_image_url'],
                'sensor_image_source': master_sensor_reference['sensor_image_source'],
                'master_sensors': []
            }
            for master_sensor_uuid in master_sensor_reference['master_sensor_uuids']:
                master_sensor = self.get_master_sensor_by_uuid(master_sensor_uuid=master_sensor_uuid)
                master_sensor_data = {
                    'master_sensor_uuid': master_sensor['master_sensor_uuid'],
                    'master_sensor_name': master_sensor['master_sensor_name'],
                    'master_sensor_default_unit_name': master_sensor['master_sensor_default_unit_name'],
                    'master_sensor_library_function': master_sensor['master_sensor_library_function'],
                    'master_sensor_default_unit_symbol': master_sensor['master_sensor_default_unit_symbol']
                }
                # Append to master sensor reference object
                sensor_reference['master_sensors'].append(master_sensor_data)

            # Append to main object
            supported_sensors.append(sensor_reference)

        return supported_sensors

    # Update supported sensor
    def update_supported_sensor(self, master_sensor_reference_uuid, library_dependencies, library_variable_initialization,
                                 library_initialization_command, sensor_pin_mappings, sensor_model,
                                 sensor_image_url, sensor_image_source, master_sensors):


        db = self.client[RUMAHIOT_GUDANG_DATABASE]

        # Update master sensor reference
        master_sensor_reference_col = db[RUMAHIOT_GUDANG_MASTER_SENSOR_REFERENCES_COLLECTION]
        master_sensor_reference_col.update_one({'master_sensor_reference_uuid': master_sensor_reference_uuid}, {'$set': {
            'library_dependencies': library_dependencies,
            'library_variable_initialization': library_variable_initialization,
            'library_initialization_command': library_initialization_command,
            'sensor_pin_mappings': sensor_pin_mappings,
            'sensor_model': sensor_model,
            'sensor_image_url': sensor_image_url,
            'sensor_image_source': sensor_image_source
        }})

        # Update master sensor
        for master_sensor in master_sensors:
            master_sensor_col = db[RUMAHIOT_GUDANG_MASTER_SENSORS_COLLECTION]
            master_sensor_col.update_one({'master_sensor_uuid': master_sensor['master_sensor_uuid']}, {'$set': {
                'master_sensor_name': master_sensor['master_sensor_name'],
                'master_sensor_default_unit_name': master_sensor['master_sensor_default_unit_name'],
                'master_sensor_library_function': master_sensor['master_sensor_library_function'],
                'master_sensor_default_unit_symbol': master_sensor['master_sensor_default_unit_symbol']
            }})








