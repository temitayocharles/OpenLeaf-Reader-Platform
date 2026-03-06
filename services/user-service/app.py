from flask import Flask, request, jsonify
import os, jwt
from pymongo import MongoClient
from bson.objectid import ObjectId
import pika, json
from shared.utils import publish_to_queue  # Assume shared module

app = Flask(__name__)
client = MongoClient(os.getenv('MONGO_URI'))
db = client['openleaf_db']
users = db['users']

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if users.find_one({'email': data['email']}):
        return jsonify({'error': 'User exists'}), 409
    user_id = users.insert_one({'email': data['email'], 'password': data['password'],  # Hash in prod!
                                'progress': {}, 'subscriptions': []}).inserted_id
    return jsonify({'user_id': str(user_id)}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = users.find_one({'email': data['email'], 'password': data['password']})
    if user:
        token = jwt.encode({'user_id': str(user['_id'])}, os.getenv('JWT_SECRET'), algorithm='HS256')
        return jsonify({'token': token})
    return jsonify({'error': 'Invalid'}), 401

@app.route('/progress/<book_id>', methods=['POST'])
def update_progress(book_id):
    token = request.headers.get('Authorization').split()[1] if ' ' in request.headers.get('Authorization', '') else request.headers.get('Authorization')
    try:
        user_id = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])['user_id']
        data = request.json
        users.update_one({'_id': ObjectId(user_id)}, {'$set': {f'progress.{book_id}': data['page']}})
        publish_to_queue('progress_sync', {'user_id': user_id, 'book_id': book_id, 'page': data['page']})
        return jsonify({'status': 'updated'})
    except:
        return jsonify({'error': 'Unauthorized'}), 401

# Add more: /profile GET

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
