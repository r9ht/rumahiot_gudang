from pymongo import MongoClient

from rumahiot_gudang.settings import RUMAHIOT_GUDANG_MONGO_HOST, \
    RUMAHIOT_GUDANG_MONGO_PASSWORD, \
    RUMAHIOT_GUDANG_MONGO_USERNAME, \
    RUMAHIOT_GUDANG_DATABASE, \
    RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION, \
    RUMAHIOT_GUDANG_DEVICE_DATA_COLLECTION, \
    RUMAHIOT_GUDANG_SENSOR_DETAIL_COLLECTION, \
    RUMAHIOT_GUDANG_MASTER_SENSORS_COLLECTION, \
    RUMAHIOT_GUDANG_USER_SENSORS_COLLECTION, \
    RUMAHIOT_GUDANG_SUPPORTED_BOARD_COLLECTION
from bson.json_util import dumps
import json


class GudangMongoDB:

    # initiate the client
    def __init__(self):
        self.client = MongoClient(RUMAHIOT_GUDANG_MONGO_HOST,
                                  username=RUMAHIOT_GUDANG_MONGO_USERNAME,
                                  password=RUMAHIOT_GUDANG_MONGO_PASSWORD,
                                  )

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
            result = col.find_one({'write_key': key})
        elif key_type == "r":
            result = col.find_one({'read_key': key})
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
                    {"location_text": {'$regex': text, '$options': '-i'}}]}]}).sort([("_id", direction)]).skip(
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
                                     {'time_added': {'$gte': from_date}}]}).sort([("_id", direction)]).skip(skip).limit(limit)
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
        result = col.find_one({'device_uuid': device_uuid})
        return result

    # get user sensor using user_sensor_uuid
    # input parameter: user_sensor_uuid(string)
    def get_user_sensor_by_uuid(self, user_sensor_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USER_SENSORS_COLLECTION]
        result = col.find_one({'user_sensor_uuid': user_sensor_uuid})
        return result

    # get master sensor using master_sensor_uuid
    # input parameter: mster_sensor_uuid(string)
    def get_master_sensor_by_uuid(self, master_sensor_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_MASTER_SENSORS_COLLECTION]
        result = col.find_one({'master_sensor_uuid': master_sensor_uuid})
        return result

    # get n latest device data
    # input parameter : device_uuid(string), n (integer)
    def get_n_latest_device_data(self, device_uuid, n):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_DEVICE_DATA_COLLECTION]
        results = col.find({'device_uuid': device_uuid}).sort([("_id", -1)]).limit(n)
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

    # get supported board list
    def get_supported_board(self):
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



