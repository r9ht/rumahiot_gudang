from django.shortcuts import render,HttpResponse
import json
from datetime import datetime
from rumahiot_gudang.apps.store.utils import RequestUtils,ResponseGenerator,GudangUtils
from rumahiot_gudang.apps.retrieve.authorization import GudangSidikModule
from rumahiot_gudang.apps.store.mongodb import GudangMongoDB

# Create your views here.

# Retrieve corresponding user device list
# Using GET because we need url parameter
def retrieve_device_list(request):
    # Gudang class
    rg = ResponseGenerator()
    requtils = RequestUtils()
    auth = GudangSidikModule()
    db = GudangMongoDB()
    gutils = GudangUtils()

    if request.method != "GET":
        response_data = rg.error_response_generator(400, "Bad request method")
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
    else:
        # Page number
        page = request.GET.get('p', '1')
        # its ok for query to be empty
        query = request.GET.get('q', '')
        # Per page limit
        limit = request.GET.get('l','10')
        # Order method , the data sorted in ascending order by default
        s_order = request.GET.get('o','asc')
        # normalize the order value
        if s_order == 'asc' :
            direction = 1
        elif s_order == 'des' :
            direction = -1
        else:
            direction = 1

        # The page and limit result shouldn't empty (e.g. ?p=)
        # If that happen the parameter will be available but empty
        # Check the page and limit parameter

        try:
            token = requtils.get_access_token(request)
        except KeyError:
            response_data = rg.error_response_generator(400, "Please define the authorization header")
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
        else:
            if token['token'] != None:
                user = auth.get_user_data(token['token'])
                if user['user_uuid'] != None:
                    # The page and limit result shouldn't empty (e.g. ?p=)
                    # If that happen the parameter will be available but empty
                    # Check the page and limit parameter exist and correct data type (int)
                    if page != '' and limit !='' and gutils.integer_check(page) and gutils.integer_check(limit):
                        # -1 so the skip will be matched with the page:
                        # Todo : Warning, skip will be slow at scale
                        skip = (int(page) - 1) * int(limit)
                        results = db.get_user_device_list(user_uuid=user['user_uuid'],skip=skip,limit=int(limit),text=query,direction=direction)
                        # Check if the next page exist
                        # Todo : Find better way to do this
                        next_results = db.get_user_device_list(user_uuid=user['user_uuid'],skip=(int(page) * int(limit)),limit=int(limit),text=query,direction=direction).count(True)
                        # if there is next page return next page number
                        # if there is no next page return "-"
                        if next_results != 0 :
                            next_page = str(int(page) + 1)
                        else:
                            next_page = "-"
                        # initiate response data structure
                        data = {
                            'page' : page,
                            'next_page' : next_page,
                            'results' : [],
                            'results_count' : results.count(True)
                        }
                        # put the result into the data
                        for result in results:
                            # Pop sensitive data
                            result.pop('_id', None)
                            result.pop('user_uuid', None)
                            data['results'].append(result)
                        # return the result
                        response_data = rg.data_response_generator(data)
                        return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)
                    else:
                        response_data = rg.error_response_generator(400, "Invalid get parameter value")
                        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
                else:
                    response_data = rg.error_response_generator(400, user['error'])
                    return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
            else:
                response_data = rg.error_response_generator(400, token['error'])
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)



# Retrieve user device data (Internally using JWT and device id)
# using GET because we need url parameter for easier access
def retrieve_device_data(request):
    # Gudang class
    rg = ResponseGenerator()
    requtils = RequestUtils()
    auth = GudangSidikModule()
    db = GudangMongoDB()
    gutils = GudangUtils()
    if request.method != "GET":
        response_data = rg.error_response_generator(400, "Bad request method")
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
    else:
        # Device UUID
        device_uuid = request.GET.get('device_uuid', '')
        # Page number
        page = request.GET.get('p', '1')
        # Start date, defaulting to 0
        from_date = request.GET.get('fd','0')
        # End date , defaulting to right now
        to_date = request.GET.get('td',float(datetime.now().timestamp()))
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

        # The page and limit result shouldn't empty (e.g. ?p=)
        # The parameter will be available but empty
        # Check the page and limit parameter
        try:
            token = requtils.get_access_token(request)
        except KeyError:
            response_data = rg.error_response_generator(400, "Please define the authorization header")
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
        else:
            if token['token'] != None:
                # Check the device uuid
                if len(device_uuid) != 0:
                    user = auth.get_user_data(token['token'])
                    if user['user_uuid'] != None:
                        # The page and limit result shouldn't empty (e.g. ?p=)
                        # If that happen the parameter will be available but empty
                        # Check if the page and limit parameter exist and correct data type (int)
                        # Check if the from_date and to_date in correct data type(float)
                        if page != '' and limit != '' and gutils.integer_check(page) and gutils.integer_check(limit) and gutils.float_check(from_date) and gutils.float_check(to_date):
                            # make sure the value in the correct order
                            if (float(to_date) > float(from_date) and (float(to_date) < datetime.now().timestamp())):
                                # Get the device data
                                device_data = db.get_user_device_data_uuid(device_uuid=device_uuid)
                                # If device_uuid isn't valid
                                if device_data != None:
                                    # Make sure the device is owned by the user
                                    if device_data != device_data['user_uuid']:
                                        # -1 so the skip will be matched with the page:
                                        # Todo : Warning, skip will be slow at scale
                                        skip = (int(page) - 1) * int(limit)
                                        results = db.get_device_data(device_uuid=device_uuid,skip=skip,limit=int(limit),direction=direction,from_date=float(from_date),to_date=float(to_date))
                                        # Check if the next page exist
                                        # Todo : Find better way to do this
                                        next_results = db.get_device_data(device_uuid=device_uuid,skip=(int(page) * int(limit)),limit=int(limit),direction=direction,from_date=float(from_date),to_date=float(to_date)).count(True)
                                        # if there is next page return next page number
                                        # if there is no next page return "-"
                                        if next_results != 0:
                                            next_page = str(int(page) + 1)
                                        else:
                                            next_page = "-"
                                        data = {
                                            'page': page,
                                            'next_page': next_page,
                                            'results': [],
                                            'results_count': results.count(True)
                                        }
                                        # put the result into the data
                                        for result in results:
                                            # Pop sensitive data
                                            result.pop('_id', None)
                                            result.pop('user_uuid', None)
                                            data['results'].append(result)
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
                                    response_data = rg.error_response_generator(400,"Invalid device UUID")
                                    return HttpResponse(json.dumps(response_data), content_type="application/json",
                                                        status=400)
                            else:
                                response_data = rg.error_response_generator(400, "Invalid date submitted")
                                return HttpResponse(json.dumps(response_data), content_type="application/json",
                                                    status=400)
                        else:
                            response_data = rg.error_response_generator(400, "Invalid get parameter value")
                            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
                    else:
                        response_data = rg.error_response_generator(400, user['error'])
                        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
                else:
                    response_data = rg.error_response_generator(400, 'Please specify the Device UUID')
                    return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
            else:
                response_data = rg.error_response_generator(400, token['error'])
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)


def retrieve_sensor_data(request):
    # Gudang class
    rg = ResponseGenerator()
    requtils = RequestUtils()
    auth = GudangSidikModule()
    db = GudangMongoDB()
    gutils = GudangUtils()
    if request.method != "GET":
        response_data = rg.error_response_generator(400, "Bad request method")
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
    else:
        # sensor_uuid
        sensor_uuid = request.GET.get('sensor_uuid', '')
        if len(sensor_uuid) != 0:
            data = db.get_sensor_detail(sensor_uuid=sensor_uuid)
            if data != None:
                # Pop the _id
                data.pop('_id',None)
                # return the result
                response_data = rg.data_response_generator(data)
                return HttpResponse(json.dumps(response_data), content_type="application/json",
                                    status=200)
            else:
                response_data = rg.error_response_generator(400, "Invalid Sensor UUID")
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
        else:
            response_data = rg.error_response_generator(400, "Please specify the Sensor UUID")
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)




