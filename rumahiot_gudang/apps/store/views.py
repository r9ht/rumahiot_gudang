import json
from datetime import datetime
import copy
from uuid import uuid4

from pytz import all_timezones

from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rumahiot_gudang.apps.store.forms import ExportXlsxDeviceDataForm
from rumahiot_gudang.apps.store.xlsx import buffered_xlsxwriter

from rumahiot_gudang.apps.store.mongodb import GudangMongoDB
from rumahiot_gudang.apps.store.resource import DeviceDataResource, SensorDataResource, DevicePositionResource, SensorPinMappingResource, AddedSensorResource, NewDeviceResource
from rumahiot_gudang.apps.store.utils import ResponseGenerator, GudangUtils, RequestUtils
from rumahiot_gudang.apps.sidik_module.authorization import GudangSidikModule
from rumahiot_gudang.settings import RUMAHIOT_GUDANG_DATABASE, RUMAHIOT_GUDANG_DEVICE_DATA_COLLECTION


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
    # a.put_data(database=RUMAHIOT_GUDANG_DATABASE,collection=RUMAHIOT_GUDANG_SENSOR_DETAIL_COLLECTION,data=data2)
    # b = a.put_data(database=RUMAHIOT_GUDANG_DATABASE,collection='rumahiot_user_devices',data=data)
    # result = a.get_all_user_device_data()
    # result = a.get_user_device_list("5083b3ed6d4341ff9d9a6f4f649f1f31")
    # for a in result:
    #     print(a)

# Handle device data xlsx export
# Export process gonna be handled asynchronously
@csrf_exempt
def store_generated_device_xlsx_data(request):
    # Gudang Classes
    rg = ResponseGenerator()
    db = GudangMongoDB()
    gutils = GudangUtils()
    requtils = RequestUtils()
    auth = GudangSidikModule()

    if request.method == 'POST':
        try:
            token = requtils.get_access_token(request)
        except KeyError:
            response_data = rg.error_response_generator(401, 'Please define the authorization header')
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=401)
        else:
            if token['token'] != None:
                user = auth.get_user_data(token['token'])
                # Check token validity
                if user['user_uuid'] != None:
                    form = ExportXlsxDeviceDataForm(request.POST)
                    if form.is_valid():
                        if (gutils.float_check(form.cleaned_data['from_time']) and gutils.float_check(form.cleaned_data['to_time'])) :
                            if(float(form.cleaned_data['from_time']) < float(form.cleaned_data['to_time'])):
                                # Check for the device
                                device = db.get_device_data_by_uuid(user_uuid=user['user_uuid'], device_uuid=form.cleaned_data['device_uuid'])
                                if(device):
                                    # Check for timezone
                                    if form.cleaned_data['time_zone'] in all_timezones:

                                        user_exported_xlsx_uuid = uuid4().hex
                                        date_format = "%d-%m-%Y %H:%M:%S"

                                        # Write reserved object into db
                                        db.put_user_exported_xlsx(user_uuid=user['user_uuid'], user_exported_xlsx_uuid=user_exported_xlsx_uuid, device_uuid=device['device_uuid'], from_time=float(form.cleaned_data['from_time']), to_time=float(form.cleaned_data['to_time']))

                                        # Call the async function for generating the sheets
                                        # Todo : make the query call more efficient, by cutting the validation steps
                                        buffered_xlsxwriter(device_uuid=form.cleaned_data['device_uuid'], user_uuid=user['user_uuid'], from_time=float(form.cleaned_data['from_time']), to_time=float(form.cleaned_data['to_time']), user_exported_xlsx_uuid=user_exported_xlsx_uuid, time_zone=form.cleaned_data['time_zone'])

                                        # Return the response object
                                        # Device successfully added
                                        response_data = rg.success_response_generator(200, "Excel document export successfully queued, you can access the data in Exported Data section when it is ready")
                                        return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)

                                    else:
                                        response_data = rg.error_response_generator(400, 'Invalid timezone')
                                        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                                else:
                                    response_data = rg.error_response_generator(400, 'Invalid device uuid')
                                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                            else:
                                response_data = rg.error_response_generator(400, 'From time must be smaller than to time')
                                return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                        else:
                            response_data = rg.error_response_generator(400, 'Invalid time data format')
                            return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                    else:
                        response_data = rg.error_response_generator(400, 'Invalid form parameter submitted')
                        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                else:
                    response_data = rg.error_response_generator(401, user['error'])
                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)
            else:
                response_data = rg.error_response_generator(401, token['error'])
                return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)

    else:
        response_data = rg.error_response_generator(400, 'Bad request method')
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)


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
            response_data = rg.error_response_generator(400, "One of the request inputs is not valid")
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
        except ValueError:
            response_data = rg.error_response_generator(400, "Malformed JSON")
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
        else:
            # make sure the device data type is correct
            # str for write_key and list for sensor_datas
            if type(d.write_key) is str and type(d.sensor_datas) is list:
                # check the write key
                device_data = db.get_user_device_data(key=d.write_key, key_type="w")
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
                            if type(s.user_sensor_uuid) is str and (type(s.user_sensor_value) is int or type(s.user_sensor_value) is float):
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
                            # Put the data first
                            response = db.put_data(database=RUMAHIOT_GUDANG_DATABASE,
                                                   collection=RUMAHIOT_GUDANG_DEVICE_DATA_COLLECTION, data=j)
                            # Todo : Find a better way to do this (might be slow at scale)
                            # Check the value of each sensor
                            for sensor_data in j['sensor_datas']:
                                # Todo : Check the output and put it in the log
                                # Put device data in the too so it can be used when the threshold criteria met
                                threshold_check_success = gutils.check_sensor_threshold(user_sensor_uuid=sensor_data['user_sensor_uuid'],
                                                                                        sensor_value=sensor_data['user_sensor_value'],
                                                                                        device_data=device_data)

                                if not threshold_check_success:
                                    response_data = rg.error_response_generator(500, "Internal server error")
                                    return HttpResponse(json.dumps(response_data), content_type="application/json",
                                                        status=500)
                            if response != None:
                                response_data = rg.success_response_generator(200, "Device data successfully submitted")
                                return HttpResponse(json.dumps(response_data), content_type="application/json",
                                                    status=200)
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

# Oh boi, this gonna be deep and long - janil realized he ducked up
@csrf_exempt
def store_new_device(request):
    # Gudang Classes
    rg = ResponseGenerator()
    db = GudangMongoDB()
    gutils = GudangUtils()
    requtils = RequestUtils()
    auth = GudangSidikModule()

    if request.method == 'POST':
        try:
            token = requtils.get_access_token(request)
        except KeyError:
            response_data = rg.error_response_generator(401, 'Please define the authorization header')
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=401)
        else:
            if token['token'] != None:
                user = auth.get_user_data(token['token'])
                # Check token validity
                if user['user_uuid'] != None:
                    # Verify the root structure
                    try:
                        j = json.loads(request.body.decode('utf-8'))
                        new_device = NewDeviceResource(**j)
                    except TypeError:
                        response_data = rg.error_response_generator(400, 'One of the request inputs is not valid')
                        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                    except ValueError:
                        response_data = rg.error_response_generator(400, 'Malformed JSON')
                        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                    else:
                        if (gutils.string_length_checker(new_device.location_text, 128) and gutils.string_length_checker(new_device.device_name, 32) and gutils.check_data_sending_interval_value(new_device.device_data_sending_interval)) :
                            # Check device wifi connection
                            user_wifi_connection = db.get_user_wifi_connection_by_uuid(user_uuid=user['user_uuid'], user_wifi_connection_uuid=new_device.user_wifi_connection_uuid)
                            if user_wifi_connection != None:
                                # Verify location structure
                                try:
                                    position = DevicePositionResource(**new_device.position)
                                except TypeError:
                                    response_data = rg.error_response_generator(400, 'One of the request inputs is not valid')
                                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                                except ValueError:
                                    response_data = rg.error_response_generator(400, 'Malformed JSON')
                                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

                                else:
                                    # Make sure lat and lng is float
                                    if gutils.float_int_check(position.lat) and gutils.float_int_check(position.lng):
                                        # Check supported board uuid
                                        supported_board = db.get_supported_board_by_uuid(board_uuid=new_device.supported_board_uuid)
                                        if supported_board != None:
                                            # Check user_sensor structure and validity
                                            # Make the copy for board pin structure checking
                                            supported_board_copy = copy.deepcopy(supported_board)
                                            # total sensor pin ( Do not count NC pin)
                                            sensor_pin_total = 0
                                            for added_sensor in new_device.added_sensors:
                                                try:
                                                    sensor = AddedSensorResource(**added_sensor)
                                                except TypeError:
                                                    response_data = rg.error_response_generator(400, 'One of the request inputs is not valid')
                                                    return HttpResponse(json.dumps(response_data),
                                                                        content_type='application/json', status=400)
                                                except ValueError:
                                                    response_data = rg.error_response_generator(400, 'Malformed JSON')
                                                    return HttpResponse(json.dumps(response_data),
                                                                        content_type='application/json', status=400)
                                                else:
                                                    if (gutils.string_length_checker(sensor.added_sensor_name, 32)) :
                                                        # Check master reference sensor
                                                        master_sensor_reference = db.get_master_sensor_reference_by_uuid(master_sensor_reference_uuid=sensor.master_sensor_reference_uuid)
                                                        if master_sensor_reference != None:
                                                            # Check pin mapping structure ( data validity will be checked in different function)
                                                            for pin_mapping in sensor.sensor_pin_mappings:
                                                                try:
                                                                    pin = SensorPinMappingResource(**pin_mapping)
                                                                except TypeError:
                                                                    response_data = rg.error_response_generator(400, 'One of the request inputs is not valid')
                                                                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                                                                except ValueError:
                                                                    response_data = rg.error_response_generator(400, 'Malformed JSON')
                                                                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                                                                else:
                                                                    # Count total sensor pin ( NC pin should not be count)
                                                                    if pin.device_pin == "NC" and pin.device_pin_name == "NC" and pin.function == "NC":
                                                                        pass
                                                                    else:
                                                                        sensor_pin_total += 1

                                                            # Match the submitted pin configuration with master sensor configuration
                                                            if not gutils.validate_sensor_pin_mapping(
                                                                    added_sensor_pin_mappings=added_sensor['sensor_pin_mappings'],
                                                                    master_sensor_reference_pin_mappings=master_sensor_reference['sensor_pin_mappings']):
                                                                response_data = rg.error_response_generator(400, 'Invalid sensor pin structure')
                                                                return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                                                        else:
                                                            response_data = rg.error_response_generator(400, 'Invalid master sensor reference uuid')
                                                            return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                                                    else:
                                                        response_data = rg.error_response_generator(400, 'Invalid added sensor string length')
                                                        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)


                                                # Validate the pin configuration
                                                if not gutils.validate_board_pin_mapping(added_sensor_pin_mappings=added_sensor['sensor_pin_mappings'],
                                                                                         supported_board_pin_mappings=supported_board_copy['board_pins']):
                                                    response_data = rg.error_response_generator(400, 'Invalid sensor pin structure')
                                                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

                                            # Check if the resulting structure mutation is correct
                                            if (len(supported_board['board_pins']) == len(supported_board_copy['board_pins']) + sensor_pin_total):

                                                # THE DATA THAT ENTER THIS STATE SHOULD BE FULLY VERIFIED AND NORMALIZED
                                                ########################################################################

                                                user_sensor_uuids = []

                                                # For each added sensor
                                                for added_sensor in new_device.added_sensors:
                                                    # Make user_sensor mapping
                                                    new_user_sensor_mapping = {
                                                        'user_sensor_mapping_uuid': uuid4().hex,
                                                        'time_added': float(datetime.now().timestamp()),
                                                        'sensor_pin_mappings': added_sensor['sensor_pin_mappings']
                                                    }

                                                    # Write into db
                                                    db.put_user_sensor_mapping(user_sensor_mapping=new_user_sensor_mapping)

                                                    # Get master sensor reference
                                                    # Threshold defaulting to disabled when new device is added
                                                    master_sensor_reference = db.get_master_sensor_reference_by_uuid(master_sensor_reference_uuid=added_sensor['master_sensor_reference_uuid'])
                                                    for master_sensor_uuid in master_sensor_reference['master_sensor_uuids']:
                                                        master_sensor = db.get_master_sensor_by_uuid(master_sensor_uuid=master_sensor_uuid)
                                                        new_user_sensor = {
                                                            'user_uuid': user['user_uuid'],
                                                            'user_sensor_uuid': uuid4().hex,
                                                            'user_sensor_name': added_sensor['added_sensor_name'],
                                                            'master_sensor_uuid': master_sensor_uuid,
                                                            'sensor_threshold': float(0),
                                                            'currently_over_threshold': False,
                                                            'threshold_direction': '1',
                                                            'threshold_enabled': False,
                                                            'user_sensor_mapping_uuid': new_user_sensor_mapping['user_sensor_mapping_uuid']
                                                        }
                                                        # Write into db
                                                        db.put_user_sensor(user_sensor=new_user_sensor)
                                                        user_sensor_uuids.append(new_user_sensor['user_sensor_uuid'])

                                                # User device structure
                                                user_device = {
                                                    'supported_board_uuid': new_device.supported_board_uuid,
                                                    'user_sensor_uuids': user_sensor_uuids,
                                                    'device_uuid': uuid4().hex,
                                                    'position': {
                                                        'lat': float(position.lat),
                                                        'lng': float(position.lng)
                                                    },
                                                    'location_text': new_device.location_text,
                                                    'read_key': uuid4().hex,
                                                    'time_added': float(datetime.now().timestamp()),
                                                    'user_uuid': user['user_uuid'],
                                                    'write_key': uuid4().hex,
                                                    'device_name': new_device.device_name,
                                                    'user_wifi_connection_uuid': new_device.user_wifi_connection_uuid,
                                                    'device_data_sending_interval': new_device.device_data_sending_interval
                                                }

                                                # Write into db
                                                db.put_user_device(user_device=user_device)

                                                # Device successfully added
                                                response_data = rg.success_response_generator(200, "New device successfully added")
                                                return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)

                                            else:
                                                response_data = rg.error_response_generator(400, 'Invalid board pin structure')
                                                return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                                        else:
                                            response_data = rg.error_response_generator(400, 'Invalid supported board uuid')
                                            return HttpResponse(json.dumps(response_data), content_type='application/json',
                                                                status=400)
                                    else:
                                        response_data = rg.error_response_generator(400, 'Invalid position coordinate data type')
                                        return HttpResponse(json.dumps(response_data), content_type='application/json',
                                                            status=400)
                            else:
                                response_data = rg.error_response_generator(400, 'invalid user wifi connection uuid')
                                return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                        else:
                            response_data = rg.error_response_generator(400, 'Invalid added device string length')
                            return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                else:
                    response_data = rg.error_response_generator(401, user['error'])
                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)
            else:
                response_data = rg.error_response_generator(401, token['error'])
                return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)

    else:
        response_data = rg.error_response_generator(400, 'Bad request method')
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

