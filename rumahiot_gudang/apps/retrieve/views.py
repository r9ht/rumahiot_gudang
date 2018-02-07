from django.shortcuts import render,HttpResponse
import json
from rumahiot_gudang.apps.store.utils import RequestUtils,ResponseGenerator,GudangUtils
from rumahiot_gudang.apps.retrieve.authorization import GudangSidikModule
from rumahiot_gudang.apps.store.mongodb import GudangMongoDB

# Create your views here.

# Retrieve corresponding user device list
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
        # Get the GET request parameter
        page = request.GET.get('p', '1')
        # its ok for query to be empty
        query = request.GET.get('q', '')
        # Per page limit
        limit = request.GET.get('l','10')
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
                user = auth.get_user_uuid(token['token'])
                if user['user_uuid'] != None:
                    # The page and limit result shouldn't empty (e.g. ?p=)
                    # The parameter will be available but empty
                    # Check the page and limit parameter exist and correct data type (int)
                    if page != "" and limit !="" and gutils.integer_check(page) and gutils.integer_check(limit):
                        # -1 so the skip will be matched with the page:
                        # Todo : Warning, skip will be slow at scale
                        skip = (int(page) - 1) * int(limit)
                        results = db.get_user_device_list(user_uuid=user['user_uuid'],skip=skip,limit=int(limit),text=query)
                        # Check if the next page exist
                        # Todo : Find better way to do this
                        next_results = db.get_user_device_list(user_uuid=user['user_uuid'],skip=(int(page) * int(limit)),limit=int(limit),text=query).count(True)
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
                            result.pop('_id', None)
                            result.pop('user_uuid', None)
                            data['results'].append(result)
                        # return the result
                        response_data = rg.data_response_generator(data)
                        return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)
                    else:
                        response_data = rg.error_response_generator(400, "Invalid get parameter value supplied")
                        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
                else:
                    response_data = rg.error_response_generator(400, user['error'])
                    return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
            else:
                response_data = rg.error_response_generator(400, token['error'])
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)





