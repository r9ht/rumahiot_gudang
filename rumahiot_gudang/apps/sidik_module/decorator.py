import json

from django.shortcuts import HttpResponse

from rumahiot_gudang.apps.sidik_module.authorization import GudangSidikModule
from rumahiot_gudang.apps.store.mongodb import GudangMongoDB
from rumahiot_gudang.apps.store.utils import RequestUtils, ResponseGenerator, GudangUtils

# Decorator to make sure the request method is post
def post_method_required(function):

    def post_check(request, *args, **kwargs):
        # Gudang class
        rg = ResponseGenerator()

        if request.method == "POST" :
            return function(request, *args, **kwargs)
        else:
            response_data = rg.error_response_generator(400, 'Bad request method')
            return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)
    post_check.__doc__ = function.__doc__
    post_check.__name__ = function.__name__
    
    return post_check


# Decorator to make sure the request method is post
def get_method_required(function):
    def get_check(request, *args, **kwargs):
        # Gudang class
        rg = ResponseGenerator()

        if request.method == "GET":
            return function(request, *args, **kwargs)
        else:
            response_data = rg.error_response_generator(400, 'Bad request method')
            return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

    get_check.__doc__ = function.__doc__
    get_check.__name__ = function.__name__

    return get_check


# Decorator to make sure user is authenticated
def authentication_required(function):

    def token_check(request, *args, **kwargs):

        requtils = RequestUtils()
        auth = GudangSidikModule()
        rg = ResponseGenerator()

        # Check the token
        try:
            token = requtils.get_access_token(request)
        except KeyError:
            response_data = rg.error_response_generator(1, 'Please define the authorization header')
            return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)
        else:
            if token['token'] != None:
                user = auth.get_user_data(token['token'])
                # Check token validity
                if user['user_uuid'] != None:
                    # Return the user object too
                    return function(request, user, *args, **kwargs)
                else:
                    response_data = rg.error_response_generator(1, user['error'])
                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)
            else:
                response_data = rg.error_response_generator(1, token['error'])
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=401)

    token_check.__doc__ = function.__doc__
    token_check.__name__ = function.__name__

    return token_check

# Decorator to make sure admin is authenticated
def admin_authentication_required(function):

    def token_check(request, *args, **kwargs):

        requtils = RequestUtils()
        auth = GudangSidikModule()
        rg = ResponseGenerator()

        # Check the token
        try:
            token = requtils.get_access_token(request)
        except KeyError:
            response_data = rg.error_response_generator(2, 'Please define the authorization header')
            return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)
        else:
            if token['token'] != None:
                user = auth.get_admin_data(token['token'])
                # Check token validity
                if user['user_uuid'] != None:
                    # Return the user object too
                    return function(request, user, *args, **kwargs)
                else:
                    response_data = rg.error_response_generator(2, user['error'])
                    return HttpResponse(json.dumps(response_data), content_type='application/json', status=401)
            else:
                response_data = rg.error_response_generator(2, token['error'])
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=401)

    token_check.__doc__ = function.__doc__
    token_check.__name__ = function.__name__

    return token_check