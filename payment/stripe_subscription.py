from flask import Flask, render_template, request, jsonify, Blueprint
import stripe
from dotenv import load_dotenv
import os
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from config import user_table, Topics_table, message_table  
from stripe.error import SignatureVerificationError
from datetime import datetime, timedelta
import botocore.exceptions


payments_blueprint = Blueprint('payments', __name__)

load_dotenv()

# Set your secret key. Remember to switch to your live secret key in production!
stripe.api_key = os.environ.get("secret_key")
stripe_webhook_secret = os.environ.get('webhook_secret')


@payments_blueprint.route('/v1/create-checkout-session', methods=['POST'])
@jwt_required()
def create_checkout_session():
    data = request.json
    current_user_email = get_jwt_identity()
    response = user_table.get_item(Key={'email': current_user_email})
    if 'Item' not in response:
        return jsonify({"error": "User not found"}), 404
    user = response['Item']
    if user.get('subscribed', {}).get('state', False):
        return jsonify({"message": "User is already subscribed"}), 400
    
    # Check if the 'active_checkout_session' is present and if 'session_id' is set
    if not user.get('active_checkout_session'):
        print('I am here')
        user_table.update_item(
            Key={'email': current_user_email},
            UpdateExpression="SET active_checkout_session = if_not_exists(active_checkout_session, :empty_map)",
            ExpressionAttributeValues={
                ':empty_map': {}
            }
        )
        

        user_table.update_item(
            Key={'email': current_user_email},
            UpdateExpression="SET active_checkout_session.session_id = :val, #ts = :time",
            ExpressionAttributeValues={
                ':val': None,  # No active session yet
                ':time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            },
            ExpressionAttributeNames={
                "#ts": "active_checkout_session.timestamp"
            }
        )
        response = user_table.get_item(Key={'email': current_user_email})
        user = response['Item']

    default_url = 'https://vocoverse.com'
    success_url = data.get('success_url', default_url)  
    cancel_url = data.get('cancel_url', default_url)
    if not success_url.startswith(('http://', 'https://')):
        success_url = 'https://' + success_url
    if not cancel_url.startswith(('http://', 'https://')):
        cancel_url = 'https://' + cancel_url
    
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user_email,  # This associates the email with the checkout session.
            line_items=[
                {
                    'price': os.environ.get("price_id"),
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
        )


        # Once the session is successfully created, update 'active_checkout_session_id' for the user
        current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        user_table.update_item(
            Key={'email': current_user_email},
            UpdateExpression="SET active_checkout_session.session_id = :val, #ts = :time",
            ExpressionAttributeValues={
                ':val': checkout_session.id,
                ':time': current_time
            },
            ExpressionAttributeNames={
                "#ts": "active_checkout_session.timestamp"
            }
        )


        return jsonify({'url': checkout_session.url})
    except Exception as e:
        return jsonify(error=str(e)), 500



@payments_blueprint.route('/v1/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    # Verify the signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_webhook_secret
        )
    except SignatureVerificationError:
        return jsonify({'message': 'Invalid payload or signature'}), 400


    subscription_id = event['data']['object'].get('id')
    customer_id = event['data']['object'].get('customer')

    # Retrieve the customer's email using the customer ID
    email = None
    if customer_id:
        try:
            customer = stripe.Customer.retrieve(customer_id)
            email = customer.email
        except Exception as e:
            # Handle exceptions, such as network issues, rate limits, etc.
            print(f"Error fetching email for customer {customer_id}: {e}")

    # Handle the event

    if event['type'] == 'customer.subscription.created':
        
        # Retrieve the item
        response = user_table.get_item(Key={'email': email})
        item = response.get('Item', {})

        # Check if 'subscribed' attribute exists
        if 'subscribed' in item:
            # If 'subscribed' exists, update nested attributes inside it
            user_table.update_item(
                Key={'email': email},
                UpdateExpression="SET active_checkout_session.session_id = :session_val, #ts = :time_val, subscribed.#state_attr = :sub_state, subscribed.id = :sub_id, subscribed.stripe_id = :stripe_id_val",
                ExpressionAttributeValues={
                    ':session_val': None,
                    ':time_val': None,
                    ':sub_state': True,
                    ':sub_id': subscription_id,
                    ':stripe_id_val': customer_id
                },
                ExpressionAttributeNames={
                    "#ts": "active_checkout_session.timestamp",
                    "#state_attr": "state"
                }
            )
        else:
            # If 'subscribed' doesn't exist, initialize it
            subscribed_map = {
                'state': True,
                'id': subscription_id,
                'stripe_id': customer_id
            }
            user_table.update_item(
                Key={'email': email},
                UpdateExpression="SET active_checkout_session.session_id = :session_val, #ts = :time_val, subscribed = :subscribed_map",
                ExpressionAttributeValues={
                    ':session_val': None,
                    ':time_val': None,
                    ':subscribed_map': subscribed_map
                },
                ExpressionAttributeNames={
                    "#ts": "active_checkout_session.timestamp"
                }
            )


    elif event['type'] == 'customer.subscription.deleted':
        # Explicitly set the 'subscribed' attribute to False
        user_table.update_item(
            Key={'email': email},
            UpdateExpression="SET active_checkout_session.session_id = :session_val, #ts = :time_val, subscribed.#state_attr = :sub_state, subscribed.id = :null_val",
            ExpressionAttributeValues={
                ':session_val': None,
                ':time_val': None,
                ':sub_state': False,
                ':null_val': None
            },
            ExpressionAttributeNames={
                "#ts": "active_checkout_session.timestamp",
                "#state_attr": "state"  # Alias for the 'state' attribute
            }
        )



    else:
        # Unexpected event type
        return jsonify({'message': 'Unhandled event type'}), 400

    # Return a success response
    return jsonify({'status': 'success'})



@payments_blueprint.route('/v1/manage-subscription', methods=['POST'])
@jwt_required()
def manage_subscription():
    current_user_email = get_jwt_identity()
    data = request.json

    # Fetch the user record from DynamoDB using the current_user_email
    response = user_table.get_item(Key={'email': current_user_email})

    # Check if user is found and has a stripe_id
    if 'Item' not in response or not response['Item'].get('subscribed', {}).get('stripe_id'):
        return jsonify({'message': 'User not found or user is not a Stripe customer'}), 404

    stripe_customer_id = response['Item']['subscribed']['stripe_id']
    default_url = 'https://vocoverse.com'
    return_url = data.get('return_url', default_url)

    # Ensure that the return_url starts with http:// or https://
    if not return_url.startswith(('http://', 'https://')):
        return_url = 'https://' + return_url


    # Create a session for the Stripe Customer Portal
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=return_url  # Use the dynamically provided URL
    )

    # Return the session URL in the response instead of redirecting
    return jsonify({'session_url': session.url}), 200









    
