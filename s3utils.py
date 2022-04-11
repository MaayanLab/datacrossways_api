import boto3
import json

def get_aws_client(cred):
    s3_client = boto3.client(
        's3',
        region_name=cred["region"],
        aws_access_key_id=cred["aws_id"],
        aws_secret_access_key=cred["aws_key"],
    )
    return s3_client

def sign_get_file(file_name, cred):
    
    s3_client = get_aws_client(cred)

    url = s3_client.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': cred["bucket_name"],
            'Key': file_name,
        },
        ExpiresIn=6000
    )
    return url

def sign_upload_file(file_name, cred):

    s3_client = get_aws_client(cred)

    response = s3_client.generate_presigned_post(cred["bucket_name"],
        file_name,
        Fields=None,
        Conditions=None,
        ExpiresIn=600)

    return response

def start_multipart(filename, cred):
    s3_client = get_aws_client(cred)
    return s3_client.create_multipart_upload(Bucket=cred["bucket_name"], Key=filename)['UploadId']

def sign_multipart(filename, upload_id, part_number, cred):
    s3_client = get_aws_client(cred)
    signed_url = s3_client.generate_presigned_url(
        ClientMethod='upload_part',
        Params={'Bucket': cred['bucket_name'], 
        'Key': filename, 
        'UploadId': upload_id, 
        'PartNumber': part_number})
    return signed_url

def complete_multipart(filename, upload_id, parts, cred):
    s3_client = get_aws_client(cred)
    res = s3_client.complete_multipart_upload(
        Bucket=cred["bucket_name"],
        Key=filename,
        MultipartUpload={'Parts': parts},
        UploadId=upload_id)