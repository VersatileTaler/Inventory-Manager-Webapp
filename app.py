from flask import Flask, render_template, request, redirect
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

# ─────────────────────────────
# Prometheus Metrics Definition
# ─────────────────────────────

# Count total HTTP requests
REQUEST_COUNT = Counter(
    'inventory_request_count_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

# Track request duration
REQUEST_DURATION = Histogram(
    'inventory_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Track total items in inventory
INVENTORY_ITEMS = Gauge(
    'inventory_total_items',
    'Total number of items in inventory'
)

# Track total inventory value
INVENTORY_VALUE = Gauge(
    'inventory_total_value',
    'Total monetary value of inventory'
)

# Count item operations
ITEM_OPERATIONS = Counter(
    'inventory_item_operations_total',
    'Total item operations performed',
    ['operation']
)

# ─────────────────────────────
# In-memory storage
# ─────────────────────────────
inventory = {}
item_id_counter = 1

def update_inventory_metrics():
    INVENTORY_ITEMS.set(len(inventory))
    total_value = sum(
        item['quantity'] * item['price']
        for item in inventory.values()
    )
    INVENTORY_VALUE.set(total_value)

# ─────────────────────────────
# Middleware to track requests
# ─────────────────────────────
@app.before_request
def start_timer():
    request._start_time = time.time()

@app.after_request
def track_metrics(response):
    duration = time.time() - request._start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code
    ).inc()
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.path
    ).observe(duration)
    return response

# ─────────────────────────────
# Routes
# ─────────────────────────────
@app.route("/")
def index():
    total_value = sum(
        item['quantity'] * item['price']
        for item in inventory.values()
    )
    return render_template("index.html",
                           inventory=inventory,
                           total_value=total_value)

@app.route("/add", methods=["POST"])
def add_item():
    global item_id_counter
    name     = request.form.get("name")
    quantity = int(request.form.get("quantity", 0))
    price    = float(request.form.get("price", 0.0))
    if name:
        inventory[item_id_counter] = {
            "name": name,
            "quantity": quantity,
            "price": price
        }
        item_id_counter += 1
        ITEM_OPERATIONS.labels(operation="add").inc()
        update_inventory_metrics()
    return redirect("/")

@app.route("/update/<int:item_id>", methods=["POST"])
def update_item(item_id):
    if item_id in inventory:
        inventory[item_id]['quantity'] = int(
            request.form.get("quantity", 0)
        )
        ITEM_OPERATIONS.labels(operation="update").inc()
        update_inventory_metrics()
    return redirect("/")

@app.route("/delete/<int:item_id>")
def delete_item(item_id):
    if item_id in inventory:
        del inventory[item_id]
        ITEM_OPERATIONS.labels(operation="delete").inc()
        update_inventory_metrics()
    return redirect("/")

# ─────────────────────────────
# Prometheus Metrics Endpoint
# ─────────────────────────────
@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {
        'Content-Type': CONTENT_TYPE_LATEST
    }

# Health check
@app.route("/health")
def health():
    return {
        "status": "healthy",
        "version": "1.0",
        "app": "inventory-tracker",
        "total_items": len(inventory)
    }, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
