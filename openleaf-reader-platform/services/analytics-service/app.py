from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
import os
from pymongo import MongoClient
import pika
import json
import threading
from shared.utils import publish_to_queue  # not needed here, but for consistency
import jwt

app = Flask(__name__)
metrics = PrometheusMetrics(app)  # Auto-instruments /metrics endpoint

# Custom metrics
total_pages_read = metrics.counter('total_pages_read_total', 'Total pages read across all users')
active_subscribers = metrics.gauge('active_subscribers', 'Current active subscribers by tier', labels={'tier': None})
new_books_published = metrics.counter('new_books_published_total', 'Total self-published books')

client = MongoClient(os.getenv('MONGO_URI'))
db = client['openleaf_db']
analytics = db['analytics']  # Aggregates collection
users = db['users']
books = db['books']

# Background RabbitMQ consumer
def consume_events():
    connection = pika.BlockingConnection(pika.ConnectionParameters(os.getenv('RABBITMQ_HOST')))
    channel = connection.channel()

    def callback(ch, method, properties, body):
        data = json.loads(body)
        queue = method.routing_key

        if queue == 'progress_sync':
            user_id = data['user_id']
            book_id = data['book_id']
            page = data['page']

            # Update book stats (anonymized)
            analytics.update_one(
                {'type': 'book', 'book_id': book_id},
                {'$inc': {'total_pages_read': 1, 'unique_users': 1 if analytics.find_one({'type': 'book', 'book_id': book_id, 'user_ids': user_id}) is None else 0}},
                upsert=True
            )
            # Track user-specific progress for personal insights
            users.update_one(
                {'_id': user_id},
                {'$set': {f'progress.{book_id}': page}}
            )
            total_pages_read.inc()

        elif queue == 'subscription_confirmed':
            tier = data['tier']
            active_subscribers.labels(tier=tier).inc()

        elif queue == 'subscription_cancelled':
            # Decrement (simplified; in real use find tier from user)
            active_subscribers.labels(tier='basic').dec()  # Adjust logic per tier

        elif queue == 'new_publish':
            new_books_published.inc()
            analytics.update_one(
                {'type': 'global'},
                {'$inc': {'self_published_count': 1}},
                upsert=True
            )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='progress_sync', on_message_callback=callback)
    channel.basic_consume(queue='subscription_confirmed', on_message_callback=callback)
    channel.basic_consume(queue='subscription_cancelled', on_message_callback=callback)
    channel.basic_consume(queue='new_publish', on_message_callback=callback)

    channel.start_consuming()

# Start consumer in thread
threading.Thread(target=consume_events, daemon=True).start()

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/books/<book_id>', methods=['GET'])
def book_analytics(book_id):
    # Public-ish stats (anonymized)
    stats = analytics.find_one({'type': 'book', 'book_id': book_id}) or {}
    total_read = stats.get('total_pages_read', 0)
    unique = stats.get('unique_users', 0)
    completion = (total_read / (unique * 300)) * 100 if unique > 0 else 0  # Assume avg 300 pages
    return jsonify({
        'book_id': book_id,
        'total_pages_read': total_read,
        'unique_readers': unique,
        'estimated_completion_rate': round(completion, 2)
    })

@app.route('/global', methods=['GET'])
def global_analytics():
    # Admin-only; add JWT check + Kong ACL
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    try:
        decoded = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
        # Assume admin role in token claims; skip detailed check for now
    except:
        return jsonify({'error': 'Unauthorized'}), 401

    global_stats = analytics.find_one({'type': 'global'}) or {}
    return jsonify({
        'total_self_published': global_stats.get('self_published_count', 0),
        # Add more aggregates
    })

# Add /user/insights endpoint (personalized, requires auth)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006, debug=False)
