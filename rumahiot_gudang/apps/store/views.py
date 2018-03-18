from django.shortcuts import render,HttpResponse
from rumahiot_gudang.apps.store.mongodb import GudangMongoDB
from rumahiot_gudang.settings import RUMAHIOT_GUDANG_DATABASE,RUMAHIOT_GUDANG_DEVICE_DATA_COLLECTION,RUMAHIOT_GUDANG_SENSOR_DETAIL_COLLECTION
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
from rumahiot_gudang.apps.store.utils import RequestUtils,ResponseGenerator, GudangUtils
from rumahiot_gudang.apps.store.resource import DeviceDataResource, SensorDataResource

# Create your views here.

def mock_view(request):
    a = GudangMongoDB()
    # data = {
    #         'data' :
    #             {
    #                 'write_key' : '12345',
    #                 'device_data' : [
    #                     {
    #                         'device_sensor_uuid': '123453',
    #                         'device_sensor_value' : '12.4'
    #                     },
    #                     {
    #                         'device_sensor_uuid': '123454',
    #                         'device_sensor_value': '12.4'
    #                     }
    #                 ]
    #
    #             }
    #
    #         }
    # data = {
    #      "device_sensors": [
    #     "e6a2b64dd73d443aad765d2e7e8958d9",
    # "8d3655e349b44845abaa03e93d5a3f38"
    #     ],
    #     "device_uuid": "8d3655e349b44845abaa03e93d5a3f38",
    #     "location": "12.12313,1212.1414",
    #     "location_text" : "Hehehe",
    # "read_key": "2277ccbac02f4679910de9bf9bbef74e",
    # "time_added": 1212121.12,
    #     "user_uuid": "5083b3ed6d4341ff9d9a6f4f649f1f31",
    #     "write_key": "f454805a928543f48a15bcf3d4401999",
    #     "device_name" : "Mancing 2"
    # }
    # data2 = {
    #     'sensor_uuid' : 'e6a2b64dd73d443aad765d2e7e8958d9',
    #     'sensor_name' : 'DHT 11'
    # }
    #a.put_data(database=RUMAHIOT_GUDANG_DATABASE,collection=RUMAHIOT_GUDANG_SENSOR_DETAIL_COLLECTION,data=data2)
    #b = a.put_data(database=RUMAHIOT_GUDANG_DATABASE,collection='rumahiot_user_devices',data=data)
    #result = a.get_all_user_device_data()
    #result = a.get_user_device_list("5083b3ed6d4341ff9d9a6f4f649f1f31")
    # for a in result:
    #     print(a)



# Handle request sent by device
@csrf_exempt
def store_device_data(request):

    # Gudang classes
    rg = ResponseGenerator()
    # Construct sensor_list from request and compare it with the one in the user_device document
    sensor_list = []

    if request.method != "POST":
        response_data = rg.error_response_generator(400, "Bad request method")
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
    else:
        try:
            # Verify the data format
            j = json.loads(request.body.decode('utf-8'))
            d = DeviceDataResource(**j)
            db = GudangMongoDB()
            gutils = GudangUtils()

        except TypeError:
            response_data = rg.error_response_generator(400,"One of the request inputs is not valid")
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
        except ValueError:
            response_data = rg.error_response_generator(400, "Malformed JSON")
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
        else:
            # make sure the device data type is correct
            # str for write_key and list for sensor_datas
            if type(d.write_key) is str and type(d.sensor_datas) is list:
                # check the write key
                device_data = db.get_user_device_data(key=d.write_key,key_type="w")
                if device_data != None:
                    # Check the data structure and make sure the sensor exist in user device
                    for data in d.sensor_datas:
                        try:
                            # Verify the sensor data
                            s = SensorDataResource(**data)
                        except TypeError:
                            response_data = rg.error_response_generator(400, "One of the request inputs is not valid")
                            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
                        except ValueError:
                            response_data = rg.error_response_generator(400, "Malformed JSON")
                            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
                        else:
                            # make sure the sensor data type is correct
                            # str for device_sensor_uuid and float for device_sensor_value
                            if type(s.user_sensor_uuid) is str and gutils.float_check(s.user_sensor_value):
                                # Append the uuid from request to comapre with the one in user_device document
                                sensor_list.append(s.user_sensor_uuid)
                                pass
                            else:
                                response_data = rg.error_response_generator(400, "Incorrect field type")
                                return HttpResponse(json.dumps(response_data), content_type="application/json",
                                                    status=400)

                    # Sensor list from corresponding device
                    db_sensor_list = [sensor for sensor in device_data['user_sensor_uuids']]

                    # Use sort to make sure both data in the same order

                    db_sensor_list.sort()
                    sensor_list.sort()

                    # Match the data from user_device collection with the one from the request
                    if db_sensor_list == sensor_list:
                        try:
                            # put the time into the data
                            j['time_added'] = datetime.now().timestamp()
                            # Put the write key away
                            j.pop('write_key', None)
                            # Add the device_uuid
                            j['device_uuid'] = device_data['device_uuid']
                        # for unknown error
                        except:
                            response_data = rg.error_response_generator(500, "Internal server error")
                            return HttpResponse(json.dumps(response_data), content_type="application/json", status=500)
                        else:
                            response = db.put_data(database=RUMAHIOT_GUDANG_DATABASE,collection=RUMAHIOT_GUDANG_DEVICE_DATA_COLLECTION,data=j)
                            if response != None:
                                response_data = rg.success_response_generator(200, "Device data successfully submitted")
                                return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)
                            else:
                                # If the mongodb server somehow didn't return the object id
                                response_data = rg.error_response_generator(500, "Internal server error")
                                return HttpResponse(json.dumps(response_data), content_type="application/json",
                                                    status=500)
                    else:
                        response_data = rg.error_response_generator(400, "Invalid sensor configuration")
                        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
                else:
                    response_data = rg.error_response_generator(400, "Invalid Write Key")
                    return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

            else:
                response_data = rg.error_response_generator(400, "Incorrect field type")
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)








