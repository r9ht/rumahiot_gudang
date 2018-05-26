import boto3
from rumahiot_gudang.settings import RUMAHIOT_REGION

class GudangS3:
    # todo : add target bucket to initialization
    def __init__(self):
        self.client = boto3.client('s3', region_name=RUMAHIOT_REGION)

    # S3 put object
    def put_object(self, target_bucket, target_file, object_body):
        # please catch the exception in the view so the service wont stop working when something bad happened
        self.client.put_object(Bucket=target_bucket, Key=target_file, Body=object_body, ACL='public-read')
