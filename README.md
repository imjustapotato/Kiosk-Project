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
kiosk_project/
├── kiosk_backend.py          # Backend classes (Cart, Database)
├── requirements.txt          # Pinned Python dependencies
├── database_setup.sql        # SQL for initial database setup
├── README.md                 # This file
└── src/                      # Menu item images + fallback
	└── no-image.jpg
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- XAMPP with MySQL

### 2. Local Folder Setup (Manual File Copy)
If you are setting this up using files shared directly:

1. Create a folder named `kiosk_project`.
2. Move these files into that folder:
- `kiosk_backend.py`
- `database_setup.sql`
- `requirements.txt`
3. Keep the `src/` folder (including `src/no-image.jpg`) in the same project root.
4. Right-click the folder and open it with VS Code (or any IDE).
5. Alternatively, right-click and choose **Open in Terminal**.

### 3. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 4. Create and Use Virtual Environment (Recommended but optional)
```bash
python -m venv .venv
./.venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5. Start Database (XAMPP)
1. Start XAMPP Control Panel
2. Run XAMPP as Administrator if needed
3. Click **Start** on MySQL
4. Click **Admin** or open http://localhost/phpmyadmin

### 7. Preload Database and Menu Items
You can preload data using phpMyAdmin (Web Admin) or terminal SQL import.

#### Option A: Web Admin (phpMyAdmin)
1. Create a schema named `kiosk_db`.
2. Open `kiosk_db`.
3. Click **Import**.
4. Choose file `database_setup.sql`.
5. Click **Import**.

#### Option B: Terminal Import (MySQL CLI)
```bash
mysql -u root -p kiosk_db < database_setup.sql
```

If your local MySQL root has no password, you can run:
```bash
mysql -u root kiosk_db < database_setup.sql
```

## Git Collaboration Guide

### Clone the Repository (first time)
```bash
git clone <https://github.com/imjustapotato/Kiosk-Project.git>
cd kiosk_project
```

### Pull Latest Changes
```bash
git pull origin main
```

### Create and Use Your Own Branch
Each should push to each own branch not directly to `main`.

```bash
git checkout -b <your-branch-name>
```

### Commit and Push Your Updates
```bash
git add .
git commit -m "Describe your change"
git push -u origin <your-branch-name>
```

After first push with `-u`, next pushes can be:
```bash
git push
```

### Sync Your Branch with Main
```bash
git checkout main
git pull origin main
git checkout <your-branch-name>
git merge main
```

Resolve conflicts if prompted, then commit and push again.

## Default Login Credentials
- Username: `admin`, Password: `admin123`

## Database Auto-Setup
The system automatically:
- Creates `kiosk_db` database if it doesn't exist
- Creates all necessary tables
- Adds default admin staff account

You can also run `database_setup.sql` in phpMyAdmin to manually set up the database.

## Frontend Integration Guide

### 1. Import and initialize
```python
from kiosk_backend import Cart, Database, MENU_CATEGORIES, format_php

db = Database()
cart = Cart()
```

### 2. Mapping
- Customer menu screen -> `db.get_menu()`
- Cart screen -> `Cart` methods (`add_item`, `remove_item`, `update_quantity`, `get_total`)
- Checkout button -> `db.save_new_order(...)`
- Queue screen -> `db.get_active_orders()`
- Track order screen -> `db.get_order_details(order_id)`
- Admin login screen -> `db.verify_staff_login(...)`
- Admin menu management -> `db.get_all_menu_items()`, `add_menu_item`, `update_menu_item`, `delete_menu_item`
- Admin order management -> `db.get_all_orders()`, `db.update_order_status()`, `db.cancel_order()`

### 3. Notes
- Use `format_php(amount)` to format prices consistently.
- Call `db.close()` when the app exits.

## Database Schema
- `staff`: Staff login credentials
- `menu_items`: Food items with prices and `image_path`
- `orders`: Order information
- `order_items`: Items in each order

## Image Rules
- Image picker allows broad file selection.
- Selected files are validated as decodable images before being saved for item records.
- If no image is attached, or a saved image cannot be loaded, the app falls back to `src/no-image.jpg`.

## Troubleshooting
- If MySQL connection fails, ensure XAMPP MySQL is running and credentials in `kiosk_backend.py` match your local setup.
- If images are missing, confirm `src/no-image.jpg` exists in project root.
- If Qt dependencies fail to import, reactivate `.venv` and reinstall with `python -m pip install -r requirements.txt`.

## Added Front-End using PySide6
- A new file `kiosk_frontend_qt.py` has been added which implements a designed GUI for the backend. However the back_end is still headless or agnostic to the front-end, so the backend can be used with any front-end framework.

## License
Educational project for college coursework.