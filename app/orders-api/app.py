import random
import time
import uuid

from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = Flask(__name__)

REQUESTS = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5),
)
ORDERS_CREATED = Counter("orders_created_total", "Orders accepted by the API")


@app.before_request
def _start_timer():
    g.start = time.perf_counter()


@app.after_request
def _record_metrics(response):
    endpoint = request.url_rule.rule if request.url_rule else "unmatched"
    if endpoint != "/metrics":
        LATENCY.labels(endpoint).observe(time.perf_counter() - g.start)
        REQUESTS.labels(request.method, endpoint, response.status_code).inc()
    return response


@app.get("/healthz")
def healthz():
    return jsonify(status="ok")


@app.post("/orders")
def create_order():
    payload = request.get_json(silent=True) or {}
    if "item" not in payload:
        return jsonify(error="'item' is required"), 400
    time.sleep(random.uniform(0.01, 0.08))  # simulate work so dashboards have shape
    ORDERS_CREATED.inc()
    # TODO: write to DynamoDB and publish to SQS using boto3 (Pod Identity supplies credentials)
    return jsonify(orderId=str(uuid.uuid4()), item=payload["item"]), 201


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
