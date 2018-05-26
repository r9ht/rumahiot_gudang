from xlsxwriter.workbook import Workbook
from rumahiot_gudang.apps.store.mongodb import GudangMongoDB
from rumahiot_gudang.apps.store.utils import GudangUtils
from rumahiot_gudang.apps.store.s3 import GudangS3
from io import BytesIO
import xlsxwriter
import datetime
import timeit
from uuid import uuid4
from zappa.async import task
from rumahiot_gudang.settings import RUMAHIOT_UPLOAD_BUCKET, RUMAHIOT_UPLOAD_ROOT

# Function in here wont be put into an object, as zappa async execution does not have the support for it yet.
@task()
def buffered_xlsxwriter(user_uuid, device_uuid, from_time, to_time, time_zone, user_exported_xlsx_uuid):
    db = GudangMongoDB()
    gutils = GudangUtils()
    gs3 = GudangS3()
    # Prepare the stream
    out = BytesIO()
    workbook = xlsxwriter.Workbook(out)
    # Worksheets for this current device, consists of multiple sheets for each sensor
    worksheets = {}
    user_device = db.get_device_data_by_uuid(user_uuid=user_uuid, device_uuid=device_uuid)
    # Iterate through the sensor
    for index, user_sensor_uuid in enumerate(user_device['user_sensor_uuids']):
        # Start time
        start_time = timeit.default_timer()
        # Get user sensor data
        sensor = db.get_user_sensor_by_uuid(user_sensor_uuid=user_sensor_uuid)
        master_sensor = db.get_master_sensor_by_uuid(master_sensor_uuid=sensor['master_sensor_uuid'])
        master_sensor_reference = db.get_master_sensor_reference_by_uuid(master_sensor_reference_uuid=master_sensor['master_sensor_reference_uuid'])
        # Add the worksheet
        worksheets[user_sensor_uuid] = workbook.add_worksheet('Sensor {} data'.format(index + 1))
        # Widen the A and B and C column
        worksheets[user_sensor_uuid].set_column('A:A', 10)
        worksheets[user_sensor_uuid].set_column('B:B', 40)
        worksheets[user_sensor_uuid].set_column('C:C', 20)
        worksheets[user_sensor_uuid].set_column('D:D', 20)
        worksheets[user_sensor_uuid].set_column('E:E', 40)

        # Add rumahiot logo
        worksheets[user_sensor_uuid].insert_image('A1', 'rumahiot_gudang/apps/store/xlsxwriter_data/rumahiot-logo.png', {'x_scale': 0.49999999, 'y_scale': 0.49999999, 'y_offset': 30, 'x_offset': 150})
        # Logo merge format
        logo_merge_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bold': 1,
        })
        center_text_format = workbook.add_format({
            'align': 'center',
            'border': 1,
        })
        left_text_format = workbook.add_format({
            'align': 'left',
            'border': 1,
        })
        # Merge 'Sensor Data' Cell
        worksheets[user_sensor_uuid].merge_range('A10:C10', 'Device Data', logo_merge_format)
        # Bold format
        bold = workbook.add_format({'bold': True})
        # Merge the logo cell
        worksheets[user_sensor_uuid].merge_range('A1:C9', '', logo_merge_format)

        # Date format
        date_format = "%d-%m-%Y %H:%M:%S %Z%z"

        # Write file information
        worksheets[user_sensor_uuid].write('D1', 'Device Name', bold)
        worksheets[user_sensor_uuid].write('D2', 'Time to Generate', bold)
        worksheets[user_sensor_uuid].write('D3', 'Sensor Model', bold)
        worksheets[user_sensor_uuid].write('D4', 'Sensor Name', bold)
        worksheets[user_sensor_uuid].write('D5', 'Value Type', bold)
        worksheets[user_sensor_uuid].write('D6', 'From', bold)
        worksheets[user_sensor_uuid].write('D7', 'To', bold)
        worksheets[user_sensor_uuid].write('D8', 'Timezone', bold)
        worksheets[user_sensor_uuid].write('D9', 'Generated At', bold)

        worksheets[user_sensor_uuid].write('E1', user_device['device_name'])
        # Add time to generate later
        worksheets[user_sensor_uuid].write('E3', master_sensor_reference['sensor_model'])
        worksheets[user_sensor_uuid].write('E4', sensor['user_sensor_name'])
        worksheets[user_sensor_uuid].write('E5', '{}, {}({})'.format(master_sensor['master_sensor_name'], master_sensor['master_sensor_default_unit_name'],
                                                                     master_sensor['master_sensor_default_unit_symbol']))
        worksheets[user_sensor_uuid].write('E6', gutils.datetime_timezone_converter(datetime.datetime.fromtimestamp(from_time), time_zone).strftime(date_format))
        worksheets[user_sensor_uuid].write('E7', gutils.datetime_timezone_converter(datetime.datetime.fromtimestamp(to_time), time_zone).strftime(date_format))
        worksheets[user_sensor_uuid].write('E8', time_zone)
        worksheets[user_sensor_uuid].write('E9', gutils.datetime_timezone_converter(datetime.datetime.now(), time_zone).strftime(date_format))
        worksheets[user_sensor_uuid].write('A11', 'No.', center_text_format)
        worksheets[user_sensor_uuid].write('B11', 'Time', center_text_format)
        worksheets[user_sensor_uuid].write('C11', 'Sensor Value', center_text_format)

        # Get the sensor data
        sensor_datas = db.get_device_sensor_data_interval(device_uuid=user_device['device_uuid'], from_time=from_time, to_time=to_time, user_sensor_uuid=user_sensor_uuid)

        # Iterate through the data
        row_index = 11
        column_index = 0
        for index, sensor_data in enumerate(sensor_datas):
            worksheets[user_sensor_uuid].write(row_index, column_index, index + 1, left_text_format)
            worksheets[user_sensor_uuid].write(row_index, column_index + 1, gutils.datetime_timezone_converter(datetime.datetime.fromtimestamp(sensor_data['time_added']), time_zone).strftime(date_format),
                                               left_text_format)
            worksheets[user_sensor_uuid].write(row_index, column_index + 2, '{}{}'.format(sensor_data['sensor_datas']['user_sensor_value'], master_sensor['master_sensor_default_unit_symbol']),
                                               center_text_format)
            row_index += 1

        finish_time = timeit.default_timer() - start_time
        # Write time to generate
        worksheets[user_sensor_uuid].write('E2', '{} seconds'.format(finish_time))

    # Close the workbook
    workbook.close()
    # Start the stream from 0
    out.seek(0)
    # put the document into s3
    target_file = 'docs/xlsx/{}/{}.xlsx'.format(user_uuid, uuid4().hex)
    gs3.put_object(target_bucket=RUMAHIOT_UPLOAD_BUCKET, target_file=target_file, object_body=out.read())
    # Close the stream
    out.close()
    # Update db after document is ready
    db.update_user_exported_xlsx(user_exported_xlsx_uuid=user_exported_xlsx_uuid, document_link=RUMAHIOT_UPLOAD_ROOT + target_file)
    # Finished

