from flask import Flask, request, jsonify
import requests
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import jwt

app = Flask(__name__)
client = MongoClient(os.getenv('MONGO_URI'))
db = client['openleaf_db']
users = db['users']

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/subscriptions', methods=['POST'])
def create_sub():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized'}), 401

    token = auth_header.split(' ')[1]
    try:
        decoded = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
        user_id = decoded['user_id']
    except:
        return jsonify({'error': 'Invalid token'}), 401

    data = request.json
    tier = data.get('tier')
    if tier not in ['basic', 'premium']:
        return jsonify({'error': 'Invalid tier'}), 400

    # Forward to payment service (internal call via cluster DNS)
    try:
        resp = requests.post(
            'http://payment-service:5005/create-checkout-session',
            json={'tier': tier, 'user_id': str(user_id)},
            headers={'Authorization': f'Bearer {token}'},  # Forward token
            timeout=10
        )
        resp.raise_for_status()
        return jsonify(resp.json()), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Payment service error: {str(e)}'}), 502

@app.route('/subscriptions', methods=['GET'])
def get_subscriptions():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized'}), 401

    token = auth_header.split(' ')[1]
    try:
        decoded = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
        user_id = decoded['user_id']
    except:
        return jsonify({'error': 'Invalid token'}), 401

    user = users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'subscriptions': user.get('subscriptions', []),
        'stripe_customer_id': user.get('stripe_customer_id')
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=False)
