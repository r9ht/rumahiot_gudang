# This section provide Sidik authentication methods for RumahIoT services
import requests

from rumahiot_gudang.settings import SIDIK_TOKEN_VALIDATION_ENDPOINT


class GudangSidikModule:
    # validate jwt token using Sidik service and return user uuid if the token is valid
    # input parameter : token (string)
    # return :  data['user_uuid'] = user_uuid, when the token is valid (string)
    #           data['error'] = None, when the token is valid (string)
    #           data['user_uuid'] = None, when the token is invalid or expired
    #           data['error'] = Error, message when the token is invalid (string)
    # data = {
    #     'user_uuid' : user_uuid(string),
    #     'error' : error(string)
    # }

    def get_user_data(self, token):
        data = {}
        # define the auth payload
        payload = {
            'token': token,
            'email': '0'
        }
        response = requests.post(SIDIK_TOKEN_VALIDATION_ENDPOINT, data=payload)
        # check if the request success
        if response.status_code == 200:
            # return the user uuid
            data['user_uuid'] = response.json()['data']['payload']['user_uuid']
            data['error'] = None
            return data
        else:
            # return the error
            data['user_uuid'] = None
            data['error'] = response.json()['error']['message']
            return data
