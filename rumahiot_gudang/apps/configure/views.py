import json

from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rumahiot_gudang.apps.store.resource import UpdateDeviceDetailResource, DevicePositionResource, UpdateSupportedBoardResource, NewSupportedBoardPinResource

from rumahiot_gudang.apps.configure.forms import UpdateUserSensorDetailForm
from rumahiot_gudang.apps.store.mongodb import GudangMongoDB
from rumahiot_gudang.apps.store.utils import ResponseGenerator, GudangUtils
from rumahiot_gudang.apps.sidik_module.decorator import get_method_required, authentication_required, post_method_required, admin_authentication_required


# Create your views here.

@csrf_exempt
@post_method_required
@authentication_required
def update_user_sensor_detail(request, user):

    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()
    gutils = GudangUtils()

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

        if gutils.float_check(form.cleaned_data['new_threshold']):
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
                                                     threshold_direction=threshold_direction,
                                                     threshold_enabled=threshold_enabled
                                                     )
                    except:
                        response_data = rg.error_response_generator(500, "Internal server error")
                        return HttpResponse(json.dumps(response_data), content_type="application/json", status=500)
                    else:
                        response_data = rg.success_response_generator(200, "Sensor detail successfully updated")
                        return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)
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

@csrf_exempt
@post_method_required
@authentication_required
def update_device_detail(request, user):
    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()
    gutils = GudangUtils()

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
        try:
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
            if gutils.string_length_checker(new_device_detail.device_uuid, 32) and gutils.string_length_checker(new_device_detail.device_name, 32) and type(
                    new_device_detail.user_wifi_connection_uuid) is str and type(new_device_detail.device_name) is str and type(new_device_detail.device_uuid) is str and gutils.float_int_check(
                    position.lat) and gutils.float_int_check(position.lng) and type(new_device_detail.location_text) is str and gutils.float_int_check(new_device_detail.device_data_sending_interval):
                # check user_wifi_connection_uuid
                if (new_device_detail.device_data_sending_interval <= 1440 and new_device_detail.device_data_sending_interval >= 5):
                    wifi_connection = db.get_user_wifi_connection_by_uuid(user_uuid=user['user_uuid'], user_wifi_connection_uuid=new_device_detail.user_wifi_connection_uuid)
                    if (wifi_connection):
                        db.update_device_detail(device_uuid=new_device_detail.device_uuid, device_name=new_device_detail.device_name, position=new_device_detail.position,
                                                user_wifi_connection_uuid=new_device_detail.user_wifi_connection_uuid, location_text=new_device_detail.location_text,
                                                device_data_sending_interval=new_device_detail.device_data_sending_interval)
                        # Device successfully added
                        response_data = rg.success_response_generator(200, 'Device detail successfully updated')
                        return HttpResponse(json.dumps(response_data), content_type='application/json', status=200)
                    else:
                        response_data = rg.error_response_generator(400, 'Invalid wifi connection uuid')
                        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
                else:
                    response_data = rg.error_response_generator(400, 'Invalid device data sending interval')
                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
            else:
                response_data = rg.error_response_generator(400, 'Invalid request data type')
                return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

@get_method_required
@authentication_required
def remove_user_device(request, user, device_uuid):

    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()

    device = db.get_device_data_by_uuid(user_uuid=user['user_uuid'], device_uuid=device_uuid)
    if (device):
        # Remove the device
        db.remove_user_device(device_uuid=device_uuid)
        response_data = rg.success_response_generator(200, 'Device successfully removed')
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=200)
    else:
        response_data = rg.error_response_generator(400, 'Invalid device uuid')
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)


@get_method_required
@admin_authentication_required
def remove_supported_board(request, user, board_uuid):

    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()

    # Check if the board being used by a device
    device = db.get_device_by_board_uuid(board_uuid=board_uuid)

    if device.count(True) == 0:
        # Check the board
        board = db.get_supported_board_by_uuid(board_uuid=board_uuid)
        if (board) :
            db.remove_supported_board(board_uuid=board_uuid)
            response_data = rg.success_response_generator(200, 'Board successfully removed')
            return HttpResponse(json.dumps(response_data), content_type='application/json', status=200)
        else:
            response_data = rg.error_response_generator(400, 'Invalid board uuid')
            return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
    else:
        response_data = rg.error_response_generator(400, 'Board being used by one or more user device')
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

@csrf_exempt
@post_method_required
@admin_authentication_required
def update_supported_board(request, user):

    # Gudang Classes
    rg = ResponseGenerator()
    db = GudangMongoDB()

    try:
        # Verify JSON structure
        j = json.loads(request.body.decode('utf-8'))

    except TypeError:
        response_data = rg.error_response_generator(400, "One of the request inputs is not valid")
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
    except ValueError:
        response_data = rg.error_response_generator(400, "Malformed JSON")
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
    else:

        # Verify the data format for added board
        try:
            updated_board = UpdateSupportedBoardResource(**j)
        except TypeError:
            response_data = rg.error_response_generator(400, "One of the request inputs is not valid")
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
        except ValueError:
            response_data = rg.error_response_generator(400, "Malformed JSON")
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
        else:
            # Make sure the board exist
            board = db.get_supported_board_by_uuid(board_uuid=updated_board.board_uuid)
            if(board):
                # Verify the sensor pin configuration
                for board_pin in updated_board.board_pins:
                    try:
                        pin = NewSupportedBoardPinResource(**board_pin)
                    except TypeError:
                        response_data = rg.error_response_generator(400, "One of the request inputs is not valid")
                        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
                    except ValueError:
                        response_data = rg.error_response_generator(400, "Malformed JSON")
                        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

                # All data successfully verified in this step
                # Put new board in db
                db.update_supported_board(board_uuid=updated_board.board_uuid, board_name=updated_board.board_name, chip=updated_board.chip, manufacturer=updated_board.manufacturer,
                                           board_specification=updated_board.board_specification, board_image=updated_board.board_image,
                                           board_image_source=updated_board.board_image_source, board_pins=updated_board.board_pins, s3_path=updated_board.s3_path,
                                           version=updated_board.version)

                response_data = rg.success_response_generator(200, "Board configuration successfully updated")
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)
            else:
                response_data = rg.error_response_generator(400, "Invalid board UUID")
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)


