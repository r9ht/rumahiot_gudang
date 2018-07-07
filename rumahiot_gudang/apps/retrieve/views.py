import json
import datetime
import timeit
from uuid import uuid4
from pytz import all_timezones

from django.shortcuts import HttpResponse

from rumahiot_gudang.apps.sidik_module.authorization import GudangSidikModule
from rumahiot_gudang.apps.store.mongodb import GudangMongoDB
from rumahiot_gudang.apps.store.utils import RequestUtils, ResponseGenerator, GudangUtils
from rumahiot_gudang.apps.retrieve.template_master import GudangTemplateMaster
from rumahiot_gudang.apps.sidik_module.decorator import get_method_required, authentication_required, admin_authentication_required

from calendar import monthrange


# Create your views here.

# Retrieve timezone list
@get_method_required
@authentication_required
def retrieve_timezone_list(request, user):
    # Gudang class
    rg = ResponseGenerator()
    requtils = RequestUtils()
    auth = GudangSidikModule()

    data = {
        'all_timezones': all_timezones
    }
    # return response object
    response_data = rg.data_response_generator(data)
    return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)

# Retrieve specified device information
@get_method_required
@authentication_required
def retrieve_device_detail(request, user, device_uuid):

    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()

    device = db.get_device_by_uuid(device_uuid=device_uuid)
    if (device):
        if device['user_uuid'] == user['user_uuid']:
            device_connection = db.get_user_wifi_connection_by_uuid(user_wifi_connection_uuid=device['user_wifi_connection_uuid'], user_uuid=user['user_uuid'])
            device_connection.pop('_id')
            device.pop('_id')
            # Add connection detail
            device['device_wifi_connection'] = device_connection
            data = device
            # return response object
            response_data = rg.data_response_generator(data)
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)
        else:
            response_data = rg.error_response_generator(400, 'Invalid device uuid')
            return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
    else:
        response_data = rg.error_response_generator(400, 'Invalid device uuid')
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

# Retrieve board pin mapping for specified sensor
# Using get because we need url parameter
@get_method_required
@authentication_required
def retrieve_board_pin_options(request, user):
    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()

    if request.method == 'GET':
        supported_board_uuid = request.GET.get('board_uuid', '')
        master_sensor_reference_uuid = request.GET.get('sensor_uuid', '')
        # Make sure both parameter exist and contain value
        if supported_board_uuid != '' and supported_board_uuid and master_sensor_reference_uuid != '' and master_sensor_reference_uuid:
            board = db.get_supported_board_by_uuid(board_uuid=supported_board_uuid)
            if board != None:
                sensor = db.get_master_sensor_reference_by_uuid(master_sensor_reference_uuid=master_sensor_reference_uuid)
                if sensor != None:
                    # Main payload for the response
                    data = {
                        'supported_board_uuid': supported_board_uuid,
                        'master_sensor_reference_uuid': master_sensor_reference_uuid,
                        'random_uuid': uuid4().hex,
                        'pin_mapping': []
                    }

                    # Iterate through the pin
                    for sensor_pin_mapping in sensor['sensor_pin_mappings']:
                        pin_option = {
                            'sensor_pin': sensor_pin_mapping['pin'],
                            'sensor_pin_name': sensor_pin_mapping['pin_name'],
                            'mapping_options': []
                        }
                        # Iterate through the function
                        for function in sensor_pin_mapping['function']:
                            # Iterate through board pin mapping
                            if function == 'NC':
                                mapping_option = {
                                    'sensor_pin': sensor_pin_mapping['pin'],
                                    'device_pin': 'NC',
                                    'device_arduino_pin': 'NC',
                                    'device_pin_name': 'NC',
                                    'function': function
                                }
                                # Append it into mapping option
                                pin_option['mapping_options'].append(mapping_option)
                            else:
                                for board_pin in board['board_pins']:
                                    if function in board_pin['functions']:
                                        # Redundant sensor_pin parameter so it can be used easier by front end
                                        mapping_option = {
                                            'sensor_pin': sensor_pin_mapping['pin'],
                                            'device_pin': board_pin['pin'],
                                            'device_arduino_pin': board_pin['arduino_pin'],
                                            'device_pin_name': board_pin['name'],
                                            'function': function
                                        }
                                        # Append it into mapping option
                                        pin_option['mapping_options'].append(mapping_option)
                        # Append it into pin mapping
                        data['pin_mapping'].append(pin_option)
                    response_data = rg.data_response_generator(data)
                    return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)

                else:
                    response_data = rg.error_response_generator(400, "Invalid master sensor reference uuid")
                    return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
            else:
                response_data = rg.error_response_generator(400, "Invalid supported board uuid")
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
        else:
            response_data = rg.error_response_generator(400, 'Invalid get parameter value')
            return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

    else:
        response_data = rg.error_response_generator(400, 'Bad request method')
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

# Retrieve corresponding user device list
# Using GET because we need url parameter
@get_method_required
@authentication_required
def retrieve_device_list(request, user):
    # Init time
    start_time = timeit.default_timer()

    # Gudang class
    rg = ResponseGenerator()
    requtils = RequestUtils()
    auth = GudangSidikModule()
    db = GudangMongoDB()
    gutils = GudangUtils()

    # Const for quick status
    status_good = "All good"
    # if one or more sensor is above the threshold
    status_warning = "{} Over Threshold"

    # Page number
    page = request.GET.get('p', '1')
    # its ok for query to be empty
    query = request.GET.get('q', '')
    # Per page limit
    limit = request.GET.get('l', '10')
    # Order method , the data sorted in ascending order by default
    s_order = request.GET.get('o', 'asc')
    # normalize the order value
    if s_order == 'asc':
        direction = 1
    elif s_order == 'des':
        direction = -1
    else:
        direction = 1

    # Normalize the get parameter

    if len(page) == 0:
        page = '1'
    if len(limit) == 0:
        limit = '0'

    # The page and limit result shouldn't empty (e.g. ?p=)
    # If that happen the parameter will be available but empty
    # Check the page and limit parameter
    # The page and limit result shouldn't empty (e.g. ?p=)
    # If that happen the parameter will be available but empty
    # Check the page and limit parameter exist and correct data type (int)
    if page != '' and limit != '' and gutils.integer_check(page) and gutils.integer_check(limit):
        # -1 so the skip will be matched with the page:
        # Todo : Warning, skip will be slow at scale
        skip = (int(page) - 1) * int(limit)
        results = db.get_user_device_list(user_uuid=user['user_uuid'], skip=skip, limit=int(limit), text=query, direction=direction)
        # When there is no limit for the result , the next page should not called
        if limit != '0':
            # Check if the next page exist
            # Todo : Find better way to do this
            next_results = db.get_user_device_list(user_uuid=user['user_uuid'], skip=(int(page) * int(limit)), limit=int(limit), text=query, direction=direction).count(True)
        else:
            next_results = 0
        # if there is next page return next page number
        # if there is no next page return "-"
        if next_results != 0:
            next_page = str(int(page) + 1)
        else:
            next_page = "-"
        # initiate response data structure
        data = {
            'page': page,
            'next_page': next_page,
            'results': [],
            'results_count': results.count(True)
        }

        # new data structure for device list from the result
        # the structure included everything so there is no need to call for another endpoint
        # Iterate through the mongo result
        for result in results:
            # Total for sensor value that goes above the threshold
            over_threshold_total = 0
            preparsed_result = {}
            preparsed_result['device_sensors'] = []
            preparsed_result['device_uuid'] = result['device_uuid']
            preparsed_result['position'] = result['position']
            preparsed_result['location_text'] = result['location_text']
            preparsed_result['read_key'] = result['read_key']
            preparsed_result['write_key'] = result['write_key']
            preparsed_result['device_name'] = result['device_name']
            preparsed_result['time_added'] = result['time_added']
            # Quick overall status of the device
            preparsed_result['quick_status'] = ''
            preparsed_result['over_threshold'] = 0

            # iterate through each user_sensor_uuids
            for user_sensor_uuid in result['user_sensor_uuids']:
                sensor_detail = {}
                user_sensor = db.get_user_sensor_by_uuid(user_sensor_uuid)
                sensor_detail['user_sensor_uuid'] = user_sensor['user_sensor_uuid']
                sensor_detail['user_sensor_name'] = user_sensor['user_sensor_name']
                sensor_detail['sensor_threshold'] = user_sensor['sensor_threshold']
                sensor_detail['threshold_enabled'] = user_sensor['threshold_enabled']
                sensor_detail['threshold_direction'] = user_sensor['threshold_direction']
                # Get master sensor for value type and unit
                master_sensor = db.get_master_sensor_by_uuid(user_sensor['master_sensor_uuid'])
                # Get master sensor reference for sensor model
                master_sensor_reference = db.get_master_sensor_reference_by_uuid(master_sensor_reference_uuid=master_sensor['master_sensor_reference_uuid'])
                sensor_detail['master_sensor_name'] = master_sensor['master_sensor_name']
                # get lastest data value
                # take the first element, as the result length is one, by iterating over mongo cursor (as it cannot be accessed directly with index)
                device_latest_datas = db.get_n_latest_device_data(result['device_uuid'], 1)

                # Check if there's latest data available
                if device_latest_datas.count() != 0:
                    for device_latest_data in device_latest_datas:
                        for sensor_data in device_latest_data['sensor_datas']:
                            if sensor_data['user_sensor_uuid'] == user_sensor['user_sensor_uuid']:
                                sensor_detail['latest_value_added'] = device_latest_data['time_added']
                                sensor_detail['latest_value'] = sensor_data['user_sensor_value']

                    # Check the threshold for quick status for sensor with enabled threshold
                    if sensor_detail['threshold_enabled']:
                        if sensor_detail['threshold_direction'] == "1":
                            if sensor_detail['latest_value'] > sensor_detail['sensor_threshold']:
                                over_threshold_total += 1

                        elif sensor_detail['threshold_direction'] == "-1":
                            if sensor_detail['latest_value'] < sensor_detail['sensor_threshold']:
                                over_threshold_total += 1
                else:
                    # If theres no data yet
                    sensor_detail['latest_value_added'] = None
                    sensor_detail['latest_value'] = None

                # Add detail about sensor unit convertion for easier api call
                sensor_detail['unit_name'] = master_sensor['master_sensor_default_unit_name']
                sensor_detail['unit_symbol'] = master_sensor['master_sensor_default_unit_symbol']
                sensor_detail['sensor_model'] = master_sensor_reference['sensor_model']
                preparsed_result['device_sensors'].append(sensor_detail)
            # Add quick overall status
            if over_threshold_total == 0:
                preparsed_result['quick_status'] = status_good
                preparsed_result['over_threshold'] = 0
            else:
                preparsed_result['quick_status'] = status_warning.format(over_threshold_total)
                preparsed_result['over_threshold'] = over_threshold_total
            # Append to the main data
            data['results'].append(preparsed_result)

        # Finish time
        data['time_to_generate'] = timeit.default_timer() - start_time

        response_data = rg.data_response_generator(data)
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)
    else:
        response_data = rg.error_response_generator(400, "Invalid get parameter value")
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

# Retrieve user device data (Internally using JWT and device id)
# using GET because we need url parameter for easier access
@get_method_required
@authentication_required
def retrieve_device_data(request, user):

    # Start time
    start_time = timeit.default_timer()
    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()
    gutils = GudangUtils()

    # Device UUID
    device_uuid = request.GET.get('device_uuid', '')
    # Page number
    page = request.GET.get('p', '1')
    # Start date, defaulting to 0
    from_date = request.GET.get('fd', '0')
    # End date , defaulting to right now
    to_date = request.GET.get('td', float(datetime.datetime.now().timestamp()))
    # Per page limit
    limit = request.GET.get('l', '10')
    # Order method , the data sorted in descending order (newest data first) by default
    s_order = request.GET.get('o', 'des')
    # normalize the order value
    if s_order == 'asc':
        direction = 1
    elif s_order == 'des':
        direction = -1
    else:
        direction = 1

    # Normalize the blank get parameter
    # Todo : check normalization for order value

    if len(page) == 0:
        page = '1'
    if len(limit) == 0:
        limit = '0'

    # The page and limit result shouldn't empty (e.g. ?p=)
    # If that happen the parameter will be available but empty
    # Check if the page and limit parameter exist and correct data type (int)
    # Check if the from_date and to_date in correct data type(float)
    if page != '' and limit != '' and gutils.integer_check(page) and gutils.integer_check(limit) and gutils.float_check(from_date) and gutils.float_check(to_date):
        # make sure the value in the correct order
        if (float(to_date) > float(from_date) and (float(to_date) < datetime.datetime.now().timestamp())):
            # Get the device data
            device_data = db.get_device_by_uuid(device_uuid=device_uuid)
            # If device_uuid isn't valid
            if device_data != None:
                # Make sure the device is owned by the user
                if user['user_uuid'] == device_data['user_uuid']:
                    # -1 so the skip will be matched with the page:
                    # Todo : Warning, skip will be slow at scale
                    skip = (int(page) - 1) * int(limit)
                    results = db.get_device_data(device_uuid=device_uuid, skip=skip,limit=int(limit), direction=direction,from_date=float(from_date), to_date=float(to_date))

                    if limit != '0':
                        # Check if the next page exist
                        # Todo : Find better way to do this
                        next_results = db.get_device_data(device_uuid=device_uuid, skip=(int(page) * int(limit)), limit=int(limit), direction=direction, from_date=float(from_date), to_date=float(to_date)).count(True)
                    else:
                        next_results = 0
                    # if there is next page return next page number
                    # if there is no next page return "-"
                    if next_results != 0:
                        next_page = str(int(page) + 1)
                    else:
                        next_page = "-"

                    # New result structure for easier parsing in client side
                    preparsed_results = []
                    # Temp list for storing the sensor_uuid
                    sensor_uuids = []
                    # list for storing sensor value details
                    sensor_values = {}
                    for result in results:
                        for sensor_data in result['sensor_datas']:
                            if sensor_data['user_sensor_uuid'] not in sensor_uuids:
                                sensor_uuids.append(sensor_data['user_sensor_uuid'])
                                # Create new key using sensor_uuid
                                sensor_values[sensor_data['user_sensor_uuid']] = []
                            sensor_value = {
                                'value': sensor_data['user_sensor_value'],
                                'time_added': result['time_added']
                            }
                            sensor_values[sensor_data['user_sensor_uuid']].append(sensor_value)

                    for sensor_uuid in sensor_uuids:
                        sensor_result = {
                            'sensor_uuid': sensor_uuid,
                            'sensor_values': sensor_values[sensor_uuid]
                        }
                        preparsed_results.append(sensor_result)

                    data = {
                        'page': page,
                        'next_page': next_page,
                        'device_uuid': device_uuid,
                        'results': preparsed_results,
                        'result_per_sensor_count': results.count(True),
                        'listed_sensor_count': len(sensor_uuids)
                    }
                    # Finish time
                    data['time_to_generate'] = timeit.default_timer() - start_time
                    # return the result
                    response_data = rg.data_response_generator(data)
                    return HttpResponse(json.dumps(response_data), content_type="application/json",
                                        status=200)

                else:
                    # Return the same message as invalid deice_uuid to obsofucate the device ownership
                    response_data = rg.error_response_generator(400, "Invalid device UUID")
                    return HttpResponse(json.dumps(response_data), content_type="application/json",
                                        status=400)
            else:
                response_data = rg.error_response_generator(400, "Invalid device UUID")
                return HttpResponse(json.dumps(response_data), content_type="application/json",
                                    status=400)
        else:
            response_data = rg.error_response_generator(400, "Invalid date submitted")
            return HttpResponse(json.dumps(response_data), content_type="application/json",
                                status=400)
    else:
        response_data = rg.error_response_generator(400, "Invalid get parameter value")
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

@get_method_required
@authentication_required
def retrieve_device_data_statistic(request, user):
    # Start time
    start_time = timeit.default_timer()
    # Gudang class
    rg = ResponseGenerator()
    requtils = RequestUtils()
    auth = GudangSidikModule()
    db = GudangMongoDB()
    gutils = GudangUtils()

    # Device UUID
    device_uuid = request.GET.get('device_uuid', '')
    # start time
    from_time = request.GET.get('ft', '')
    # End time , defaulting to right now
    to_time = request.GET.get('tt', '')
    # Time range divider
    divider = request.GET.get('divider', '')

    # check the parameter
    if (len(device_uuid) != 0) and (len(from_time) != 0) and (len(to_time) != 0) and (len(divider) != 0):
        # Check from_time, to_time, and divider data type
        if gutils.float_check(from_time) and gutils.float_check(to_time) and gutils.float_check(divider):
            if float(divider) > 0:
                if float(to_time) > float(from_time):
                    # check if the device is correct and owned by the user
                    device = db.get_device_by_uuid(device_uuid=device_uuid)
                    if device != None:
                        # Check device ownership
                        if device['user_uuid'] == user['user_uuid']:
                            # Type cast the value
                            to_time = float(to_time)
                            from_time = float(from_time)
                            divider = float(divider)

                            from_time_datetime = datetime.datetime.fromtimestamp(from_time)
                            to_time_datetime = datetime.datetime.fromtimestamp(to_time)
                            # Delta between from_time and to_time
                            time_delta = to_time_datetime - from_time_datetime
                            # Prepare statistic data
                            data = {
                                'device_name': device['device_name'],
                                'device_uuid': device['device_uuid'],
                                'total_user_sensor': len(device['user_sensor_uuids']),
                                # Random colors for being used by client's chart
                                'random_material_colors': gutils.get_n_random_material_color(len(device['user_sensor_uuids'])),
                                'device_data_statistics': [],
                                'time_generated': float(datetime.datetime.now().timestamp())
                            }
                            # Iterate between the user_sensor_uuid in the device
                            for user_sensor_uuid in device['user_sensor_uuids']:
                                # Get the sensor data
                                user_sensor = db.get_user_sensor_by_uuid(user_sensor_uuid=user_sensor_uuid)
                                # Get master sensor
                                master_sensor = db.get_master_sensor_by_uuid(master_sensor_uuid=user_sensor['master_sensor_uuid'])

                                # Reinitialize the data
                                time_range = time_delta / divider
                                current_pointer = from_time_datetime
                                # Iteration for each range
                                # Iteration count depends on divider value

                                device_data_statistic = {
                                    'user_sensor_uuid': user_sensor_uuid,
                                    'user_sensor_name': user_sensor['user_sensor_name'],
                                    'unit_name': master_sensor['master_sensor_name'],
                                    'unit_symbol': master_sensor['master_sensor_default_unit_symbol'],
                                    'statistic_values': []
                                }
                                # Iterate between the time range
                                # Number of the iteration depends on divider value
                                while current_pointer < to_time_datetime:
                                    # Pointer for mapping next to_time
                                    next_pointer = current_pointer + time_range
                                    results = db.user_sensor_statistic_data(from_time=current_pointer.timestamp(), to_time=next_pointer.timestamp(), device_uuid=device_uuid,
                                                                            user_sensor_uuid=user_sensor_uuid)
                                    # Check if the result is empty (no value between the time range)
                                    if len(results) == 0:
                                        avg_sensor_value = None
                                        max_sensor_value = None
                                        min_sensor_value = None
                                        data_count = 0
                                    else:
                                        avg_sensor_value = float(results[0]['user_sensor_value_average'])
                                        max_sensor_value = float(results[0]['user_sensor_value_max'])
                                        min_sensor_value = float(results[0]['user_sensor_value_min'])
                                        data_count = int(results[0]['data_count'])

                                    statistic_value = {
                                        'from_time': float(current_pointer.timestamp()),
                                        'to_time': float(next_pointer.timestamp()),
                                        'avg_sensor_value': avg_sensor_value,
                                        'max_sensor_value': max_sensor_value,
                                        'min_sensor_value': min_sensor_value,
                                        'data_count': int(data_count)
                                    }

                                    # Append the stastic for each sensor
                                    device_data_statistic['statistic_values'].append(statistic_value)
                                    current_pointer += time_range

                                # Append the final stucture
                                data['device_data_statistics'].append(device_data_statistic)

                            # Finish time
                            data['time_to_generate'] = timeit.default_timer() - start_time
                            # Generate response object
                            response_data = rg.data_response_generator(data)
                            return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)
                        else:
                            response_data = rg.error_response_generator(400, 'Invalid device UUID')
                            return HttpResponse(json.dumps(response_data), content_type="application/json",
                                                status=400)
                    else:
                        response_data = rg.error_response_generator(400, 'Invalid device UUID')
                        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
                else:
                    response_data = rg.error_response_generator(400, 'To Time must be larger than from time')
                    return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
            else:
                response_data = rg.error_response_generator(400, 'Divider must be larger than zero')
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
        else:
            response_data = rg.error_response_generator(400, "Incorrect parameter data type")
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
    else:
        response_data = rg.error_response_generator(400, "Required parameter missing")
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

@get_method_required
@authentication_required
def retrieve_device_data_statistic_monthly(request, user):
    # Start time
    start_time = timeit.default_timer()
    # Gudang class
    rg = ResponseGenerator()
    requtils = RequestUtils()
    auth = GudangSidikModule()
    db = GudangMongoDB()
    gutils = GudangUtils()

    # Device UUID
    device_uuid = request.GET.get('device_uuid', '')
    # month (1 to 12)
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')

    if (len(device_uuid) != 0) and (len(month) != 0) and (len(year) != 0):
        # Check month and year validity
        if gutils.month_check(month=month) and gutils.year_check(year=year):
            # check if the device is correct and owned by the user
            device = db.get_device_by_uuid(device_uuid=device_uuid)
            if device != None:
                # Check device ownership
                if device['user_uuid'] == user['user_uuid']:
                    # Get the number of day based on month and year
                    # Month total day available on the 2nd element of the result list
                    number_of_day = monthrange(int(year), int(month))[1]
                    # Prepare statistic data
                    data = {
                        'device_uuid': device['device_uuid'],
                        'device_name': device['device_name'],
                        'total_user_sensor': len(device['user_sensor_uuids']),
                        'device_data_statistics': [],
                        # Random colors for being used by client's chart
                        'random_material_colors': gutils.get_n_random_material_color(len(device['user_sensor_uuids'])),
                        'month': str(month),
                        'year': str(year),
                        'total_days': number_of_day,
                        'time_generated': float(datetime.datetime.now().timestamp())
                    }

                    for user_sensor_uuid in device['user_sensor_uuids']:
                        # Get the sensor data
                        user_sensor = db.get_user_sensor_by_uuid(user_sensor_uuid=user_sensor_uuid)
                        # Get master sensor
                        master_sensor = db.get_master_sensor_by_uuid(master_sensor_uuid=user_sensor['master_sensor_uuid'])

                        device_data_statistic = {
                            'user_sensor_uuid': user_sensor_uuid,
                            'user_sensor_name': user_sensor['user_sensor_name'],
                            'unit_name': master_sensor['master_sensor_name'],
                            'unit_symbol': master_sensor['master_sensor_default_unit_symbol'],
                            'statistic_values': []
                        }
                        # Iterate through the whole month
                        for i in range(1, number_of_day + 1):
                            current_pointer = datetime.datetime(year=int(year), month=int(month), day=i)
                            # time delta defined as 24 hour a day
                            results = db.user_sensor_statistic_data(
                                from_time=current_pointer.timestamp(), to_time=(current_pointer + datetime.timedelta(hours=24)).timestamp(),
                                device_uuid=device_uuid, user_sensor_uuid=user_sensor_uuid)

                            if len(results) == 0:
                                avg_sensor_value = None
                                max_sensor_value = None
                                min_sensor_value = None
                                data_count = 0
                            else:
                                avg_sensor_value = float(results[0]['user_sensor_value_average'])
                                max_sensor_value = float(results[0]['user_sensor_value_max'])
                                min_sensor_value = float(results[0]['user_sensor_value_min'])
                                data_count = int(results[0]['data_count'])

                            statistic_value = {
                                'day': str(i),
                                'from_time': float(current_pointer.timestamp()),
                                'to_time': float((current_pointer + datetime.timedelta(hours=24)).timestamp()),
                                'avg_sensor_value': avg_sensor_value,
                                'max_sensor_value': max_sensor_value,
                                'min_sensor_value': min_sensor_value,
                                'data_count': int(data_count)
                            }

                            # Append the data
                            device_data_statistic['statistic_values'].append(statistic_value)

                        # Append all result into main data
                        data['device_data_statistics'].append(device_data_statistic)

                    # Finish time
                    data['time_to_generate'] = timeit.default_timer() - start_time
                    # Generate response object
                    response_data = rg.data_response_generator(data)
                    return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)
                else:
                    response_data = rg.error_response_generator(400, 'Invalid device UUID')
                    return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
            else:
                response_data = rg.error_response_generator(400, 'Invalid device UUID')
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
        else:
            response_data = rg.error_response_generator(400, "Incorrect parameter data value")
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
    else:
        response_data = rg.error_response_generator(400, "Required parameter missing")
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

@get_method_required
@authentication_required
def retrieve_device_device_data_statistic_yearly(request, user):

    # Start time
    start_time = timeit.default_timer()
    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()
    gutils = GudangUtils()

    # Device UUID
    device_uuid = request.GET.get('device_uuid', '')
    year = request.GET.get('year', '')

    if (len(device_uuid) != 0) and (len(year) != 0):
        # Check month and year validity
        if gutils.year_check(year=year):
            # check if the device is correct and owned by the user
            device = db.get_device_by_uuid(device_uuid=device_uuid)
            if device != None:
                # Check device ownership
                if device['user_uuid'] == user['user_uuid']:

                    # Prepare statistic data
                    data = {
                        'device_uuid': device['device_uuid'],
                        'device_name': device['device_name'],
                        'total_user_sensor': len(device['user_sensor_uuids']),
                        # Random colors for being used by client's chart
                        'random_material_colors': gutils.get_n_random_material_color(len(device['user_sensor_uuids'])),
                        'device_data_statistics': [],
                        'year': str(year),
                        'time_generated': float(datetime.datetime.now().timestamp())
                    }

                    for user_sensor_uuid in device['user_sensor_uuids']:
                        # Get the sensor data
                        user_sensor = db.get_user_sensor_by_uuid(user_sensor_uuid=user_sensor_uuid)
                        # Get master sensor
                        master_sensor = db.get_master_sensor_by_uuid(master_sensor_uuid=user_sensor['master_sensor_uuid'])

                        device_data_statistic = {
                            'user_sensor_uuid': user_sensor_uuid,
                            'user_sensor_name': user_sensor['user_sensor_name'],
                            'unit_name': master_sensor['master_sensor_name'],
                            'unit_symbol': master_sensor['master_sensor_default_unit_symbol'],
                            'statistic_values': []
                        }
                        # Iterate through the year
                        for i in range(1, 13):
                            # Number of days for each month
                            # Number of days available in the second element
                            number_of_day = monthrange(year=int(year), month=i)[1]
                            # get the average data
                            # add 1 day to to_time so the  last day will be exactly 24 hour
                            results = db.user_sensor_statistic_data(
                                from_time=datetime.datetime(year=int(year), month=i, day=1).timestamp(),
                                to_time=(datetime.datetime(year=int(year), month=i, day=number_of_day) + datetime.timedelta(hours=24)).timestamp(),
                                device_uuid=device_uuid, user_sensor_uuid=user_sensor_uuid)

                            if len(results) == 0:
                                avg_sensor_value = None
                                max_sensor_value = None
                                min_sensor_value = None
                                data_count = 0
                            else:
                                avg_sensor_value = float(results[0]['user_sensor_value_average'])
                                max_sensor_value = float(results[0]['user_sensor_value_max'])
                                min_sensor_value = float(results[0]['user_sensor_value_min'])
                                data_count = int(results[0]['data_count'])

                            statistic_value = {
                                'month': str(i),
                                'from_time': float(datetime.datetime(year=int(year), month=i, day=1).timestamp()),
                                'to_time': (datetime.datetime(year=int(year), month=i, day=number_of_day) + datetime.timedelta(hours=24)).timestamp(),
                                'avg_sensor_value': avg_sensor_value,
                                'max_sensor_value': max_sensor_value,
                                'min_sensor_value': min_sensor_value,
                                'data_count': int(data_count),
                                'total_day': int(number_of_day)
                            }

                            # Append the data
                            device_data_statistic['statistic_values'].append(statistic_value)

                        # Append all result into main data
                        data['device_data_statistics'].append(device_data_statistic)
                        # Finsih time
                        data['time_to_generate'] = timeit.default_timer() - start_time
                    # Generater response object
                    response_data = rg.data_response_generator(data)
                    return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)

                else:
                    response_data = rg.error_response_generator(400, 'Invalid device UUID')
                    return HttpResponse(json.dumps(response_data), content_type="application/json",
                                        status=400)
            else:
                response_data = rg.error_response_generator(400, 'Invalid device UUID')
                return HttpResponse(json.dumps(response_data), content_type="application/json",status=400)
        else:
            response_data = rg.error_response_generator(400, "Incorrect parameter data value")
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
    else:
        response_data = rg.error_response_generator(400, "Required parameter missing")
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

@get_method_required
@authentication_required
def retrieve_master_sensor_reference_list(request, user):

    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()

    # Get all master sensor reference (for adding new sensor)
    master_sensor_references = db.get_all_master_sensor_reference()
    data = {
        'master_sensor_references': [],
        'master_sensor_reference_count': master_sensor_references.count(True)
    }

    # Append to data
    for master_sensor_reference in master_sensor_references:
        # Pop the id
        master_sensor_reference.pop('_id')
        # Detailed structure for value type
        sensor_value_type = []
        # Grab other detail from master sensor
        for master_sensor_uuid in master_sensor_reference['master_sensor_uuids']:
            # Value scale and unit
            master_sensor = db.get_master_sensor_by_uuid(master_sensor_uuid=master_sensor_uuid)
            master_sensor_value_type = {
                'value_type': master_sensor['master_sensor_name'],
                'unit': master_sensor['master_sensor_default_unit_name'],
                'unit_symbol': master_sensor['master_sensor_default_unit_symbol']
            }
            sensor_value_type.append(master_sensor_value_type)

        # Remove uuid mapping
        master_sensor_reference.pop('master_sensor_uuids')
        # Remove pin mapping
        master_sensor_reference.pop('sensor_pin_mappings')
        master_sensor_reference['sensor_value_type'] = sensor_value_type

        data['master_sensor_references'].append(master_sensor_reference)

    # Generate response object
    response_data = rg.data_response_generator(data)
    return HttpResponse(json.dumps(response_data), content_type='application/json', status=200)

@get_method_required
@authentication_required
def retrieve_supported_board_list(request, user):

    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()

    # Get all supported board
    supported_boards = db.get_all_supported_board()
    data = {
        'supported_boards': [],
        'supported_boards_count': supported_boards.count(True)
    }

    # Append to data
    for supported_board in supported_boards:
        # Pop the id
        supported_board.pop('_id')
        # Pop the pin mapping
        supported_board.pop('board_pins')
        data['supported_boards'].append(supported_board)

    # Generate response object
    response_data = rg.data_response_generator(data)
    return HttpResponse(json.dumps(response_data), content_type='application/json', status=200)

@get_method_required
@authentication_required
def retrieve_device_data_count_chart(request, user):
    # Start time
    start_time = timeit.default_timer()

    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()
    gutils = GudangUtils()

    # Device name list
    device_names = []
    # Data count list
    data_count = []
    user_devices = db.get_user_device_list_by_user_uuid(user_uuid=user['user_uuid'])

    for user_device in user_devices:
        device_names.append(user_device['device_name'])
        data_count.append(db.get_device_data_count_by_uuid(device_uuid=user_device['device_uuid']))

    data = {
        'device_names': device_names,
        'data_counts': data_count,
        'background_colors': gutils.get_n_random_material_color(user_devices.count(True))
    }
    # Finish time
    data['time_to_generate'] = timeit.default_timer() - start_time

    # Generate response object
    response_data = rg.data_response_generator(data)
    return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)

@get_method_required
@authentication_required
def retrieve_device_sensor_status_chart(request, user):
    # Start time
    start_time = timeit.default_timer()

    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()

    user_devices = db.get_user_device_list_by_user_uuid(user_uuid=user['user_uuid'])
    # Statuses
    warning_status_count = 0
    normal_status_count = 0
    disabled_status_count = 0
    # Iterate through the devices
    for user_device in user_devices:
        for user_sensor_uuid in user_device['user_sensor_uuids']:
            user_sensor = db.get_user_sensor_by_uuid(user_sensor_uuid=user_sensor_uuid)
            if (user_sensor['threshold_enabled']):
                if (user_sensor['currently_over_threshold']):
                    warning_status_count += 1
                else:
                    normal_status_count += 1
            else:
                disabled_status_count += 1

    # Main data structure
    data = {
        'status_count': {
            'normal': normal_status_count,
            'warning': warning_status_count,
            'disabled': disabled_status_count
        },
        'time_to_generate': timeit.default_timer() - start_time
    }
    # Generate response object
    response_data = rg.data_response_generator(data)
    return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)

# Retrieve simple device list
# Only returning device uuid and its name
@get_method_required
@authentication_required
def retrieve_simple_device_list(request, user):
    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()

    user_devices = db.get_user_device_list_by_user_uuid(user_uuid=user['user_uuid'])
    data = {
        'user_devices': [],
        'user_device_count': user_devices.count(True)
    }

    for user_device in user_devices:
        user_device_data = {
            'device_uuid': user_device['device_uuid'],
            'device_name': user_device['device_name']
        }
        # Append to the main data
        data['user_devices'].append(user_device_data)

    response_data = rg.data_response_generator(data)
    return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)

# Retrieve device arduino code
@get_method_required
@authentication_required
def retrieve_device_arduino_code(request, user, device_uuid):
    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()

    device = db.get_device_data_by_uuid(user_uuid=user['user_uuid'], device_uuid=device_uuid)
    if (device):
        wifi_connection = db.get_user_wifi_connection_by_uuid(user_uuid=user['user_uuid'], user_wifi_connection_uuid=device['user_wifi_connection_uuid'])
        if (wifi_connection):
            tls_fingerprint = db.get_latest_tls_fingerprint(algorithm='SHA1', domain='gudang.rumahiot.panjatdigital.com')
            # Initiate the template object
            tmaster = GudangTemplateMaster(wifi_connection=wifi_connection, device=device, tls_fingerprint=tls_fingerprint)
            string_template = tmaster.generate_gampang_template()
            # Prepare the filename
            file_name = 'rumahiot_{}.ino'.format(device['device_name'].lower().replace(' ', '_'))
            file_response = rg.file_response_generator(filename=file_name, content_type='text/x-arduino', content=string_template)
            return file_response

        else:
            response_data = rg.error_response_generator(400, 'Invalid wifi connection uuid')
            return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
    else:
        response_data = rg.error_response_generator(400, 'Invalid device uuid')
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

# Retrieve user sensor mapping
@get_method_required
@authentication_required
def retrieve_user_sensor_mapping(request, user, device_uuid):

    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()

    device = db.get_device_data_by_uuid(user_uuid=user['user_uuid'], device_uuid=device_uuid)
    if (device):
        user_sensor_mapping_uuid_list = []

        data = {
            'sensor_mapping_datas': [],
        }

        # Iterate throught user sensor
        for user_sensor_uuid in device['user_sensor_uuids']:
            user_sensor = db.get_user_sensor_by_uuid(user_sensor_uuid=user_sensor_uuid)
            user_sensor_mapping = db.get_user_sensor_mapping_by_uuid(user_sensor_mapping_uuid=user_sensor['user_sensor_mapping_uuid'])
            master_sensor = db.get_master_sensor_by_uuid(master_sensor_uuid=user_sensor['master_sensor_uuid'])
            master_sensor_reference = db.get_master_sensor_reference_by_uuid(master_sensor_reference_uuid=master_sensor['master_sensor_reference_uuid'])

            if user_sensor['user_sensor_mapping_uuid'] not in user_sensor_mapping_uuid_list:
                # Prepare & remove unnecessary data
                user_sensor_mapping.pop('user_sensor_mapping_uuid')
                user_sensor_mapping.pop('time_added')
                user_sensor_mapping.pop('_id')
                master_sensor_reference.pop('_id')
                master_sensor_reference.pop('master_sensor_reference_uuid')
                master_sensor_reference.pop('library_dependencies')
                master_sensor_reference.pop('library_variable_initialization')
                master_sensor_reference.pop('library_initialization_command')
                master_sensor_reference.pop('sensor_pin_mappings')
                master_sensor_reference.pop('master_sensor_uuids')
                master_sensor_reference.pop('sensor_image_source')

                sensor_mapping_data = {
                    'pin_mappings': user_sensor_mapping['sensor_pin_mappings'],
                    'master_sensor_reference': master_sensor_reference
                }
                data['sensor_mapping_datas'].append(sensor_mapping_data)
                user_sensor_mapping_uuid_list.append(user_sensor['user_sensor_mapping_uuid'])

        data['sensor_mapping_data_count'] = len(data['sensor_mapping_datas'])
        # return response object
        response_data = rg.data_response_generator(data)
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)

    else:
        response_data = rg.error_response_generator(400, 'Invalid device uuid')
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

@get_method_required
@admin_authentication_required
def retrieve_detailed_supported_board_list(request, user):

    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()

    all_detailed_supported_board = db.get_all_detailed_supported_board()

    data = {
        'detailed_supported_boards': all_detailed_supported_board,
        'detailed_supported_boards_count': len(all_detailed_supported_board)
    }

    # Generate response object
    response_data = rg.data_response_generator(data)
    return HttpResponse(json.dumps(response_data), content_type='application/json', status=200)

@get_method_required
@admin_authentication_required
def retrieve_detailed_supported_sensor_list(request, user):

    # Gudang class
    rg = ResponseGenerator()
    db = GudangMongoDB()

    all_detailed_supported_sensor = db.get_all_detailed_supported_sensor()

    data = {
        'detailed_supported_sensors': all_detailed_supported_sensor,
        'detailed_supported_sensors_count': len(all_detailed_supported_sensor)
    }

    # Generate response object
    response_data = rg.data_response_generator(data)
    return HttpResponse(json.dumps(response_data), content_type='application/json', status=200)
