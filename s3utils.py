import boto3
import json
import app
from botocore.config import Config
from datetime import datetime, timezone, timedelta

def delete_file(file_uuid, file_name):
    print(file_uuid)
    print(file_name)
    s3_client = get_aws_client(app.conf["aws"])
    s3_client.delete_objects(
        Bucket=app.conf["aws"]["bucket"],
        Delete={
            'Objects': [
                {
                    'Key': file_uuid+"/"+file_name
                }
            ],
            'Quiet': True
        }
    )

def get_aws_client(cred):
    addressing_style = cred.get("addressing_style", "auto")
    if addressing_style not in {"auto", "path", "virtual"}:
        raise ValueError("S3 addressing style must be auto, path, or virtual")
    client_options = {
        "region_name": cred.get("region") or "us-east-1",
        "config": Config(s3={"addressing_style": addressing_style}),
    }
    if cred.get("endpoint_url"):
        client_options["endpoint_url"] = cred["endpoint_url"]
    if cred.get("aws_id"):
        client_options["aws_access_key_id"] = cred["aws_id"]
    if cred.get("aws_key"):
        client_options["aws_secret_access_key"] = cred["aws_key"]
    s3_client = boto3.client('s3', **client_options)
    return s3_client

def sign_get_file(file_name, cred):
    
    s3_client = get_aws_client(cred)

    url = s3_client.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': cred["bucket"],
            'Key': file_name,
        },
        ExpiresIn=60*60
    )
    return url

def sign_upload_file(file_name, cred, max_size):

    s3_client = get_aws_client(cred)

    response = s3_client.generate_presigned_post(cred["bucket"],
        file_name,
        Fields={},
        Conditions=[["content-length-range", 1, int(max_size)]],
        ExpiresIn=600)

    return response

def start_multipart(filename, cred):
    s3_client = get_aws_client(cred)
    return s3_client.create_multipart_upload(Bucket=cred["bucket"], Key=filename)['UploadId']

def sign_multipart(filename, upload_id, part_number, content_length, cred):
    s3_client = get_aws_client(cred)
    signed_url = s3_client.generate_presigned_url(
        ClientMethod='upload_part',
        Params={'Bucket': cred['bucket'], 
        'Key': filename, 
        'UploadId': upload_id, 
        'PartNumber': part_number,
        'ContentLength': content_length},
        ExpiresIn=600)
    return signed_url

def abort_stale_multipart_uploads(cred, max_age_hours=24):
    """Abort incomplete uploads after a bounded retention window."""
    if not cred.get("bucket"):
        return 0
    client = get_aws_client(cred)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    aborted = 0
    paginator = client.get_paginator("list_multipart_uploads")
    for page in paginator.paginate(Bucket=cred["bucket"]):
        for upload in page.get("Uploads", []):
            initiated = upload.get("Initiated")
            if initiated and initiated < cutoff:
                client.abort_multipart_upload(
                    Bucket=cred["bucket"], Key=upload["Key"], UploadId=upload["UploadId"])
                aborted += 1
    return aborted

def complete_multipart(filename, upload_id, parts, cred):
    s3_client = get_aws_client(cred)
    res = s3_client.complete_multipart_upload(
        Bucket=cred["bucket"],
        Key=filename,
        MultipartUpload={'Parts': parts},
        UploadId=upload_id)

def get_file_size(filename, cred):
    s3_client = get_aws_client(cred)
    response = s3_client.head_object(Bucket=cred["bucket"], Key=filename)
    return response['ContentLength']

def get_file_checksum(filename):
    s3_client = get_aws_client(app.conf["aws"])
    response = s3_client.head_object(Bucket=app.conf["aws"]["bucket"], Key=filename)
    return response['Metadata'].get("checksum")
