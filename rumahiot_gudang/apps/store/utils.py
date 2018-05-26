from rumahiot_gudang.apps.store.mongodb import GudangMongoDB
from rumahiot_gudang.apps.sidik_module.authentication import GudangSidikModule
from datetime import datetime
import random
from rumahiot_gudang.apps.surat_module.send_email import send_device_android_notification_worker, send_device_notification_email_worker
from pytz import all_timezones, timezone

import multiprocessing

class GudangUtils:

    # Convert datetime object into specified timezone
    def datetime_timezone_converter(self, datetimeobject, time_zone):
        if time_zone in all_timezones:
            return datetimeobject.astimezone(timezone(time_zone))
        else:
            return None
    # Get n random material color in list format
    def get_n_random_material_color(self, n):
        db = GudangMongoDB()
        color_list = []
        db_color = db.get_material_color_document()
        # Pop the object id
        db_color.pop('_id')
        db_color_list = list(db_color.values())

        for i in range(0, n):
            rand_int = random.randint(0, len(db_color_list)-1)
            color_list.append(db_color_list[rand_int])

        return color_list

    # Check if submitted string length matched the submitted value
    # Return : boolean
    def string_length_checker(self, target_string, length):
        if len(target_string) <= length :
            return True
        else:
            return False

    # Check for device_data_sending_interval value
    # Todo : Check the interval from db instead of hardcoded it in
    def check_data_sending_interval_value(self, interval):
        if type(interval) is int:
            if (interval <= 1440 and interval >= 5):
                return True
            else:
                return False
        else:
            return False

    # Check if value type is int or float
    def float_int_check(self, value):
        if type(value) == float or type(value) == int:
            return True
        else:
            return False

    # Check if string contain integer and it is over 0
    def integer_check(self, value_in_string):
        try:
            int(value_in_string)
        except ValueError:
            return False
        else:
            if int(value_in_string) < 0:
                return False
            else:
                return True

    # Check if string contain float
    def float_check(self, value_in_string):
        try:
            float(value_in_string)
        except ValueError:
            return False
        else:
            return True

    # Check if input data is a correct value between 1-12 (valid month)
    def month_check(self, month):
        try:
            int(month)
        except ValueError:
            return False
        else:
            if int(month) > 0 and int(month) < 13:
                return True
            else:
                return False

    # check if input year is a correct value above 0
    def year_check(self, year):
        try:
            int(year)
        except ValueError:
            return False
        else:
            if int(year) > 0 :
                return True
            else:
                return False

    # Check current sensor value against the threshold and  current_above_threshold status
    # Logic :
    # If the threshold is enabled
    #  if threshold_dircetion == "1:
    #   - if the sensor value is higher than threshold then :
    #        > if the currently_over_threshold is True then :
    #             >> log the information (no notification)
    #        > else:
    #             >> log the information
    #             >> send notification (Android & email) -> Value above threshold
    #           >> set currently_over_threshold to True
    #   - else:
    #         > if the currently_over_threshold is True then :
    #             >> log the detail
    #             >> send notification (android & email) -> value is normal again
    #             >> set currently_over_threshold to false
    #        > else
    #            >> the information doesnt need to be logged (no notification)
    #  elif threshold_dircetion == "-1:
    #   - if the sensor value is lower than threshold then :
    #        > if the currently_over_threshold is True then :
    #             >> log the information (no notification)
    #        > else:
    #             >> log the information
    #             >> send notification (Android & email) -> Value above threshold
    #             >> set currently_over_threshold to True
    #   - else:
    #         > if the currently_above_threshold is True then :
    #             >> log the detail
    #             >> send notification (android & email) -> value is normal again
    #             >> set currently_over_threshold to false
    #        > else
    #            >> the information doesnt need to be logged (no notification)
    # Else: return true (There is no need to check the threshold)
    # Return value : True if the operation succeed, False if the operation failed
    def check_sensor_threshold(self, user_sensor_uuid, sensor_value, device_data):
        db = GudangMongoDB()
        try:
            user_sensor = db.get_user_sensor_by_uuid(user_sensor_uuid=user_sensor_uuid)
            master_sensor = db.get_master_sensor_by_uuid(master_sensor_uuid=user_sensor['master_sensor_uuid'])
        except:
            # For unknown error
            return False
        else:
            # Only Execute when the threshold is set
            smodule = GudangSidikModule()
            if user_sensor['threshold_enabled'] :
                if user_sensor['threshold_direction'] == "1" :
                    # Todo : Make a logger for the value
                    # Compare the value to the threshold
                    if sensor_value > user_sensor['sensor_threshold']:
                        # Check the current status
                        if user_sensor['currently_over_threshold']:
                            # Log the status
                            return True
                        else:
                            # Log the status, send the notification, and modify currently_above_threshold
                            # When the value is over threshold
                            try:
                                db.update_currently_over_threshold(object_id=user_sensor['_id'], new_status=True)
                            except:
                                # For unknown error
                                return False
                            else:
                                # Get user detail (to get the email address)
                                user = smodule.get_email_address(user_uuid=user_sensor['user_uuid'])
                                # Get the master sensor (For unit & symbol)
                                master_sensor = db.get_master_sensor_by_uuid(master_sensor_uuid=user_sensor['master_sensor_uuid'])
                                if user.status_code == 200:
                                    # Prepare the request data
                                    user_email = user.json()['data']['email']
                                    device_name = device_data['device_name']
                                    user_sensor_name = user_sensor['user_sensor_name']
                                    threshold_value = user_sensor['sensor_threshold']
                                    latest_value = sensor_value
                                    time_reached = datetime.now().timestamp()
                                    threshold_direction = user_sensor['threshold_direction']
                                    unit_symbol = master_sensor['master_sensor_default_unit_symbol']
                                    notification_type = "0"
                                    # Required parameter for logger
                                    user_uuid = user.json()['data']['user_uuid']
                                    user_sensor_uuid = user_sensor['user_sensor_uuid']
                                    device_uuid = device_data['device_uuid']

                                    # Send using different lambda execution env.
                                    send_device_notification_email_worker(user_uuid=user_uuid, user_sensor_uuid=user_sensor_uuid, device_uuid=device_uuid, email=user_email, device_name=device_name,
                                                                                 user_sensor_name=user_sensor_name, threshold_value=threshold_value, latest_value=latest_value,
                                                                                 time_reached=time_reached, threshold_direction=threshold_direction, unit_symbol=unit_symbol,
                                                                                 notification_type=notification_type)
                                    # Send using different lambda execution env.
                                    send_device_android_notification_worker(user_uuid=user_uuid, device_uuid=device_uuid, user_sensor_name=user_sensor_name, device_name=device_name,
                                                                                   user_sensor_uuid=user_sensor_uuid, status='1', time_reached=time_reached)


                                    return True

                                else:
                                    return False
                    else:
                        # Check the current status
                        # When the value is return back to normal
                        if user_sensor['currently_over_threshold']:
                            # Log the status, send the notification, and modify currently_above_threshold
                            try:
                                db.update_currently_over_threshold(object_id=user_sensor['_id'], new_status=False)
                            except:
                                # For unknown error
                                return False
                            else:
                                # Get user detail (to get the email address)
                                user = smodule.get_email_address(user_uuid=user_sensor['user_uuid'])
                                # Get the master sensor (For unit & symbol)
                                master_sensor = db.get_master_sensor_by_uuid(
                                    master_sensor_uuid=user_sensor['master_sensor_uuid'])
                                if user.status_code == 200:
                                    # Prepare the request data
                                    user_email = user.json()['data']['email']
                                    device_name = device_data['device_name']
                                    user_sensor_name = user_sensor['user_sensor_name']
                                    threshold_value = user_sensor['sensor_threshold']
                                    latest_value = sensor_value
                                    time_reached = datetime.now().timestamp()
                                    threshold_direction = user_sensor['threshold_direction']
                                    unit_symbol = master_sensor['master_sensor_default_unit_symbol']
                                    notification_type = "1"

                                    # Required parameter for logger
                                    user_uuid = user.json()['data']['user_uuid']
                                    user_sensor_uuid = user_sensor['user_sensor_uuid']
                                    device_uuid = device_data['device_uuid']

                                    # Send using different lambda execution env.
                                    send_device_notification_email_worker(user_uuid=user_uuid,
                                                                          user_sensor_uuid=user_sensor_uuid,
                                                                          device_uuid=device_uuid, email=user_email,
                                                                          device_name=device_name,
                                                                          user_sensor_name=user_sensor_name,
                                                                          threshold_value=threshold_value,
                                                                          latest_value=latest_value,
                                                                          time_reached=time_reached,
                                                                          threshold_direction=threshold_direction,
                                                                          unit_symbol=unit_symbol,
                                                                          notification_type=notification_type)

                                    # Send using different lambda execution env.
                                    send_device_android_notification_worker(user_uuid=user_uuid,
                                                                                   device_uuid=device_uuid,
                                                                                   user_sensor_name=user_sensor_name,
                                                                                   device_name=device_name,
                                                                                   user_sensor_uuid=user_sensor_uuid,
                                                                                   status='0',
                                                                                   time_reached=time_reached)

                                    return True


                                else:
                                    return False
                        else:
                            # Status Wont be logged
                            return True
                elif user_sensor['threshold_direction'] == "-1":
                    # Todo : Make a logger for the value
                    # Compare the value to the threshold
                    if sensor_value < user_sensor['sensor_threshold']:
                        # Check the current status
                        if user_sensor['currently_over_threshold']:
                            # Log the status
                            return True
                        else:
                            # When the value is over the threshold
                            # Log the status, send the notification, and modify currently_above_threshold
                            try:
                                db.update_currently_over_threshold(object_id=user_sensor['_id'], new_status=True)
                            except:
                                # For unknown error
                                return False
                            else:
                                # Get user detail (to get the email address)
                                user = smodule.get_email_address(user_uuid=user_sensor['user_uuid'])
                                # Get the master sensor (For unit & symbol)
                                master_sensor = db.get_master_sensor_by_uuid(
                                    master_sensor_uuid=user_sensor['master_sensor_uuid'])
                                if user.status_code == 200:
                                    # Prepare the request data
                                    user_email = user.json()['data']['email']
                                    device_name = device_data['device_name']
                                    user_sensor_name = user_sensor['user_sensor_name']
                                    threshold_value = user_sensor['sensor_threshold']
                                    latest_value = sensor_value
                                    time_reached = datetime.now().timestamp()
                                    threshold_direction = user_sensor['threshold_direction']
                                    unit_symbol = master_sensor['master_sensor_default_unit_symbol']
                                    notification_type = "0"

                                    # Required parameter for logger
                                    user_uuid = user.json()['data']['user_uuid']
                                    user_sensor_uuid = user_sensor['user_sensor_uuid']
                                    device_uuid = device_data['device_uuid']

                                    # Send using different lambda execution env.
                                    send_device_notification_email_worker(user_uuid=user_uuid,
                                                                          user_sensor_uuid=user_sensor_uuid,
                                                                          device_uuid=device_uuid, email=user_email,
                                                                          device_name=device_name,
                                                                          user_sensor_name=user_sensor_name,
                                                                          threshold_value=threshold_value,
                                                                          latest_value=latest_value,
                                                                          time_reached=time_reached,
                                                                          threshold_direction=threshold_direction,
                                                                          unit_symbol=unit_symbol,
                                                                          notification_type=notification_type)

                                    # Send using different lambda execution env.
                                    send_device_android_notification_worker(user_uuid=user_uuid,
                                                                                   device_uuid=device_uuid,
                                                                                   user_sensor_name=user_sensor_name,
                                                                                   device_name=device_name,
                                                                                   user_sensor_uuid=user_sensor_uuid,
                                                                                   status='1',
                                                                                   time_reached=time_reached)

                                    return True

                                else:
                                    return False
                    else:
                        # Check the current status
                        if user_sensor['currently_over_threshold']:
                            # Log the status, send the notification, and modify currently_above_threshold
                            try:
                                db.update_currently_over_threshold(object_id=user_sensor['_id'], new_status=False)
                            except:
                                # For unknown error
                                return False
                            else:
                                # Get user detail (to get the email address)
                                user = smodule.get_email_address(user_uuid=user_sensor['user_uuid'])
                                # Get the master sensor (For unit & symbol)
                                master_sensor = db.get_master_sensor_by_uuid(
                                    master_sensor_uuid=user_sensor['master_sensor_uuid'])
                                if user.status_code == 200:
                                    # Prepare the request data
                                    user_email = user.json()['data']['email']
                                    device_name = device_data['device_name']
                                    user_sensor_name = user_sensor['user_sensor_name']
                                    threshold_value = user_sensor['sensor_threshold']
                                    latest_value = sensor_value
                                    time_reached = datetime.now().timestamp()
                                    threshold_direction = user_sensor['threshold_direction']
                                    unit_symbol = master_sensor['master_sensor_default_unit_symbol']
                                    notification_type = "1"

                                    # Required parameter for logger
                                    user_uuid = user.json()['data']['user_uuid']
                                    user_sensor_uuid = user_sensor['user_sensor_uuid']
                                    device_uuid = device_data['device_uuid']

                                    # Send using different lambda execution env.
                                    send_device_notification_email_worker(user_uuid=user_uuid,
                                                                          user_sensor_uuid=user_sensor_uuid,
                                                                          device_uuid=device_uuid, email=user_email,
                                                                          device_name=device_name,
                                                                          user_sensor_name=user_sensor_name,
                                                                          threshold_value=threshold_value,
                                                                          latest_value=latest_value,
                                                                          time_reached=time_reached,
                                                                          threshold_direction=threshold_direction,
                                                                          unit_symbol=unit_symbol,
                                                                          notification_type=notification_type)

                                    # Send using different lambda execution env.
                                    send_device_android_notification_worker(user_uuid=user_uuid,
                                                                                   device_uuid=device_uuid,
                                                                                   user_sensor_name=user_sensor_name,
                                                                                   device_name=device_name,
                                                                                   user_sensor_uuid=user_sensor_uuid,
                                                                                   status='0',
                                                                                   time_reached=time_reached)

                                    return True


                                else:
                                    return False
                        else:
                            # Status Wont be logged
                            return True
                else:
                    return False
            else:
                # If threshold is disabled
                return True

    def validate_sensor_pin_mapping(self, added_sensor_pin_mappings, master_sensor_reference_pin_mappings):
        # Make sure the submitted data has the same length with master_sensor from db
        if len(master_sensor_reference_pin_mappings) == len(added_sensor_pin_mappings):
            master_sensor_pin_mappings_copy = master_sensor_reference_pin_mappings[:]
            for sensor_pin_mapping in added_sensor_pin_mappings:
                i = 0
                while(i < len(master_sensor_pin_mappings_copy)):
                    e = master_sensor_pin_mappings_copy[i]
                    # Check the sensor_pin and function for each pin
                    if sensor_pin_mapping['sensor_pin'] == e['pin'] and sensor_pin_mapping['function'] in e['function']:
                        try:
                            master_sensor_pin_mappings_copy.remove(e)
                        except:
                            return False
                        else:
                            pass
                    else:
                        i += 1
            if len(master_sensor_pin_mappings_copy) == 0:
                return True
            else:
                return False
        else:
            return False

    def validate_board_pin_mapping(self, added_sensor_pin_mappings, supported_board_pin_mappings):
        # Make sure submitted pin structure supported by the board
        # Take note that the supported_board_pin_mapping should be a pointer and the value should not reinitiated for each user_sensor
        if len(added_sensor_pin_mappings) < len(supported_board_pin_mappings):
            for sensor_pin_mapping in added_sensor_pin_mappings:
                i = 0
                while (i < len(supported_board_pin_mappings)):
                    e = supported_board_pin_mappings[i]
                    if sensor_pin_mapping['device_pin_name'] == e['name'] and sensor_pin_mapping['device_pin'] == e['pin'] and sensor_pin_mapping['device_arduino_pin'] == e['arduino_pin'] and sensor_pin_mapping['function'] in e['functions']:
                        try :
                            supported_board_pin_mappings.remove(e)
                        except:
                            return False
                        else:
                            pass
                    else:
                        i += 1
            return True
        else:
            return False

class ResponseGenerator:
    # generate error response in dict format
    def error_response_generator(self, code, message):
        response = {
            "error": {
                "code": code,
                "message": message
            }
        }
        return response

    # generate data response in dict format
    # input parameter data(dict)
    def data_response_generator(self, data):
        response = {
            "data": data
        }
        return response

    # generate error response in dict format
    def success_response_generator(self, code, message):
        response = {
            "success": {
                "code": code,
                "message": message
            }
        }
        return response

class RequestUtils:
    # get access token from authorization header
    # input parameter : request(request)
    # return :  data['token'] = token, when the header format is correct (string)
    #           data['error'] = None, when the header format is correct
    #           data['token'] = None, when the header format is incorrect
    #           data['error'] = Error, when the header format is incorrect(string)
    # data = {
    #     'token' : token(string),
    #     'error' : error(string)
    # }
    def get_access_token(self, request):
        data = {}
        auth_header = request.META['HTTP_AUTHORIZATION'].split()
        # verify the authorization header length (including authorization type, currently using bearer)
        if len(auth_header) != 2:
            data['token'] = None
            data['error'] = 'Invalid authorization header length'
            return data
        else:
            # check for the type
            if auth_header[0].lower() != 'bearer':
                data['token'] = None
                data['error'] = 'Invalid authorization token method'
                return data
            else:
                data['token'] = auth_header[1]
                data['error'] = None
                return data


