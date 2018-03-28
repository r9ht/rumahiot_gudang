from django import forms
from django.utils.translation import ugettext_lazy as _


class EmailLoginForm(forms.Form):
    email = forms.EmailField(required=True, max_length=254)
    password = forms.CharField(required=True, max_length=128)


class UpdateUserSensorDetailForm(forms.Form):
    user_sensor_uuid = forms.CharField(required=True, max_length=128)
    new_threshold = forms.CharField(required=False, max_length=32)
    # "1" for enabled, "0" for disabled
    threshold_enabled = forms.CharField(required=True, max_length=1)
    # 1 for over, -1 for less
    threshold_direction = forms.CharField(required=False, max_length=2)
    new_user_sensor_name = forms.CharField(required=True, max_length=32)

    # Clean and check the data
    def clean(self):
        if 'user_sensor_uuid'in self.cleaned_data and 'threshold_enabled'in self.cleaned_data and 'new_user_sensor_name'in self.cleaned_data:
             # Validate threshold value
             if self.cleaned_data['threshold_enabled'] == "1":
                 # Check if threshold direction and value if the threshold is enabled
                 if 'threshold_direction' in self.cleaned_data and 'new_threshold' in self.cleaned_data:
                     if self.cleaned_data['threshold_direction'] == "-1" or self.cleaned_data[
                         'threshold_direction'] == "1":
                         return self.cleaned_data
                     else:
                         # Invalid threshold direction
                         raise forms.ValidationError(_('Invalid parameter or value submitted'))
                 else:
                     raise forms.ValidationError(_('Invalid parameter or value submitted'))
             elif self.cleaned_data['threshold_enabled'] == "0":
                 return self.cleaned_data
             else:
                 raise forms.ValidationError(_('Invalid parameter or value submitted'))
        else:
            raise forms.ValidationError(_('Invalid parameter or value submitted'))

