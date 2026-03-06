from pathlib import Path


def test_service_entrypoints_exist():
    root = Path(__file__).resolve().parents[2]
    expected = [
        root / "services/user-service/app.py",
        root / "services/book-service/app.py",
        root / "services/publishing-service/app.py",
        root / "services/subscription-service/app.py",
        root / "services/payment-service/app.py",
        root / "services/analytics-service/app.py",
    ]
    missing = [str(p) for p in expected if not p.exists()]
    assert not missing, f"Missing service entrypoints: {missing}"
