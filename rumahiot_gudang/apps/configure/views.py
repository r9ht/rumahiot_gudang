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
                        if gutils.float_check(form.cleaned_data['new_threshold']) :
                            user_sensor = db.get_user_sensor_by_uuid(user_sensor_uuid=form.cleaned_data['user_sensor_uuid'])
                            if user_sensor != None:
                                if user_sensor['user_uuid'] == user['user_uuid']:
                                    try:
                                        db.update_user_sensor_threshold(object_id=user_sensor['_id'], new_threshold_value=float(form.cleaned_data['new_threshold']))
                                    except:
                                        response_data = rg.error_response_generator(500, "Internal server error")
                                        return HttpResponse(json.dumps(response_data), content_type="application/json",
                                                            status=500)
                                    else:
                                        response_data = rg.success_response_generator(200,"Sensor threshold successfully updated")
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
                    response_data = rg.error_response_generator(400, user['error'])
                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
    else:
        response_data = rg.error_response_generator(400, 'Bad request method')
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)


