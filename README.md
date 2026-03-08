# Fast Food Kiosk System
**Default Staff Login Credentials:**
- **Admin:** `admin` / `admin123` (Full Access)

---

# Fast Food Kiosk Ordering System

A Python-based fast food kiosk ordering system with backend database.

## Features
- Staff login system with password hashing
- Order management
- Order Queue display for kitchen staff
- MySQL database integration
- Menu item image support with fallback placeholder (`src/no-image.jpg`)
- CRUD for orders (Customer and Admin)
- CRUD for menu items (Admin)

## Project Structure
```
src/(images)
├── kiosk_backend.py    # Backend classes (Cart, Database)
├── requirements.txt    # Python dependencies
├── database_setup.sql  # SQL for initial database setup
└── README.md          # This file
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- XAMPP with MySQL

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start Database
1. Start XAMPP Control Panel
2. Start MySQL service
3. (Optional) Open phpMyAdmin at http://localhost/phpmyadmin

## Default Login Credentials
- Username: `admin`, Password: `admin123`

## Database Auto-Setup
The system automatically:
- Creates `kiosk_db` database if it doesn't exist
- Creates all necessary tables
- Adds default admin staff account

You can also run `database_setup.sql` in phpMyAdmin to manually set up the database.

## Frontend Integration Guide (For Groupmates)

Use `kiosk_backend.py` as the backend contract. Your frontend only needs to call these methods.

### 1. Import and initialize
```python
from kiosk_backend import Database, Cart, format_php

db = Database()
cart = Cart()
```

### 4. Mapping
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
- Call `db.close()` when the app exits.

## Database Schema
- `staff`: Staff login credentials
- `menu_items`: Food items with prices and `image_path`
- `orders`: Order information
- `order_items`: Items in each order

## Image Rules
- Image supports only `jpg/jpeg/png` formats.
- Selected images are copied into `src/` and saved to the item record.
- If no image is attached, or if a saved image file is missing, the app uses `src/no-image.jpg`.

## License
Educational project for college coursework.