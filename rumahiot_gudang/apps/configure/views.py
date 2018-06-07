import json

from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rumahiot_gudang.apps.store.resource import UpdateDeviceDetailResource, DevicePositionResource

from rumahiot_gudang.apps.configure.forms import UpdateUserSensorDetailForm
from rumahiot_gudang.apps.sidik_module.authorization import GudangSidikModule
from rumahiot_gudang.apps.store.mongodb import GudangMongoDB
from rumahiot_gudang.apps.store.utils import RequestUtils, ResponseGenerator, GudangUtils


# Create your views here.

@csrf_exempt
def update_user_sensor_detail(request):
    # Gudang class
    rg = ResponseGenerator()
    requtils = RequestUtils()
    auth = GudangSidikModule()
    db = GudangMongoDB()
    gutils = GudangUtils()

    if request.method == "POST":
        try:
            token = requtils.get_access_token(request)
        except KeyError:
            response_data = rg.error_response_generator(401, 'Please define the authorization header')
            return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)
        else:
            if token['token'] != None:
                user = auth.get_user_data(token['token'])
                if user['user_uuid'] != None:
                    form = UpdateUserSensorDetailForm(request.POST)
                    if form.is_valid():
                        # Normalize the threshold_direction, threshold_enabled, and new_threshold
                        threshold_enabled = True
                        # 1 (Positive) As the default direction if the threshold is disabled
                        threshold_direction = "1"
                        # 0 For default value if the threshold is disabled
                        if form.cleaned_data['threshold_enabled'] == "0":
                            form.cleaned_data['new_threshold'] = 0
                            threshold_enabled = False

                        if gutils.float_check(form.cleaned_data['new_threshold']) :
                            if form.cleaned_data['threshold_enabled'] == "1":
                            # Put the real threshold direction if the threshold is enabled
                                threshold_direction = form.cleaned_data['threshold_direction']

                            user_sensor = db.get_user_sensor_by_uuid(user_sensor_uuid=form.cleaned_data['user_sensor_uuid'])
                            if user_sensor != None:
                                if user_sensor['user_uuid'] == user['user_uuid']:
                                    try:
                                        db.update_user_sensor_detail(object_id=user_sensor['_id'],
                                                                    new_threshold_value=float(form.cleaned_data['new_threshold']),
                                                                    new_user_sensor_name=form.cleaned_data['new_user_sensor_name'],
                                                                    threshold_direction = threshold_direction,
                                                                    threshold_enabled=threshold_enabled
                                                                     )
                                    except:
                                        response_data = rg.error_response_generator(500, "Internal server error")
                                        return HttpResponse(json.dumps(response_data), content_type="application/json", status=500)
                                    else:
                                        response_data = rg.success_response_generator(200,"Sensor detail successfully updated")
                                        return HttpResponse(json.dumps(response_data), content_type="application/json",status=200)
                                else:
                                    # Obfuscate the error for accessing unowned sensor
                                    response_data = rg.error_response_generator(400, 'Invalid user sensor uuid')
                                    return HttpResponse(json.dumps(response_data), content_type='application/json',
                                                        status=400)
                            else:
                                response_data = rg.error_response_generator(400, 'Invalid user sensor uuid')
                                return HttpResponse(json.dumps(response_data), content_type='application/json',
                                                    status=400)
                        else:
                            response_data = rg.error_response_generator(400, 'Invalid threshold value')
                            return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                    else:
                        response_data = rg.error_response_generator(400, 'invalid or missing parameter submitted')
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

@csrf_exempt
def update_device_detail(request):
    # Gudang class
    rg = ResponseGenerator()
    requtils = RequestUtils()
    auth = GudangSidikModule()
    db = GudangMongoDB()
    gutils = GudangUtils()

    if request.method == 'POST':
        # Check the token
        try:
            token = requtils.get_access_token(request)
        except KeyError:
            response_data = rg.error_response_generator(401, 'Please define the authorization header')
            return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)
        else:
            if token['token'] != None:
                # Check token validity
                user = auth.get_user_data(token['token'])
                if user['user_uuid'] != None:
                    try:
                        json_body = json.loads(request.body.decode('utf-8'))
                        new_device_detail = UpdateDeviceDetailResource(**json_body)
                    except TypeError:
                        response_data = rg.error_response_generator(400, "One of the request inputs is not valid")
                        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
                    except ValueError:
                        response_data = rg.error_response_generator(400, "Malformed JSON")
                        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
                    else:
                        try :
                            # Verify location value exist
                            position = (DevicePositionResource(**new_device_detail.position))
                        except TypeError:
                            response_data = rg.error_response_generator(400, "One of the request inputs is not valid")
                            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
                        except ValueError:
                            response_data = rg.error_response_generator(400, "Malformed JSON")
                            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
                        else:
                            # Check for the datatype
                            if gutils.string_length_checker(new_device_detail.device_uuid, 32) and gutils.string_length_checker(new_device_detail.device_name, 32) and type(new_device_detail.user_wifi_connection_uuid) is str and type(new_device_detail.device_name) is str and type(new_device_detail.device_uuid) is str and gutils.float_int_check(position.lat) and gutils.float_int_check(position.lng):
                                # check user_wifi_connection_uuid
                                wifi_connection = db.get_user_wifi_connection_by_uuid(user_uuid=user['user_uuid'], user_wifi_connection_uuid=new_device_detail.user_wifi_connection_uuid)
                                if(wifi_connection) :
                                    db.update_device_detail(device_uuid=new_device_detail.device_uuid, device_name=new_device_detail.device_name, position=new_device_detail.position, user_wifi_connection_uuid=new_device_detail.user_wifi_connection_uuid)
                                    # Device successfully added
                                    response_data = rg.success_response_generator(200, 'Device detail successfully updated')
                                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=200)

                                else:
                                    response_data = rg.error_response_generator(400, 'Invalid wifi connection uuid')
                                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                            else:
                                response_data = rg.error_response_generator(400, 'Invalid request data type')
                                return HttpResponse(json.dumps(response_data), content_type='application/json',status=400)
                else:
                    response_data = rg.error_response_generator(401, user['error'])
                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)

            else:
                response_data = rg.error_response_generator(401, token['error'])
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=401)
    else:
        response_data = rg.error_response_generator(400, 'Bad request method')
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)



def remove_user_device(request, device_uuid):
    # Gudang class
    rg = ResponseGenerator()
    requtils = RequestUtils()
    auth = GudangSidikModule()
    db = GudangMongoDB()
    gutils = GudangUtils()

    if request.method == 'GET':
        # Check the token
        try:
            token = requtils.get_access_token(request)
        except KeyError:
            response_data = rg.error_response_generator(401, 'Please define the authorization header')
            return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)
        else:
            if token['token'] != None:
                user = auth.get_user_data(token['token'])
                # Check token validity
                if user['user_uuid'] != None:
                    device = db.get_device_data_by_uuid(user_uuid=user['user_uuid'], device_uuid=device_uuid)
                    if (device):
                        # Remove the device
                        db.remove_user_device(device_uuid=device_uuid)
                        response_data = rg.success_response_generator(200, 'Device successfully removed')
                        return HttpResponse(json.dumps(response_data), content_type='application/json', status=200)
                    else:
                        response_data = rg.error_response_generator(400, 'Invalid device uuid')
                        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                else:
                    response_data = rg.error_response_generator(401, user['error'])
                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)
            else:
                response_data = rg.error_response_generator(401, token['error'])
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=401)
    else:
        response_data = rg.error_response_generator(400, 'Bad request method')
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)