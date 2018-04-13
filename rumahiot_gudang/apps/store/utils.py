from rumahiot_gudang.apps.store.mongodb import GudangMongoDB
from rumahiot_gudang.apps.sidik_module.authentication import GudangSidikModule
from datetime import datetime
from rumahiot_gudang.apps.surat_module.send_email import GudangSuratModule
import multiprocessing

class GudangUtils:

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
                                gsurat = GudangSuratModule()
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

                                    # Send the notification email using different process
                                    notification_process = multiprocessing.Process(
                                        target=gsurat.send_device_notification_email_worker,
                                        args=(user_uuid, user_sensor_uuid, device_uuid, user_email, device_name,
                                              user_sensor_name, threshold_value,
                                              latest_value, time_reached, threshold_direction,
                                              unit_symbol, notification_type))
                                    # Start the process
                                    notification_process.start()

                                    # Send android notification
                                    android_notification_process = multiprocessing.Process(target=gsurat.send_device_android_notification_worker,
                                                                                   args=(user_sensor['user_uuid'],device_data['device_uuid'],
                                                                                         user_sensor_name, device_name, user_sensor['user_sensor_uuid'],
                                                                                         '1', time_reached))
                                    android_notification_process.start()
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
                                gsurat = GudangSuratModule()
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

                                    # Send the notification email using different process
                                    notification_process = multiprocessing.Process(
                                        target=gsurat.send_device_notification_email_worker,
                                        args=(user_uuid, user_sensor_uuid, device_uuid, user_email, device_name,
                                              user_sensor_name, threshold_value,
                                              latest_value, time_reached, threshold_direction,
                                              unit_symbol, notification_type))
                                    # Start the process
                                    notification_process.start()

                                    # Send android notification
                                    android_notification_process = multiprocessing.Process(
                                        target=gsurat.send_device_android_notification_worker,
                                        args=(user_sensor['user_uuid'], device_data['device_uuid'],
                                              user_sensor_name, device_name, user_sensor['user_sensor_uuid'],
                                              '0', time_reached))
                                    android_notification_process.start()
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
                                gsurat = GudangSuratModule()
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

                                    # Send the notification email using different process
                                    notification_process = multiprocessing.Process(
                                        target=gsurat.send_device_notification_email_worker,
                                        args=(user_uuid, user_sensor_uuid, device_uuid, user_email, device_name, user_sensor_name, threshold_value,
                                              latest_value, time_reached, threshold_direction,
                                              unit_symbol, notification_type))
                                    # Start the process
                                    notification_process.start()

                                    # Send android notification
                                    android_notification_process = multiprocessing.Process(
                                        target=gsurat.send_device_android_notification_worker,
                                        args=(user_sensor['user_uuid'], device_data['device_uuid'],
                                              user_sensor_name, device_name, user_sensor['user_sensor_uuid'],
                                              '1', time_reached))
                                    android_notification_process.start()
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
                                gsurat = GudangSuratModule()
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

                                    # Send the notification email using different process
                                    notification_process = multiprocessing.Process(
                                        target=gsurat.send_device_notification_email_worker,
                                        args=(user_uuid, user_sensor_uuid, device_uuid, user_email, device_name,
                                              user_sensor_name, threshold_value,
                                              latest_value, time_reached, threshold_direction,
                                              unit_symbol, notification_type))
                                    # Start the process
                                    notification_process.start()

                                    # Send android notification
                                    android_notification_process = multiprocessing.Process(
                                        target=gsurat.send_device_android_notification_worker,
                                        args=(user_sensor['user_uuid'], device_data['device_uuid'],
                                              user_sensor_name, device_name, user_sensor['user_sensor_uuid'],
                                              '0', time_reached))
                                    android_notification_process.start()
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


