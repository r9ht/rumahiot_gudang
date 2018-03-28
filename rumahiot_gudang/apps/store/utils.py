from rumahiot_gudang.apps.store.mongodb import GudangMongoDB

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

    # Check current sensor value against the threshold and  current_above_threshold status
    # Logic :
    # - if the sensor value is higher than threshold then :
    #     > if the currently_above_threshold is True then :
    #         >> log the information (no notification)
    #     > else:
    #         >> log the information
    #         >> send notification (Android & email) -> Value above threshold
    #         >> set currently_above_threshold to True
    # - else:
    #     > if the currently_above_threshold is True then :
    #         >> log the detail
    #         >> send notification (android & email) -> value is normal again
    #         >> set currently_above_threshold to false
    #     > else
    #         >> the information doesnt need to be logged (no notification)
    # Return value : True if the operation succeed, False if the operation failed
    def check_sensor_threshold(self, user_sensor_uuid, sensor_value):
        db = GudangMongoDB()
        try:
            user_sensor = db.get_user_sensor_by_uuid(user_sensor_uuid=user_sensor_uuid)
            master_sensor = db.get_master_sensor_by_uuid(master_sensor_uuid=user_sensor['master_sensor_uuid'])
        except:
            # For unknown error
            return False
        else:
            # Only Execute when the threshold is set
            if user_sensor['threshold_enabled'] :
                if user_sensor['threshold_direction'] == "1" :
                    # Todo : Make a logger for the value
                    # Todo : Create a reusable fucntion for logging and sensing notificatio
                    # Compare the value to the threshold
                    if sensor_value > user_sensor['sensor_threshold']:
                        # Check the current status
                        if user_sensor['currently_over_threshold']:
                            # Log the status
                            print('logged')
                            return True
                        else:
                            # Log the status, send the notification, and modify currently_above_threshold
                            try:
                                db.update_currently_over_threshold(object_id=user_sensor['_id'], new_status=True)
                            except:
                                # For unknown error
                                return False
                            else:
                                print('logged, email sent. current status changed')
                                print('Sensor x exceeding value set')
                                return True
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
                                print('logged, email sent. current status changed')
                                print('Sensor x Back to normal')
                                return True
                        else:
                            # Status Wont be logged
                            print('not logged')
                            return True
                elif user_sensor['threshold_direction'] == "-1":
                    # Todo : Make a logger for the value
                    # Todo : Create a reusable fucntion for logging and sensing notificatio
                    # Compare the value to the threshold
                    if sensor_value < user_sensor['sensor_threshold']:
                        # Check the current status
                        if user_sensor['currently_over_threshold']:
                            # Log the status
                            print('logged')
                            return True
                        else:
                            # Log the status, send the notification, and modify currently_above_threshold
                            try:
                                db.update_currently_over_threshold(object_id=user_sensor['_id'], new_status=True)
                            except:
                                # For unknown error
                                return False
                            else:
                                print('logged, email sent. current status changed')
                                print('Sensor x exceeding value set')
                                return True
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
                                print('logged, email sent. current status changed')
                                print('Sensor x Back to normal')
                                return True
                        else:
                            # Status Wont be logged
                            print('not logged')
                            return True

            else:
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
