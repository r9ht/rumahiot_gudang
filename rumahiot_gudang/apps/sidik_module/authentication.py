# Sidik module that used in gudang service
from rumahiot_gudang.settings import RUMAHIOT_SIDIK_API_KEY,RUMAHIOT_SIDIK_GET_EMAIL_ENDPOINT
import requests

class GudangSidikModule:
    # Get email address for sending notification using user_uuid
    # Using Sidik Service
    def get_email_address(self, user_uuid):
        # define the auth header
        header = {
            'Authorization': 'Bearer {}'.format(RUMAHIOT_SIDIK_API_KEY)
        }
        # Data payload
        payload = {
            'user_uuid': user_uuid
        }
        user = requests.post(url=RUMAHIOT_SIDIK_GET_EMAIL_ENDPOINT,headers=header, data=payload)
        return user


