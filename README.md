# Fast Food Kiosk System
**Default Staff Login Credentials:**
- **Admin:** `admin` / `admin123` (Full Access)

---

# Fast Food Kiosk Ordering System

A Python-based fast food kiosk ordering system with backend database and frontend GUI.

## Features
- Staff login system with password hashing
- Customer ordering interface
- Kitchen order display
- Order management
- MySQL database integration
- CustomTkinter GUI
- Menu item image support with fallback placeholder (`src/no-image.jpg`)
- Philippine Peso (₱) currency

## Project Structure
```
├── kiosk_backend.py    # Backend classes (Cart, Database)
├── kiosk_frontend.py   # Frontend GUI with CustomTkinter
├── test_backend.py     # Test script for backend
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- XAMPP with MySQL (or standalone MySQL)
- Git (optional)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start Database
1. Start XAMPP Control Panel
2. Start MySQL service
3. (Optional) Open phpMyAdmin at http://localhost/phpmyadmin

### 4. Run the Application
```bash
# Option 1: Run the frontend (auto-creates database)
python kiosk_frontend.py

# Option 2: Test backend only
python kiosk_backend.py

# Option 3: Run comprehensive test
python test_backend.py
```

## Default Login Credentials
- Username: `admin`, Password: `admin123`

## Database Auto-Setup
The system automatically:
- Creates `kiosk_db` database if it doesn't exist
- Creates all necessary tables
- Migrates legacy menu category values (`Drinks` -> `Beverage`; unknown -> `Main Course`)
- Adds default admin staff account

To preload menu items for testing, import `database_setup.sql` once.
You do not need to drop and recreate schema for image/category updates; runtime migration handles existing tables.

## Frontend Integration Guide (For Groupmates)

Use `kiosk_backend.py` as the backend contract. Your frontend only needs to call these methods.

### 1. Import and initialize
```python
from kiosk_backend import Database, Cart, format_php

db = Database()
cart = Cart()
```

### 2. Customer-side methods
- `db.get_menu()`
   - Returns: `(id, name, description, price, category, is_available, image_path)`
- `cart.add_item(item_id, name, price, quantity)`
- `cart.get_items()`
- `cart.get_total()`
- `db.save_new_order(order_type, cart_items, total_amount, customer_name)`
   - Returns queue number (`int`) or `None`
- `db.get_order_details(order_id)`
   - Returns dictionary:
   - `order_info`: `(id, status, total_amount, order_type, order_time, customer_name)`
   - `items`: `(oi_id, order_id, item_id, quantity, price_at_time, menu_name, category)`
- `db.get_active_orders()`
   - Returns active queue rows:
   - `(id, status, total_amount, order_type, order_time, customer_name)`

### 3. Admin-side methods
- `db.verify_staff_login(username, password)` -> `True/False`
- `db.get_all_menu_items()`
- `db.add_menu_item(name, description, price, category, is_available=True, image_path=None)` -> inserted `item_id` or `False`
- `db.update_menu_item(item_id, **fields)` -> `True/False`
- `db.delete_menu_item(item_id)` -> soft delete (`is_available=False`)
- `db.get_categories()` -> fixed categories list: `Main Course`, `Appetizer`, `Dessert`, `Beverage`, `Side`
- `db.get_all_orders(limit=50)`
- `db.update_order_status(order_id, new_status)`
   - Valid statuses: `Pending`, `Preparing`, `Completed`, `Cancelled`
- `db.cancel_order(order_id)`

### 4. Suggested screen-to-method mapping
- Customer menu screen -> `db.get_menu()`
- Cart screen -> `Cart` methods (`add_item`, `remove_item`, `update_quantity`, `get_total`)
- Checkout button -> `db.save_new_order(...)`
- Queue screen -> `db.get_active_orders()`
- Track order screen -> `db.get_order_details(order_id)`
- Admin login screen -> `db.verify_staff_login(...)`
- Admin menu management -> `db.get_all_menu_items()`, `add_menu_item`, `update_menu_item`, `delete_menu_item`
- Admin order management -> `db.get_all_orders()`, `db.update_order_status()`, `db.cancel_order()`

### 5. Notes
- Use `format_php(amount)` to format prices consistently.
- `cli_backend.py` is the working reference for backend call flow.
- Call `db.close()` when the app exits.

## Database Schema
The system creates these tables automatically:
- `staff`: Staff login credentials
- `menu_items`: Food items with prices (PHP) and `image_path`
- `orders`: Order information
- `order_items`: Items in each order

## Image Rules
- GUI inventory supports `.jpg`, `.jpeg`, and `.png` when selecting item images.
- Selected images are copied into `src/` and saved to the item record.
- If no image is attached, or if a saved image file is missing, the app uses `src/no-image.jpg`.
- CLI remains image-agnostic; it does not prompt for image input.

## Category Rules
- Canonical categories are fixed to: `Main Course`, `Appetizer`, `Dessert`, `Beverage`, `Side`.
- Legacy `Drinks` is migrated to `Beverage` automatically.
- Invalid or unknown categories are auto-normalized to `Main Course` by backend logic.

## Currency
All prices are in Philippine Peso (₱). Use the `format_php()` function to display prices.

## Testing
Run `python test_backend.py` to test database connection and basic functionality before implementing GUI features.

## Troubleshooting

### MySQL Connection Errors
1. Ensure XAMPP MySQL is running
2. Check if port 3306 is available
3. Verify username/password in `kiosk_backend.py` (default: root with no password)

### CustomTkinter Errors
```bash
# If customtkinter not found
pip install customtkinter
```

### ModuleNotFoundError
Make sure all files are in the same directory and you're running from the project root.

## License
Educational project for college coursework.

## Group Members
- [Your Name/Groupmate Name] - Backend
- [Groupmate Name] - Frontend Customer Ordering
- [Groupmate Name] - Frontend Kitchen Display
- [Groupmate Name] - Frontend Order Management