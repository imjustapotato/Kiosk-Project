import hashlib
import mysql.connector

DEFAULT_IMAGE_PATH = "src/no-image.jpg"
DEFAULT_CATEGORY = "Main Course"
MENU_CATEGORIES = [
    "Main Course",
    "Appetizer",
    "Dessert",
    "Beverage",
    "Side",
]
LEGACY_CATEGORY_MAP = {
    "drinks": "Beverage",
}

def format_php(amount):
    return f"₱{amount:.2f}"

class Cart:
    
    def __init__(self):
        self.items = []
    
    def add_item(self, item_id, name, price, quantity):
        item = {
            'item_id': item_id,
            'name': name,
            'price': price,
            'quantity': quantity
        }
        self.items.append(item)
        print(f"Added {quantity} x {name} (₱{price:.2f} each) to cart")
    
    def get_total(self):
        total = 0.0
        for item in self.items:
            total += float(item['price']) * item['quantity']
        return total
    
    def clear_cart(self):
        self.items = []
        print("Cart cleared")
    
    def remove_item(self, item_id):
        for i, item in enumerate(self.items):
            if item['item_id'] == item_id:
                removed = self.items.pop(i)
                print(f"Removed {removed['name']} from cart")
                return True
        print(f"Item with ID {item_id} not found in cart")
        return False
    
    def update_quantity(self, item_id, new_quantity):
        if new_quantity <= 0:
            return self.remove_item(item_id)
        
        for item in self.items:
            if item['item_id'] == item_id:
                old_qty = item['quantity']
                item['quantity'] = new_quantity
                print(f"Updated {item['name']}: {old_qty} → {new_quantity}")
                return True
        
        print(f"Item with ID {item_id} not found in cart")
        return False
    
    def get_items(self):
        return self.items.copy()
    
    def get_item_count(self):
        return sum(item['quantity'] for item in self.items)
    
    def is_empty(self):
        return len(self.items) == 0
    
    def display_cart(self):
        if self.is_empty():
            print("🛒 Cart is empty")
            return
        
        print("\n" + "="*50)
        print("YOUR CART")
        print("="*50)
        for i, item in enumerate(self.items, 1):
            item_total = item['price'] * item['quantity']
            print(f"{i}. {item['name']} x{item['quantity']}")
            print(f"   {format_php(item['price'])} each = {format_php(item_total)}")
        print("-"*50)
        print(f"TOTAL: {format_php(self.get_total())}")
        print(f"Items: {self.get_item_count()}")
        print("="*50)


class Database:

    @staticmethod
    def normalize_category(category):
        raw = (category or "").strip()
        if not raw:
            return DEFAULT_CATEGORY

        # Accept canonical labels case-insensitively.
        canonical_lookup = {name.lower(): name for name in MENU_CATEGORIES}
        lowered = raw.lower()
        if lowered in canonical_lookup:
            return canonical_lookup[lowered]

        if lowered in LEGACY_CATEGORY_MAP:
            return LEGACY_CATEGORY_MAP[lowered]

        return DEFAULT_CATEGORY
    
    def __init__(self):
        try:
            temp_conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password=""
            )
            temp_cursor = temp_conn.cursor()
            
            temp_cursor.execute("SHOW DATABASES LIKE 'kiosk_db'")
            if not temp_cursor.fetchone():
                print("Database 'kiosk_db' not found. Creating it...")
                temp_cursor.execute("CREATE DATABASE kiosk_db")
                print("Database 'kiosk_db' created successfully")
            
            temp_cursor.close()
            temp_conn.close()
            
            self.connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="kiosk_db"
            )
            self.cursor = self.connection.cursor()
            
            self._create_tables()
            
            print("Database connection established successfully")
            
        except mysql.connector.Error as err:
            print(f"Database connection failed: {err}")
            print("Make sure:")
            print("1. XAMPP is running with MySQL")
            print("2. MySQL service is started")
            self.connection = None
            self.cursor = None
    
    def _create_tables(self):
        try:
            staff_table = """
            CREATE TABLE IF NOT EXISTS staff (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(64) NOT NULL,
                full_name VARCHAR(100) NOT NULL
            )
            """
            self.cursor.execute(staff_table)
            
            menu_table = """
            CREATE TABLE IF NOT EXISTS menu_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                category VARCHAR(50),
                is_available BOOLEAN DEFAULT TRUE,
                image_path VARCHAR(255) DEFAULT 'src/no-image.jpg'
            )
            """
            self.cursor.execute(menu_table)

            self.cursor.execute("SHOW COLUMNS FROM menu_items LIKE 'image_path'")
            if not self.cursor.fetchone():
                self.cursor.execute(
                    "ALTER TABLE menu_items ADD COLUMN image_path VARCHAR(255) DEFAULT 'src/no-image.jpg'"
                )
            self.cursor.execute(
                "UPDATE menu_items SET image_path = %s WHERE image_path IS NULL OR image_path = ''",
                (DEFAULT_IMAGE_PATH,),
            )

            self.cursor.execute(
                "UPDATE menu_items SET category = %s WHERE LOWER(TRIM(category)) = 'drinks'",
                ("Beverage",),
            )

            canonical_values = ", ".join(["%s"] * len(MENU_CATEGORIES))
            self.cursor.execute(
                f"""
                UPDATE menu_items
                SET category = %s
                WHERE category IS NULL OR TRIM(category) = ''
                OR category NOT IN ({canonical_values})
                """,
                tuple([DEFAULT_CATEGORY] + MENU_CATEGORIES),
            )
            
            orders_table = """
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                status VARCHAR(20) DEFAULT 'Pending',
                total_amount DECIMAL(10,2) NOT NULL,
                order_type VARCHAR(20),
                order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                customer_name VARCHAR(100) DEFAULT 'Guest'
            )
            """
            self.cursor.execute(orders_table)

            self.cursor.execute("SHOW COLUMNS FROM orders LIKE 'customer_name'")
            if not self.cursor.fetchone():
                self.cursor.execute("ALTER TABLE orders ADD COLUMN customer_name VARCHAR(100) DEFAULT 'Guest'")
            
            order_items_table = """
            CREATE TABLE IF NOT EXISTS order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                item_id INT NOT NULL,
                quantity INT NOT NULL,
                price_at_time DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES menu_items(id)
            )
            """
            self.cursor.execute(order_items_table)
            
            self.connection.commit()
            print("All tables checked/created successfully")
            
            self.cursor.execute("SELECT COUNT(*) FROM staff")
            if self.cursor.fetchone()[0] == 0:
                self._add_default_data()
                
        except mysql.connector.Error as err:
            print(f"Error creating tables: {err}")
            self.connection.rollback()
    
    def _add_default_data(self):
        try:
            staff_data = [
                ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 'System Administrator')
            ]
            
            for username, password_hash, full_name in staff_data:
                self.cursor.execute(
                    "INSERT INTO staff (username, password_hash, full_name) VALUES (%s, %s, %s)",
                    (username, password_hash, full_name)
                )
            
            self.connection.commit()
            print("Default staff accounts added successfully")
            
        except mysql.connector.Error as err:
            print(f"Error adding default data: {err}")
            self.connection.rollback()
    
    def verify_staff_login(self, username, password):
        if not self.connection:
            print("No database connection")
            return False
        
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            query = "SELECT * FROM staff WHERE username = %s AND password_hash = %s"
            self.cursor.execute(query, (username, password_hash))
            result = self.cursor.fetchone()
            
            return result is not None
            
        except mysql.connector.Error as err:
            print(f"Login verification failed: {err}")
            return False
    
    def get_menu(self):
        if not self.connection:
            print("No database connection")
            return []
        
        try:
            query = "SELECT * FROM menu_items WHERE is_available = TRUE"
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            print(f"Retrieved {len(results)} menu items")
            return results
            
        except mysql.connector.Error as err:
            print(f"Failed to get menu: {err}")
            return []
    
    def save_new_order(self, order_type, cart_items, total_amount, customer_name="Guest"):
        if not self.connection:
            print("No database connection")
            return None
        
        try:
            order_query = """
            INSERT INTO orders (status, total_amount, order_type, customer_name) 
            VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(order_query, ('Pending', total_amount, order_type, customer_name))
            
            self.cursor.execute("SELECT LAST_INSERT_ID()")
            queue_number = self.cursor.fetchone()[0]
            
            for item in cart_items:
                item_query = """
                INSERT INTO order_items (order_id, item_id, quantity, price_at_time) 
                VALUES (%s, %s, %s, %s)
                """
                self.cursor.execute(item_query, (
                    queue_number,
                    item['item_id'],
                    item['quantity'],
                    item['price']
                ))
            
            self.connection.commit()
            print(f"Order #{queue_number} saved successfully - Total: ₱{total_amount:.2f}")
            return queue_number
            
        except mysql.connector.Error as err:
            print(f"Failed to save order: {err}")
            self.connection.rollback()
            return None
    
    def get_active_orders(self):
        if not self.connection:
            print("No database connection")
            return []
        
        try:
            query = """
            SELECT id, status, total_amount, order_type, order_time, customer_name FROM orders
            WHERE status NOT IN ('Completed', 'Cancelled')
            ORDER BY order_time ASC
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            print(f"Retrieved {len(results)} active orders")
            return results
            
        except mysql.connector.Error as err:
            print(f"Failed to get active orders: {err}")
            return []
    
    def get_all_menu_items(self):
        if not self.connection:
            print("No database connection")
            return []
        
        try:
            query = "SELECT * FROM menu_items ORDER BY category, name"
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Failed to get menu items: {err}")
            return []
    
    def add_menu_item(self, name, description, price, category, is_available=True, image_path=None):
        if not self.connection:
            print("No database connection")
            return False
        
        try:
            saved_image_path = (image_path or "").strip() or DEFAULT_IMAGE_PATH
            saved_category = self.normalize_category(category)
            query = """
            INSERT INTO menu_items (name, description, price, category, is_available, image_path)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (name, description, price, saved_category, is_available, saved_image_path))
            self.connection.commit()
            item_id = self.cursor.lastrowid
            print(f"✅ Menu item added successfully! ID: {item_id}")
            return item_id
        except mysql.connector.Error as err:
            print(f"Failed to add menu item: {err}")
            self.connection.rollback()
            return False
    
    def update_menu_item(self, item_id, **kwargs):
        if not self.connection:
            print("No database connection")
            return False
        
        if not kwargs:
            print("No fields to update")
            return False
        
        try:
            if 'image_path' in kwargs:
                kwargs['image_path'] = (kwargs['image_path'] or "").strip() or DEFAULT_IMAGE_PATH
            if 'category' in kwargs:
                kwargs['category'] = self.normalize_category(kwargs['category'])

            self.cursor.execute("SELECT id FROM menu_items WHERE id = %s", (item_id,))
            if not self.cursor.fetchone():
                print(f"❌ Menu item #{item_id} not found")
                return False

            set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(item_id)
            
            query = f"UPDATE menu_items SET {set_clause} WHERE id = %s"
            self.cursor.execute(query, values)
            self.connection.commit()
            
            if self.cursor.rowcount > 0:
                print(f"✅ Menu item #{item_id} updated successfully")
                return True
            else:
                print(f"ℹ️ Menu item #{item_id} has no changes to apply")
                return True
                
        except mysql.connector.Error as err:
            print(f"Failed to update menu item: {err}")
            self.connection.rollback()
            return False
    
    def delete_menu_item(self, item_id):
        return self.update_menu_item(item_id, is_available=False)
    
    def get_menu_item_by_id(self, item_id):
        if not self.connection:
            print("No database connection")
            return None
        
        try:
            query = "SELECT * FROM menu_items WHERE id = %s"
            self.cursor.execute(query, (item_id,))
            result = self.cursor.fetchone()
            return result
        except mysql.connector.Error as err:
            print(f"Failed to get menu item: {err}")
            return None
    
    def get_order_details(self, order_id):
        if not self.connection:
            print("No database connection")
            return None
        
        try:
            order_query = "SELECT * FROM orders WHERE id = %s"
            self.cursor.execute(order_query, (order_id,))
            order = self.cursor.fetchone()
            
            if not order:
                return None
            
            items_query = """
            SELECT oi.*, mi.name, mi.category
            FROM order_items oi
            JOIN menu_items mi ON oi.item_id = mi.id
            WHERE oi.order_id = %s
            """
            self.cursor.execute(items_query, (order_id,))
            items = self.cursor.fetchall()
            
            return {
                'order_info': order,
                'items': items
            }
            
        except mysql.connector.Error as err:
            print(f"Failed to get order details: {err}")
            return None
    
    def update_order_status(self, order_id, new_status):
        if not self.connection:
            print("No database connection")
            return False
        
        valid_statuses = ['Pending', 'Preparing', 'Completed', 'Cancelled']
        if new_status not in valid_statuses:
            print(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
            return False
        
        try:
            self.cursor.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
            existing = self.cursor.fetchone()
            if not existing:
                print(f"❌ Order #{order_id} not found")
                return False

            current_status = existing[0]
            if current_status == new_status:
                print(f"ℹ️ Order #{order_id} is already '{new_status}'")
                return True

            query = "UPDATE orders SET status = %s WHERE id = %s"
            self.cursor.execute(query, (new_status, order_id))
            self.connection.commit()
            
            if self.cursor.rowcount > 0:
                print(f"✅ Order #{order_id} status updated to '{new_status}'")
                return True
            else:
                print(f"❌ Order #{order_id} not found")
                return False
                
        except mysql.connector.Error as err:
            print(f"Failed to update order status: {err}")
            self.connection.rollback()
            return False
    
    def cancel_order(self, order_id):
        return self.update_order_status(order_id, 'Cancelled')
    
    def get_all_orders(self, limit=50):
        if not self.connection:
            print("No database connection")
            return []
        
        try:
            query = """
            SELECT id, status, total_amount, order_type, order_time, customer_name FROM orders
            ORDER BY order_time DESC
            LIMIT %s
            """
            self.cursor.execute(query, (limit,))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Failed to get orders: {err}")
            return []
    
    def get_orders_by_status(self, status):
        if not self.connection:
            print("No database connection")
            return []
        
        try:
            query = "SELECT * FROM orders WHERE status = %s ORDER BY order_time"
            self.cursor.execute(query, (status,))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Failed to get orders: {err}")
            return []
    
    def get_categories(self):
        if not self.connection:
            print("No database connection")
            return []
        
        try:
            return MENU_CATEGORIES.copy()
        except mysql.connector.Error as err:
            print(f"Failed to get categories: {err}")
            return []
    
    def search_menu_items(self, search_term):
        if not self.connection:
            print("No database connection")
            return []
        
        try:
            query = """
            SELECT * FROM menu_items 
            WHERE (name LIKE %s OR description LIKE %s) 
            AND is_available = TRUE
            """
            search_pattern = f"%{search_term}%"
            self.cursor.execute(query, (search_pattern, search_pattern))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Failed to search menu items: {err}")
            return []
    
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("Database connection closed")
