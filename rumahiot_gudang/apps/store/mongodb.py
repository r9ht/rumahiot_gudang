from pymongo import MongoClient
from rumahiot_gudang.settings import RUMAHIOT_GUDANG_MONGO_HOST,RUMAHIOT_GUDANG_MONGO_PASSWORD,RUMAHIOT_GUDANG_MONGO_USERNAME,RUMAHIOT_GUDANG_DATABASE,RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION



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

    # Get user device list using user_uuid
    # Input parameter : user_uuid(string), skip(int), limit(int), text(string)
    # return : result(dict)
    # Default value for skip, limit, and text will be set on view instead
    def get_user_device_list(self,user_uuid,skip,limit,text):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
        col = db[RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION]
        results = col.find({'user_uuid':user_uuid}).skip(skip).limit(limit)
        return results

    def get_sensor_detail(self,sensor_uuid):
        db = self.client[RUMAHIOT_GUDANG_DATABASE]
