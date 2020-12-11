# MWS Orders Notifications

Receive Slack notifications when you get new orders on Amazon marketplaces.

Based on [Serverless](https://serverless.com) and uses Python 3.8

The entire stack can be hosted using the AWS free tier (Always Free offer) unless you exceed the limits but it's
 pretty hard to do so 😅
* **Lambda** (used to connect to MWS and call the Slack webhook)
* **EventBridge** (used to schedule Lambda to periodically check MWS)
* **DynamoDB** (used to store order data retrieved from MWS)
* **Systems Manager** (used to store MWS credentials and Slack webhook URL)

## Lambdas
#### orders/handler.py

Connects to MWS and retrieves new orders. Scheduled to run every 5 minutes.

#### webhook/handler.py

Invoked on new DynamoDB events and calls the Slack webhook when *INSERT* is detected.  
Also updates the corresponding DB entry with *notified: true* or *failed: true* on Slack webhook POST failure.

## Table structure
```
Partition key: order_id  
Sort key: -

- order_id: String [S]  
- purchase_date: String [S]  
- product_asin: String [S]  
- order_qty: Number [N]  
- order: Map  
- order_items: Map  
- notified: Boolean [BOOL]  
- failed: Boolean [BOOL]
```
 
## Prerequisites
1. Get your MWS credentials https://docs.developer.amazonservices.com/en_US/dev_guide/DG_Registering.html  
    *Example:*  
    `SELLER_ID: A3XXXXXXXXXXFF`  
    `ACCESS_KEY: AKXXXXXXXXXXXXXXXXRQ`  
    `SECRET_KEY: ShT7XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXEqm`
    
2. Get the marketplaces/regions you sell in https://docs.developer.amazonservices.com/en_US/dev_guide/DG_Endpoints.html  
    *Example:*  
    `US: ATVPDKIKX0DER`  
    `CA: A2EUQ1WTGCTBG2`
3. Get your incoming webhook https://slack.com/apps/A0F7XDUAZ-incoming-webhooks  
    *Example:*  
    `https://hooks.slack.com/services/XXXXXXXXX/XXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXX`
    
## Installation

1. Install *serverless* https://www.serverless.com/framework/docs/getting-started
2. Add your MWS credentials and Slack webhook (from *Prerequisites, Step 1 & 2*) in *Systems Manager -> Parameter
 Store*  
![Systems Manager](https://github.com/norus/mws-orders-slack/raw/master/systems_manager.png)  
3. Customize regions in *serverless.yml* under *MWS_MARKET_ID* (should be a list!) from *Prerequisites, Step 2*
4. Customize AWS region in *serverless.yml* under *region* (default is *us-east-1*)
4. Deploy the stack by running `serverless deploy`
5. Enjoy your notifications in Slack 🎉  
<img src="https://github.com/norus/mws-orders-slack/raw/master/slack_notification.png" width="350">
