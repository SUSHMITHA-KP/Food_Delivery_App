from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# -----------------------------
# DATA
# -----------------------------

menu = [
    {"id": 1, "name": "Margherita Pizza", "price": 250, "category": "Pizza", "is_available": True},
    {"id": 2, "name": "Veg Burger", "price": 120, "category": "Burger", "is_available": True},
    {"id": 3, "name": "Cold Coffee", "price": 90, "category": "Drink", "is_available": True},
    {"id": 4, "name": "Chocolate Cake", "price": 150, "category": "Dessert", "is_available": False},
    {"id": 5, "name": "Paneer Pizza", "price": 300, "category": "Pizza", "is_available": True},
    {"id": 6, "name": "French Fries", "price": 80, "category": "Snack", "is_available": True}
]

orders = []
cart = []
order_counter = 1

# -----------------------------
# DAY 1 - BASIC APIs
# -----------------------------

@app.get("/")
def home():
    return {"message": "Welcome to Food Delivery API"}

@app.get("/menu")
def get_menu():
    return {"menu": menu, "total": len(menu)}

@app.get("/menu/summary")
def summary():
    available = [m for m in menu if m["is_available"]]
    return {
        "total": len(menu),
        "available": len(available),
        "unavailable": len(menu) - len(available),
        "categories": list(set(m["category"] for m in menu))
    }

@app.get("/menu/{item_id}")
def get_item(item_id: int):
    for item in menu:
        if item["id"] == item_id:
            return item
    return {"error": "Item not found"}

@app.get("/orders")
def get_orders():
    return {"orders": orders, "total": len(orders)}

# -----------------------------
# DAY 2 & 3 - ORDERS
# -----------------------------

class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=20)
    delivery_address: str = Field(..., min_length=5)
    order_type: str = "delivery"

def find_item(item_id):
    for item in menu:
        if item["id"] == item_id:
            return item
    return None

def calculate_bill(price, quantity, order_type):
    total = price * quantity
    if order_type == "delivery":
        total += 30
    return total

@app.post("/orders")
def create_order(data: OrderRequest):
    global order_counter

    item = find_item(data.item_id)

    if not item:
        return {"error": "Item not found"}

    if not item["is_available"]:
        return {"error": "Item not available"}

    total = calculate_bill(item["price"], data.quantity, data.order_type)

    order = {
        "order_id": order_counter,
        "customer": data.customer_name,
        "item": item["name"],
        "quantity": data.quantity,
        "total_price": total
    }

    orders.append(order)
    order_counter += 1

    return order

# -----------------------------
# DAY 4 - CRUD + FILTER
# -----------------------------

@app.get("/menu/filter")
def filter_menu(category: Optional[str] = None, max_price: Optional[int] = None):
    result = menu

    if category is not None:
        result = [m for m in result if m["category"].lower() == category.lower()]

    if max_price is not None:
        result = [m for m in result if m["price"] <= max_price]

    return {"items": result, "total": len(result)}

@app.post("/menu")
def add_item(name: str, price: int, category: str):
    new_id = len(menu) + 1

    item = {
        "id": new_id,
        "name": name,
        "price": price,
        "category": category,
        "is_available": True
    }

    menu.append(item)
    return item

@app.put("/menu/{item_id}")
def update_item(item_id: int, price: Optional[int] = None):
    item = find_item(item_id)

    if not item:
        return {"error": "Item not found"}

    if price is not None:
        item["price"] = price

    return {"message": "Updated", "item": item}

@app.delete("/menu/{item_id}")
def delete_item(item_id: int):
    item = find_item(item_id)

    if not item:
        return {"error": "Item not found"}

    menu.remove(item)
    return {"message": f"{item['name']} deleted"}

# -----------------------------
# DAY 5 - CART
# -----------------------------

@app.post("/cart/add")
def add_cart(item_id: int, quantity: int = 1):

    item = find_item(item_id)

    if not item:
        raise HTTPException(404, "Item not found")

    if not item["is_available"]:
        raise HTTPException(400, "Item not available")

    for c in cart:
        if c["item_id"] == item_id:
            c["quantity"] += quantity
            c["subtotal"] = item["price"] * c["quantity"]
            return {"message": "Updated cart", "cart": c}

    cart_item = {
        "item_id": item_id,
        "name": item["name"],
        "quantity": quantity,
        "subtotal": item["price"] * quantity
    }

    cart.append(cart_item)
    return {"message": "Added", "cart": cart_item}

@app.get("/cart")
def view_cart():
    total = sum(c["subtotal"] for c in cart)
    return {"cart": cart, "total": total}

@app.post("/cart/checkout")
def checkout(customer_name: str):
    global order_counter

    if not cart:
        raise HTTPException(400, "Cart empty")

    created = []

    for c in cart:
        order = {
            "order_id": order_counter,
            "customer": customer_name,
            "item": c["name"],
            "quantity": c["quantity"],
            "total_price": c["subtotal"]
        }
        orders.append(order)
        created.append(order)
        order_counter += 1

    cart.clear()

    return {"orders": created}

# -----------------------------
# DAY 6 - SEARCH, SORT, PAGE
# -----------------------------

@app.get("/menu/search")
def search(keyword: str):
    result = [m for m in menu if keyword.lower() in m["name"].lower()]

    if not result:
        return {"message": "No items found"}

    return {"items": result, "total": len(result)}

@app.get("/menu/sort")
def sort_menu(sort_by: str = "price", order: str = "asc"):

    if sort_by not in ["price", "name"]:
        return {"error": "Invalid sort_by"}

    result = sorted(menu, key=lambda x: x[sort_by], reverse=(order == "desc"))

    return {"items": result}

@app.get("/menu/page")
def paginate(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    return {
        "page": page,
        "limit": limit,
        "total": len(menu),
        "total_pages": -(-len(menu) // limit),
        "items": menu[start:start + limit]
    }

@app.get("/menu/browse")
def browse(keyword: Optional[str] = None, page: int = 1, limit: int = 2):

    result = menu

    if keyword:
        result = [m for m in result if keyword.lower() in m["name"].lower()]

    total = len(result)
    start = (page - 1) * limit

    return {
        "items": result[start:start + limit],
        "total_found": total,
        "page": page,
        "total_pages": -(-total // limit)
    }

# -----------------------------
# EXTRA - ORDERS SEARCH
# -----------------------------

@app.get("/orders/search")
def search_orders(customer: str):

    result = [
        o for o in orders
        if customer.lower() in o["customer"].lower()
    ]

    if not result:
        return {"message": "No orders found"}

    return {"orders": result, "total": len(result)}