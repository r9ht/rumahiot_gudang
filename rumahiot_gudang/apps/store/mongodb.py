from pymongo import MongoClient
from rumahiot_gudang.settings import RUMAHIOT_GUDANG_MONGO_HOST,RUMAHIOT_GUDANG_MONGO_PASSWORD,RUMAHIOT_GUDANG_MONGO_USERNAME,RUMAHIOT_GUDANG_DATABASE,RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION,RUMAHIOT_GUDANG_DEVICE_DATA_COLLECTION,RUMAHIOT_GUDANG_SENSOR_DETAIL_COLLECTION

class GudangMongoDB():

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
    def get_user_device_data(self,key,key_type):
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

    # Get user device data using device_uuid
    # Input parameter : device_uuid(string)
    # return result(dict)
    def get_user_device_data_uuid(self,device_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION]
        result = col.find_one({'device_uuid':device_uuid})
        return result

    # Get user device list using user_uuid
    # Input parameter : user_uuid(string), skip(int), limit(int), text(string), direction(int)
    # return : result(dict)
    # Default value for skip, limit, and text will be set on view instead
    def get_user_device_list(self,user_uuid,skip,limit,text,direction):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION]
        # The user_uuid match is a must , the device_name and location_text are added field
        # For direction 1 is ascending, and -1 is descending
        # -i Indicate insensitive case for the parameter
        results = col.find({'$and':[{'user_uuid':user_uuid},{'$or':[{'device_name':{'$regex':text,'$options': '-i'}},{"location_text":{'$regex':text,'$options': '-i'}}]}]}).sort([("_id",direction)]).skip(skip).limit(limit)
        return results

    # Get device data using device uuid and time filter
    # All date using unix timestamp format
    # Input parameter : device_uuid(string), skip(int), limit(int), direction(int),from_date(float), to_date(float)
    # For direction 1 is ascending, and -1 is descending
    def get_device_data(self,device_uuid,skip,limit,direction,from_date,to_date):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_DEVICE_DATA_COLLECTION]
        # lt operator stand for less than
        # gt operator stand for greater than
        # Filter using specified time range, limit, skip, and direction
        results = col.find({'$and':[{'device_uuid':device_uuid},{'time_added': {'$lt': to_date}}, {'time_added': {'$gt': from_date}}]}).sort([("_id",direction)]).skip(skip).limit(limit)
        return results

    # Get sensor detail using sensor_uuid
    # input parameter : sensor_uuid(string)
    def get_sensor_detail(self,sensor_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_SENSOR_DETAIL_COLLECTION]
        result = col.find_one({'sensor_uuid':sensor_uuid})
        return result

    # Get device detail using device_uuid
    # input parameter : device_uuid(string)
    def get_device_by_uuid(self, device_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION]
        result = col.find_one({'device_uuid': device_uuid})
        return result

    # Update device sensor data
    # input parameter : object_id(string), new_sensor_list(list)
    def update_device_sensor(self, object_id, new_sensor_list):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION]
        result = col.find_one_and_update({'_id': object_id},{'$set': {'device_sensors': new_sensor_list}})
        return result



