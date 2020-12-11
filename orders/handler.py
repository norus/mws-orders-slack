from mws import mws
import sys
import os
import logging
import json
import boto3
import botocore
from datetime import datetime, timedelta

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

MWS_ACCESS_KEY = os.environ['MWS_ACCESS_KEY']
MWS_SECRET_KEY = os.environ['MWS_SECRET_KEY']
MWS_SELLER_ID = os.environ['MWS_SELLER_ID']
MWS_REGION = os.environ['MWS_REGION']
MARKETPLACES = os.environ['MWS_MARKET_ID'].split(',')
DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)


def dynamodb_payload(order, order_items):
    """
    Returns a payload for DynamoDB's put_item()
    """
    item = {
        'order_id': order['AmazonOrderId']['value'],
        'purchase_date': order['PurchaseDate']['value'],
        'product_asin': order_items.parsed['OrderItems']['OrderItem']['ASIN']['value'],
        'order_qty': int(order_items.parsed['OrderItems']['OrderItem']['QuantityOrdered']['value']),
        'order': json.loads(json.dumps(order)),
        'order_items': json.loads(json.dumps(order_items.parsed)),
        'notified': False,
        'failed': False
    }
    return item


def main(event, context):
    """
    Checks for new orders
    """
    orders_api = mws.Orders(
        access_key=MWS_ACCESS_KEY,
        secret_key=MWS_SECRET_KEY,
        account_id=MWS_SELLER_ID,
        region=MWS_REGION
    )

    logger.info('INFO: connected to MWS API')

    service_status = orders_api.get_service_status()
    if service_status.parsed.Status != 'GREEN':
        logger.error('ERROR: MWS API looks to be down')
        sys.exit()

    # updated 1 day ago
    today = datetime.now() - timedelta(days=1)
    updated_after = '{}-{:02d}-{:02d}T08:00:00'.format(today.year, today.month, today.day)
    res = orders_api.list_orders(
        marketplaceids=MARKETPLACES,
        lastupdatedafter=updated_after
    )

    # new order/s found
    if len(res.parsed['Orders']) > 0:
        logger.info('INFO: found new order/s')

        # more than one order returns a list of dicts
        if type(res.parsed['Orders']['Order']) is list:
            for order in res.parsed['Orders']['Order']:
                logger.info('INFO: new order {}'.format(order['AmazonOrderId']['value']))
                # ignore cancelled orders
                if order['OrderStatus']['value'] != 'Canceled':
                    order_items = orders_api.list_order_items(amazon_order_id=order['AmazonOrderId']['value'])
                    try:
                        res = table.put_item(
                            Item=dynamodb_payload(order, order_items),
                            ConditionExpression='attribute_not_exists(order_id)'
                        )
                    except botocore.exceptions.ClientError as e:
                        if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
                            logger.info('INFO: order_id already added. Skipping insert...')
        else:
            # just one order returns dict
            order = res.parsed['Orders']['Order']
            logger.info('INFO: new order {}'.format(order['AmazonOrderId']['value']))
            # ignore canceled orders
            if order['OrderStatus']['value'] != 'Canceled':
                order_items = orders_api.list_order_items(amazon_order_id=order['AmazonOrderId']['value'])
                try:
                    table.put_item(
                        Item=dynamodb_payload(order, order_items),
                        ConditionExpression='attribute_not_exists(order_id)'
                    )
                except botocore.exceptions.ClientError as e:
                    if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
                        logger.info('INFO: order_id already added. Skipping insert...')