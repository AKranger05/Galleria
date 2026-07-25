import boto3
import json
import os

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

UPLOAD_BUCKET = os.environ['UPLOAD_BUCKET']
THUMBNAIL_BUCKET = os.environ['THUMBNAIL_BUCKET']
TABLE_NAME = os.environ['TABLE_NAME']

def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)

    # Get userId from the Cognito authorizer claims
    claims = event['requestContext']['authorizer']['claims']
    user_id = claims['sub']

    # Get imageId from the URL path
    image_id = event['pathParameters']['id']

    # Fetch the item first to confirm it belongs to this user
    response = table.get_item(Key={'imageId': image_id})
    item = response.get('Item')

    if not item:
        return {
            'statusCode': 404,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Image not found'})
        }

    if item['userId'] != user_id:
        return {
            'statusCode': 403,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Not authorized to delete this image'})
        }

    # Extract the S3 key from userId/filename structure
    s3_key = f"{item['userId']}/{item['filename']}"

    # Delete from both S3 buckets
    s3.delete_object(Bucket=UPLOAD_BUCKET, Key=s3_key)
    s3.delete_object(Bucket=THUMBNAIL_BUCKET, Key=s3_key)

    # Delete from DynamoDB
    table.delete_item(Key={'imageId': image_id})

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'message': 'Deleted successfully'})
    }
