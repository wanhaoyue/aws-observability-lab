from app import app


def test_health():
    resp = app.test_client().get("/healthz")
    assert resp.status_code == 200


def test_create_order_ok():
    resp = app.test_client().post("/orders", json={"item": "book"})
    assert resp.status_code == 201
    assert "orderId" in resp.get_json()


def test_create_order_validation():
    assert app.test_client().post("/orders", json={}).status_code == 400


def test_metrics_exposed():
    client = app.test_client()
    client.get("/healthz")
    body = client.get("/metrics").get_data(as_text=True)
    assert "http_requests_total" in body
