import boto3
import json
import os
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
TABLE_NAME = os.environ['TABLE_NAME']
THUMBNAIL_BUCKET = os.environ['THUMBNAIL_BUCKET']
UPLOAD_BUCKET = os.environ['UPLOAD_BUCKET']

def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)

    # Get userId from the Cognito authorizer claims
    claims = event['requestContext']['authorizer']['claims']
    user_id = claims['sub']

    # Scan and filter by userId (fine for small projects)
    response = table.scan(
        FilterExpression=Key('userId').eq(user_id)
    )

    items = response.get('Items', [])

    # Generate temporary signed URLs so private bucket objects can be viewed
    for item in items:
        key = f"{item['userId']}/{item['filename']}"

        item['thumbnailUrl'] = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': THUMBNAIL_BUCKET, 'Key': key},
            ExpiresIn=3600
        )
        item['originalUrl'] = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': UPLOAD_BUCKET, 'Key': key},
            ExpiresIn=3600
        )

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(items)
    }
