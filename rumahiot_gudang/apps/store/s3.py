import boto3, json
from rumahiot_gudang.settings import RUMAHIOT_REGION, RUMAHIOT_UPLOAD_BUCKET
from rumahiot_gudang.apps.store.mongodb import GudangMongoDB


class GudangS3:
    # todo : add target bucket to initialization
    def __init__(self):
        self.client = boto3.client('s3', region_name=RUMAHIOT_REGION)

    # S3 put object
    def put_object(self, target_bucket, target_file, object_body):
        # please catch the exception in the view so the service wont stop working when something bad happened
        self.client.put_object(Bucket=target_bucket, Key=target_file, Body=object_body, ACL='public-read')

    def get_object(self, target_bucket, target_file):
        return self.client.get_object(Bucket=target_bucket, Key=target_file)

    # Get the latest gampang code in string format
    def get_latest_gampang_template_string(self, supported_board_uuid):
        db = GudangMongoDB()
        latest_template_document = db.get_latest_gampang_template_document(supported_board_uuid=supported_board_uuid)
        # Get the code object from s3
        code_object = self.get_object(target_bucket=RUMAHIOT_UPLOAD_BUCKET, target_file=latest_template_document['s3_path'])
        return code_object['Body'].read().decode('utf-8')


