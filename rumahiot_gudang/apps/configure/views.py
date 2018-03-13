from django.shortcuts import render, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rumahiot_gudang.apps.store.utils import RequestUtils,ResponseGenerator,GudangUtils
from rumahiot_gudang.apps.retrieve.authorization import GudangSidikModule
from rumahiot_gudang.apps.store.mongodb import GudangMongoDB
from rumahiot_gudang.apps.configure.forms import UpdateDeviceSensorThresholdForm
import json


# Create your views here.

@csrf_exempt
def update_device_sensor_threshold(request):
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
            response_data = rg.error_response_generator(400, 'Please define the authorization header')
            return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
        else:
            if token['token'] != None:
                user = auth.get_user_data(token['token'])
                if user['user_uuid'] != None:
                    form = UpdateDeviceSensorThresholdForm(request.POST)
                    if form.is_valid():
                        device = db.get_device_by_uuid(device_uuid=form.cleaned_data['device_uuid'])
                        if device['user_uuid'] == user['user_uuid']:
                            sensor_list = device['device_sensors']
                            # For sensor matching
                            target_sensor = None
                            other_sensor = []
                            # Iterate through the sensor list to find the correct one
                            # TODO: Find a better way to do this
                            for sensor in sensor_list:
                                if sensor['sensor_uuid'] == form.cleaned_data['sensor_uuid']:
                                    target_sensor = sensor
                                else:
                                    other_sensor.append(sensor)

                            # Check if the sensor exist
                            if target_sensor != None:
                                # Check new threshold datatype
                                if gutils.float_check(form.cleaned_data['new_threshold']):
                                    # implement the change
                                    target_sensor['sensor_threshold'] = float(form.cleaned_data['new_threshold'])
                                    other_sensor.append(target_sensor)
                                    result = db.update_device_sensor(device['_id'], other_sensor)
                                    # Check the operation result
                                    if result != None:
                                        response_data = rg.success_response_generator(200,"Device sensor threshold successfully updated")
                                        return HttpResponse(json.dumps(response_data), content_type="application/json",status=200)
                                    else:
                                        response_data = rg.error_response_generator(500, "Internal server error")
                                        return HttpResponse(json.dumps(response_data), content_type="application/json",
                                                            status=500)
                                else:
                                    response_data = rg.error_response_generator(400, "Incorrect field type")
                                    return HttpResponse(json.dumps(response_data), content_type="application/json",
                                                        status=400)
                            else:
                                response_data = rg.error_response_generator(400, 'Invalid sensor UUID')
                                return HttpResponse(json.dumps(response_data), content_type='application/json',
                                                    status=400)
                        else:
                            response_data = rg.error_response_generator(400, 'Invalid device UUID')
                            return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                    else:
                        response_data = rg.error_response_generator(400, 'invalid or missing parameter submitted')
                        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

                else:
                    response_data = rg.error_response_generator(400, user['error'])
                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
    else:
        response_data = rg.error_response_generator(400, 'Bad request method')
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)


