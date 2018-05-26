from django import forms

class ExportXlsxDeviceDataForm(forms.Form):
    device_uuid = forms.CharField(required=True, max_length=32)
    time_zone = forms.CharField(required=True, max_length=32)
    to_time = forms.CharField(required=True, max_length=32)
    from_time = forms.CharField(required=True, max_length=32)

