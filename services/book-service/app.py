from flask import Flask, request, jsonify
import os
from pymongo import MongoClient
from shared.utils import publish_to_queue

app = Flask(__name__)
client = MongoClient(os.getenv('MONGO_URI'))
db = client['openleaf_db']
books = db['books']

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/books', methods=['GET'])
def get_books():
    query = request.args.get('search')
    filter_ = {'$text': {'$search': query}} if query else {}
    books_list = list(books.find(filter_, limit=50).sort('title'))
    for b in books_list:
        b['_id'] = str(b['_id'])
    return jsonify(books_list)

@app.route('/books', methods=['POST'])
def add_book():  # For admin/self-publish integration
    data = request.json
    book_id = books.insert_one(data).inserted_id
    publish_to_queue('new_book', {'book_id': str(book_id)})
    return jsonify({'book_id': str(book_id)}), 201

# Audiobooks similar, separate collection if needed

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)
