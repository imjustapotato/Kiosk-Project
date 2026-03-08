# Kiosk Backend Documentation

This guide explains how `kiosk_backend.py` works, what logic it uses, and how you can connect any GUI/frontend to it.

## Purpose
`kiosk_backend.py` is the business-logic and data-access layer for the kiosk system.

It handles:
- cart operations in memory
- database setup and persistence
- menu retrieval and management
- order creation and order status flow
- admin login verification

## Backend Architecture

### 1. Utility Formatter
- `kiosk_backend.py:4` `def format_php(amount):`
- Purpose: formats numeric values to peso format `₱{amount:.2f}`.

### 2. In-Memory Cart Layer
- `kiosk_backend.py:7` `class Cart:`
- Responsibility: temporary cart state before checkout.

Key methods:
- `kiosk_backend.py:9` `__init__`: initializes `self.items`.
- `kiosk_backend.py:12` `add_item`: appends an item dictionary to cart.
- `kiosk_backend.py:22` `get_total`: computes subtotal sum of `price * quantity` and normalizes item prices to numeric float values.
- `kiosk_backend.py:28` `clear_cart`: resets cart after successful checkout/cancel.
- `kiosk_backend.py:32` `remove_item`: removes one cart row by `item_id`.
- `kiosk_backend.py:41` `update_quantity`: updates quantity or removes if <= 0.
- `kiosk_backend.py:55` `get_items`: returns shallow copy for safe transfer to DB layer.
- `kiosk_backend.py:58` `get_item_count`: sum of all quantities.
- `kiosk_backend.py:61` `is_empty`: `True` when cart has no lines.
- `kiosk_backend.py:64` `display_cart`: CLI-friendly rendering.

### 3. Database Access Layer
- `kiosk_backend.py:82` `class Database:`
- Responsibility: MySQL connection, schema bootstrapping, and all CRUD/order queries.

Initialization flow:
- `kiosk_backend.py:84` `__init__`
1. Connects to MySQL server.
2. Creates `kiosk_db` if missing.
3. Connects to `kiosk_db`.
4. Calls `_create_tables`.
5. If `staff` table is empty, seeds default admin user via `_add_default_data`.

Schema creation:
- `kiosk_backend.py:122` `_create_tables`
- Ensures these tables exist:
1. `staff`
2. `menu_items`
3. `orders`
4. `order_items`

Menu schema note:
- `menu_items` includes `image_path` with default `src/no-image.jpg`.
- `_create_tables` performs a compatibility migration for older databases by auto-adding `image_path` when missing.
- Existing rows with empty image paths are normalized to `src/no-image.jpg`.
- Category values are normalized to fixed options: `Main Course`, `Appetizer`, `Dessert`, `Beverage`, `Side`.
- Legacy `Drinks` rows are migrated to `Beverage`; unknown/empty categories are normalized to `Main Course`.

Orders schema note:
- `orders` includes `customer_name` for queue visibility.
- `_create_tables` also performs a compatibility migration: if `customer_name` is missing in an older DB, it auto-adds the column.

Default seed data:
- `kiosk_backend.py:186` `_add_default_data`
- Adds single admin account:
	- username: `admin`
	- password: `admin123` (stored as SHA-256 hash)

## Business Logic by Feature

### Login
- `kiosk_backend.py:205` `verify_staff_login(username, password)`
- Logic:
1. Hash incoming password with SHA-256.
2. Query `staff` by `username` + `password_hash`.
3. Return `True` on match, else `False`.

### Menu Retrieval (Customer)
- `kiosk_backend.py:223` `get_menu()`
- Returns only rows where `is_available = TRUE`.
- Returned row shape includes `image_path` at the end.

### Place Order
- `kiosk_backend.py:240` `save_new_order(order_type, cart_items, total_amount, customer_name="Guest")`
- Logic:
1. Insert new row in `orders` with status `Pending` and `customer_name`.
2. Read generated order ID using `LAST_INSERT_ID()`.
3. Insert each cart line into `order_items`.
4. Commit transaction.
5. Return queue number (same as `orders.id`).

### Queue/Kitchen View
- `kiosk_backend.py:276` `get_active_orders()`
- Returns queue rows with this shape:
	- `id`
	- `status`
	- `total_amount`
	- `order_type`
	- `order_time`
	- `customer_name`
- Filters to orders where status is not `Completed` and not `Cancelled`.

### Menu Management (Admin)
- `kiosk_backend.py:297` `get_all_menu_items()`
- `kiosk_backend.py:310` `add_menu_item(...)`
- `kiosk_backend.py:330` `update_menu_item(item_id, **kwargs)`
- `kiosk_backend.py:360` `delete_menu_item(item_id)`
- `kiosk_backend.py:363` `get_menu_item_by_id(item_id)`

Notes:
- `delete_menu_item` is a soft delete (`is_available = False`).
- `update_menu_item` supports partial update through `kwargs`.
- `update_menu_item` first checks if item exists; no-change updates return success (info) instead of false not-found.
- Category inputs are normalized by backend before persistence.

### Order Management (Admin)
- `kiosk_backend.py:377` `get_order_details(order_id)`
- `kiosk_backend.py:408` `update_order_status(order_id, new_status)`
- `kiosk_backend.py:446` `cancel_order(order_id)`
- `kiosk_backend.py:449` `get_all_orders(limit=50)`
- `kiosk_backend.py:466` `get_orders_by_status(status)`

Status rules enforced:
- Valid statuses are `Pending`, `Preparing`, `Completed`, `Cancelled`.
- Status update now validates order existence first.
- If selected status is already the current status, method returns success as a no-op.

### Utility Queries
- `kiosk_backend.py:479` `get_categories()`
- `kiosk_backend.py:492` `search_menu_items(search_term)`
- `kiosk_backend.py:510` `close()`

## How Frontend/GUI Should Use This Backend

This backend is framework-agnostic. Groupmates can use CustomTkinter, Tkinter, PyQt, web frameworks, or mobile wrappers as long as they call these methods in the same order.

### Recommended Integration Pattern
1. Create one shared `Database()` instance at app startup.
2. Create one `Cart()` per active customer session/order flow.
3. Never write SQL directly in frontend code.
4. Use backend methods only, then render returned data in UI.
5. Call `db.close()` when app exits.

### Suggested UI-to-Backend Mapping

Landing screen:
- Dine-in/Take-out button sets `order_type` local state.
- Staff/Admin login screen uses `verify_staff_login`.

Customer menu screen:
- Load items with `get_menu()`.
- Add item button calls `cart.add_item(...)`.
- Cart section reads `cart.get_items()`, `cart.get_total()`, `cart.get_item_count()`.

Checkout flow:
- Validate `not cart.is_empty()`.
- Capture name input (or set `Guest` fallback).
- Call `save_new_order(order_type, cart.get_items(), cart.get_total(), customer_name)`.
- Display returned queue number.
- Call `cart.clear_cart()`.

Admin inventory screen:
- List all with `get_all_menu_items()`.
- Add with `add_menu_item(..., image_path=None)`.
- Edit with `update_menu_item(item_id, ...)`.
- Delete with `delete_menu_item(item_id)`.

Image behavior:
- If no image is provided, backend stores `src/no-image.jpg`.
- CLI does not need image prompts; default placeholder behavior still applies.

Category behavior:
- Backend exposes fixed categories via `get_categories()` for UI/CLI selectors.
- Invalid categories are auto-normalized to `Main Course`.

Admin order screen:
- Active queue with `get_active_orders()`.
- Show `customer_name` beside queue/order number in queue view.
- Full history with `get_all_orders()`.
- Details with `get_order_details(order_id)`.
- Status updates with `update_order_status(order_id, new_status)`.
- Cancel with `cancel_order(order_id)`.

## Minimal Example (for Groupmates)

```python
from kiosk_backend import Database, Cart

db = Database()
cart = Cart()

menu = db.get_menu()
first = menu[0]
cart.add_item(first[0], first[1], first[3], 1)

queue_no = db.save_new_order("Dine-in", cart.get_items(), cart.get_total(), "Juan Dela Cruz")
print("Queue:", queue_no)

db.close()
```

## Error-Handling Guidelines for Frontend Developers
- If any method returns `False`, `None`, or empty list, show a user-friendly message.
- Keep backend print logs for debugging during development.
- For production polish, wrap backend calls with UI loading states and try/except in frontend.

## Current Auth Model
- Single operational role: `admin`.
- Default credentials are seeded by backend when `staff` is empty.
- If you later add more roles, add a `role` column in `staff` and route UI sections by role.
