from flask import Flask, request, jsonify
import os
import stripe
import jwt
from pymongo import MongoClient
from bson.objectid import ObjectId
from shared.utils import publish_to_queue

app = Flask(__name__)

stripe.api_key = os.getenv('STRIPE_SECRET')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client['openleaf_db']
users = db['users']

PRICE_BASIC = os.getenv('STRIPE_PRICE_BASIC')
PRICE_PREMIUM = os.getenv('STRIPE_PRICE_PREMIUM')

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        data = request.json
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        try:
            decoded = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
            user_id = decoded['user_id']
        except:
            return jsonify({'error': 'Invalid token'}), 401
        tier = data.get('tier')  # 'basic' or 'premium'

        if tier not in ['basic', 'premium']:
            return jsonify({'error': 'Invalid tier'}), 400
        if not PRICE_BASIC or not PRICE_PREMIUM:
            return jsonify({'error': 'Stripe price IDs are not configured'}), 500

        price_id = PRICE_BASIC if tier == 'basic' else PRICE_PREMIUM

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='http://localhost:3000/subscriptions/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://localhost:3000/subscriptions/cancel',
            client_reference_id=user_id,  # Pass user_id for webhook matching
            metadata={'tier': tier}
        )

        return jsonify({'id': session.id})
    except Exception as e:
        return jsonify(error=str(e)), 403

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400

    # Return 200 immediately (best practice) - process async if heavy
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('client_reference_id')
        tier = session['metadata'].get('tier')

        if user_id and tier:
            users.update_one(
                {'_id': ObjectId(user_id)},
                {'$addToSet': {'subscriptions': tier},
                 '$set': {'stripe_customer_id': session['customer'],
                          'stripe_subscription_id': session['subscription']}}
            )
            publish_to_queue('subscription_confirmed', {
                'user_id': user_id,
                'tier': tier,
                'subscription_id': session['subscription']
            })

    elif event['type'] == 'customer.subscription.deleted':
        sub = event['data']['object']
        user = users.find_one({'stripe_subscription_id': sub['id']})
        if user:
            users.update_one(
                {'_id': user['_id']},
                {'$pull': {'subscriptions': {'$in': ['basic', 'premium']}}}
            )
            publish_to_queue('subscription_cancelled', {'user_id': str(user['_id'])})

    # Handle other events: invoice.payment_succeeded (renewal), payment_failed, etc.
    # For now, basic handling

    return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=False)
