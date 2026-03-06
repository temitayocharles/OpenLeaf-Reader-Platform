from flask import Flask, request, jsonify
import os
import jwt
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import pika
import json
from shared.utils import publish_to_queue

app = Flask(__name__)
client = MongoClient(os.getenv('MONGO_URI'))
db = client['openleaf_db']
books = db['books']  # Reuse books collection for simplicity

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/publish', methods=['POST'])
def publish():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid token'}), 401

    token = auth_header.split(' ')[1]
    try:
        decoded = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
        user_id = decoded['user_id']
    except:
        return jsonify({'error': 'Invalid token'}), 401

    data = request.json  # {title, author, content_url, genre}
    required = ['title', 'author', 'genre', 'content_url']  # Simulate ePub URL or S3 link
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    book_data = {
        'title': data['title'],
        'author': data['author'],
        'genre': data['genre'],
        'content_url': data['content_url'],
        'publisher_id': user_id,
        'created_at': datetime.utcnow().isoformat()
    }

    book_id = books.insert_one(book_data).inserted_id
    publish_to_queue('new_publish', {
        'book_id': str(book_id),
        'title': data['title'],
        'publisher_id': user_id
    })

    return jsonify({
        'status': 'published',
        'book_id': str(book_id)
    }), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=False)
