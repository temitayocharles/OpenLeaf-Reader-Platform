import importlib.util
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import jwt
from bson.objectid import ObjectId


ROOT = Path(__file__).resolve().parents[2]
JWT_SECRET = "test-secret"


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeUsersCollection:
    def __init__(self):
        self.docs = []

    def find_one(self, query):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    def insert_one(self, doc):
        inserted_id = ObjectId()
        record = dict(doc)
        record["_id"] = inserted_id
        self.docs.append(record)
        return FakeInsertResult(inserted_id)

    def update_one(self, *_args, **_kwargs):
        return None


class FakeCursor(list):
    def sort(self, *_args, **_kwargs):
        return self


class FakeBooksCollection:
    def __init__(self):
        self.docs = []

    def find(self, *_args, **_kwargs):
        return FakeCursor(self.docs)

    def insert_one(self, doc):
        inserted_id = ObjectId()
        record = dict(doc)
        record["_id"] = inserted_id
        self.docs.append(record)
        return FakeInsertResult(inserted_id)


def load_service_module(service_dir: str, module_name: str):
    service_path = ROOT / "services" / service_dir
    app_path = service_path / "app.py"

    os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
    os.environ.setdefault("JWT_SECRET", JWT_SECRET)
    os.environ.setdefault("RABBITMQ_HOST", "localhost")
    os.environ.setdefault("STRIPE_SECRET", "sk_test_dummy")
    os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")

    original_sys_path = list(sys.path)
    sys.path.insert(0, str(service_path))
    try:
        spec = importlib.util.spec_from_file_location(module_name, app_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path = original_sys_path


def bearer_for(user_id: str) -> str:
    token = jwt.encode({"user_id": user_id}, JWT_SECRET, algorithm="HS256")
    return f"Bearer {token}"


def test_user_service_health_auth_and_basic_contracts():
    module = load_service_module("user-service", "user_service_test")
    module.users = FakeUsersCollection()
    module.publish_to_queue = Mock()
    client = module.app.test_client()

    assert client.get("/health").status_code == 200

    r = client.post("/progress/book-1", json={"page": 1})
    assert r.status_code == 401

    r = client.post("/register", json={"email": "u@example.com", "password": "pw"})
    assert r.status_code == 201

    r = client.post("/register", json={"email": "u@example.com", "password": "pw"})
    assert r.status_code == 409

    r = client.post("/login", json={"email": "u@example.com", "password": "bad"})
    assert r.status_code == 401

    r = client.post("/login", json={"email": "u@example.com", "password": "pw"})
    assert r.status_code == 200


def test_book_service_health_and_crud_contracts():
    module = load_service_module("book-service", "book_service_test")
    module.books = FakeBooksCollection()
    module.publish_to_queue = Mock()
    client = module.app.test_client()

    assert client.get("/health").status_code == 200

    r = client.post("/books", json={"title": "T1", "author": "A1"})
    assert r.status_code == 201

    r = client.get("/books")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_publishing_service_auth_and_field_validation():
    module = load_service_module("publishing-service", "publishing_service_test")
    module.books = FakeBooksCollection()
    module.publish_to_queue = Mock()
    client = module.app.test_client()

    assert client.get("/health").status_code == 200

    r = client.post("/publish", json={"title": "T"})
    assert r.status_code == 401

    r = client.post(
        "/publish",
        headers={"Authorization": bearer_for(str(ObjectId()))},
        json={"title": "T", "author": "A"},
    )
    assert r.status_code == 400


def test_subscription_service_auth_and_tier_validation():
    module = load_service_module("subscription-service", "subscription_service_test")
    user_id = ObjectId()
    module.users = SimpleNamespace(find_one=lambda query: {"_id": user_id, "subscriptions": ["basic"]})

    mock_resp = SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {"id": "cs_test_123"},
    )
    module.requests = SimpleNamespace(post=lambda *args, **kwargs: mock_resp)
    client = module.app.test_client()

    assert client.get("/health").status_code == 200
    assert client.get("/subscriptions").status_code == 401

    valid_auth = {"Authorization": bearer_for(str(user_id))}
    assert client.get("/subscriptions", headers=valid_auth).status_code == 200

    r = client.post("/subscriptions", headers=valid_auth, json={"tier": "invalid"})
    assert r.status_code == 400

    r = client.post("/subscriptions", headers=valid_auth, json={"tier": "basic"})
    assert r.status_code == 200


def test_payment_service_env_auth_and_webhook_guards():
    os.environ["STRIPE_PRICE_BASIC"] = "price_basic_test"
    os.environ["STRIPE_PRICE_PREMIUM"] = "price_premium_test"

    module = load_service_module("payment-service", "payment_service_test")
    module.publish_to_queue = Mock()
    module.users = SimpleNamespace(update_one=lambda *args, **kwargs: None, find_one=lambda *args, **kwargs: None)
    module.stripe.checkout.Session.create = Mock(return_value=SimpleNamespace(id="cs_test_123"))
    module.stripe.Webhook.construct_event = Mock(side_effect=ValueError("invalid"))

    client = module.app.test_client()

    assert client.get("/health").status_code == 200

    r = client.post("/create-checkout-session", json={"tier": "basic"})
    assert r.status_code == 401

    valid_auth = {"Authorization": bearer_for(str(ObjectId()))}
    r = client.post("/create-checkout-session", headers=valid_auth, json={"tier": "invalid"})
    assert r.status_code == 400

    r = client.post("/create-checkout-session", headers=valid_auth, json={"tier": "basic"})
    assert r.status_code == 200

    r = client.post("/webhook", data="{}", headers={"Stripe-Signature": "bad"})
    assert r.status_code == 400
