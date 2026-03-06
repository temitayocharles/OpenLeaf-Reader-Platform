from pymongo import MongoClient
import os

mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
client = MongoClient(mongo_uri)
db = client['openleaf_db']

books = []
for i in range(1, 101):
    books.append({
        'title': f'Sample Book {i}',
        'genre': 'Fiction' if i % 2 == 0 else 'Non-Fiction',
        'author': f'Author {i}'
    })

if books:
    db['books'].insert_many(books)

db['users'].insert_one({
    'email': 'demo@example.com',
    'password': 'secret',
    'progress': {},
    'subscriptions': []
})

print('Seed complete')
