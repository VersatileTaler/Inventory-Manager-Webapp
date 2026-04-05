from app import app

def test_home():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200

def test_health():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200

def test_metrics():
    client = app.test_client()
    response = client.get("/metrics")
    assert response.status_code == 200

def test_add_item():
    client = app.test_client()
    response = client.post("/add", data={
        "name": "Test Item",
        "quantity": "10",
        "price": "5.99"
    })
    assert response.status_code == 302

def test_delete_item():
    client = app.test_client()
    client.post("/add", data={
        "name": "Delete Me",
        "quantity": "1",
        "price": "1.00"
    })
    response = client.get("/delete/1")
    assert response.status_code == 302
