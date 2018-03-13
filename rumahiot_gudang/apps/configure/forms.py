from django import forms

from django.utils.translation import ugettext_lazy as _

class EmailLoginForm(forms.Form):
    email = forms.EmailField(required=True,max_length=254)
    password = forms.CharField(required=True,max_length=128)

class UpdateDeviceSensorThresholdForm(forms.Form):
    device_uuid = forms.CharField(required=True,max_length=128)
    sensor_uuid = forms.CharField(required=True,max_length=128)
    new_threshold = forms.CharField(required=True,max_length=32)

