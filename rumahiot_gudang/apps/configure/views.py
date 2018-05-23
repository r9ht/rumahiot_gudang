import json

from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt

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
                                        return HttpResponse(json.dumps(response_data), content_type="application/json",
                                                            status=500)
                                    else:
                                        response_data = rg.success_response_generator(200,
                                                                                      "Sensor detail successfully updated")

                                        return HttpResponse(json.dumps(response_data), content_type="application/json",
                                                            status=200)
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