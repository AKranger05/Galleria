import boto3
import os
import uuid
import urllib.parse
from datetime import datetime, timezone

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

THUMBNAIL_BUCKET = os.environ['THUMBNAIL_BUCKET']
TABLE_NAME = os.environ['TABLE_NAME']

def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)

    for record in event['Records']:
        source_bucket = record['s3']['bucket']['name']
        source_key = urllib.parse.unquote_plus(record['s3']['object']['key'])

        # Expect uploads stored as: userId/filename.jpg
        parts = source_key.split('/')
        if len(parts) >= 2:
            user_id = parts[0]
            filename = parts[1]
        else:
            user_id = "unknown"
            filename = source_key

        # Copy the image to the thumbnail bucket
        copy_source = {'Bucket': source_bucket, 'Key': source_key}
        s3.copy_object(
            CopySource=copy_source,
            Bucket=THUMBNAIL_BUCKET,
            Key=source_key
        )

        original_url = f"https://{source_bucket}.s3.amazonaws.com/{source_key}"
        thumbnail_url = f"https://{THUMBNAIL_BUCKET}.s3.amazonaws.com/{source_key}"

        image_id = str(uuid.uuid4())
        table.put_item(
            Item={
                'imageId': image_id,
                'userId': user_id,
                'filename': filename,
                'uploadDate': datetime.now(timezone.utc).isoformat(),
                'originalUrl': original_url,
                'thumbnailUrl': thumbnail_url
            }
        )

    return {
        'statusCode': 200,
        'body': 'Processed successfully'
    }
