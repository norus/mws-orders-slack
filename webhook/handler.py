import requests
import logging
import os
import boto3
import json

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']
WEBHOOK_URL = os.environ['WEBHOOK_URL']

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)


def slack_notification(url, data):
    """
    Runs the Slack webhook
    """
    return requests.post(url, data=json.dumps({
        'text': 'New order for {} x {} ({})'.format(
            data['order_qty'],
            data['asin'],
            data['order_id'])
        }),
        headers={'Content-Type': 'application/json'}
    )


def main(event, context):
    """
    Calls the Slack webhook
    """
    for record in event['Records']:
        if record['eventName'] == 'INSERT':

            logger.info('INFO: got a new order!')

            change_set = record['dynamodb']['NewImage']
            payload = {
                'order_id': change_set['order_id']['S'],
                'asin': change_set['product_asin']['S'],
                'order_qty': change_set['order_qty']['N'],
            }

            logger.info('INFO: payload: {}'.format(payload))

            # post to slack
            req = slack_notification(WEBHOOK_URL, payload)

            if req.status_code == 200:
                logger.info('INFO: POST to {} was successful!'.format(WEBHOOK_URL))
                table.update_item(
                    Key={
                        'order_id': change_set['order_id']['S']
                    },
                    UpdateExpression="set notified = :n",
                    ExpressionAttributeValues={
                            ':n': True,
                    },
                    ReturnValues="UPDATED_NEW"
                )
            else:
                table.update_item(
                    Key={
                        'order_id': change_set['order_id']['S']
                    },
                    UpdateExpression="set failed = :f",
                    ExpressionAttributeValues={
                            ':f': True,
                    },
                    ReturnValues="UPDATED_NEW"
                )
                logger.error('ERROR: got {}'.format(req.status_code))
