import boto3
import json
import os
import uuid

s3 = boto3.client('s3')
UPLOAD_BUCKET = os.environ['UPLOAD_BUCKET']

def lambda_handler(event, context):
    # Get userId from the Cognito authorizer claims
    claims = event['requestContext']['authorizer']['claims']
    user_id = claims['sub']

    # Get filename from query string
    query_params = event.get('queryStringParameters') or {}
    filename = query_params.get('filename', f"{uuid.uuid4()}.jpg")

    # Build the S3 key: userId/filename
    key = f"{user_id}/{filename}"

    # Generate pre-signed URL valid for 5 minutes
    presigned_url = s3.generate_presigned_url(
        'put_object',
        Params={'Bucket': UPLOAD_BUCKET, 'Key': key},
        ExpiresIn=300
    )

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'uploadUrl': presigned_url, 'key': key})
    }
