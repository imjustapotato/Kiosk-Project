# test_backend.py
# Simple test script for the kiosk backend - can be removed later for GUI
# All prices in Philippine Peso (₱)

import sys

# Import our backend classes
try:
    from kiosk_backend import Cart, Database, format_php
except ImportError:
    print("Error: kiosk_backend.py not found in the same directory")
    sys.exit(1)

def test_cart_class():
    """Test the Cart class functionality"""
    print("=== Testing Cart Class ===")
    cart = Cart()
    
    # Test adding items
    cart.add_item(101, "Cheeseburger", 5.99, 2)
    cart.add_item(102, "French Fries", 2.99, 1)
    cart.add_item(103, "Soda", 1.99, 3)
    
    # Test total calculation
    total = cart.get_total()
    print(f"Cart total should be: 5.99*2 + 2.99*1 + 1.99*3 = ${total:.2f}")
    
    # Test clearing cart
    print(f"Items in cart before clear: {len(cart.items)}")
    cart.clear_cart()
    print(f"Items in cart after clear: {len(cart.items)}")
    
    # Add some items again for later tests
    cart.add_item(201, "Chicken Sandwich", 6.49, 1)
    cart.add_item(202, "Onion Rings", 3.49, 2)
    
    return cart

def test_database_connection():
    """Test database connection and basic operations"""
    print("\n=== Testing Database Connection ===")
    db = Database()
    
    if not db.connection:
        print("WARNING: Could not connect to database")
        print("Make sure:")
        print("1. XAMPP is running with MySQL")
        print("2. Database 'kiosk_db' exists")
        print("3. Tables are created (run the SQL script if needed)")
        return None
    
    print("✓ Database connection successful")
    return db

def test_staff_login(db):
    """Test staff login functionality"""
    print("\n=== Testing Staff Login ===")
    
    # Test with dummy credentials (will fail unless you have data)
    test_username = input("Enter test username (or press Enter to skip): ").strip()
    
    if test_username:
        test_password = input("Enter test password: ").strip()
        result = db.verify_staff_login(test_username, test_password)
        print(f"Login result for '{test_username}': {'SUCCESS' if result else 'FAILED'}")
    else:
        print("Skipping login test (no credentials provided)")
    
    return db

def test_menu_retrieval(db):
    """Test getting menu items from database"""
    print("\n=== Testing Menu Retrieval ===")
    
    try:
        menu_items = db.get_menu()
        print(f"Retrieved {len(menu_items)} menu items")
        
        if menu_items:
            print("\nFirst 3 menu items (if available):")
            for i, item in enumerate(menu_items[:3]):
                print(f"  {i+1}. {item}")
        else:
            print("No menu items found or table might be empty")
    except Exception as e:
        print(f"Error getting menu: {e}")
        print("Make sure 'menu_items' table exists with columns: id, name, price, is_available")
    
    return db

def test_order_saving(db, cart):
    """Test saving a new order to database"""
    print("\n=== Testing Order Saving ===")
    
    if not cart.items:
        print("Cart is empty - adding test items")
        cart.add_item(301, "Test Burger", 4.99, 2)
        cart.add_item(302, "Test Drink", 1.49, 1)
    
    total = cart.get_total()
    print(f"Cart total for test order: ${total:.2f}")
    print(f"Number of items in cart: {len(cart.items)}")
    
    response = input("\nDo you want to save this test order? (yes/no): ").strip().lower()
    
    if response == 'yes':
        try:
            queue_number = db.save_new_order("Test", cart.items, total)
            if queue_number:
                print(f"✓ Test order saved successfully! Queue number: {queue_number}")
            else:
                print("✗ Failed to save test order")
        except Exception as e:
            print(f"Error saving order: {e}")
            print("Make sure 'orders' and 'order_items' tables exist")
    else:
        print("Skipping order save test")
    
    return db

def test_active_orders(db):
    """Test retrieving active orders"""
    print("\n=== Testing Active Orders Retrieval ===")
    
    try:
        active_orders = db.get_active_orders()
        print(f"Number of active orders: {len(active_orders)}")
        
        if active_orders:
            print("\nActive orders (first 3):")
            for i, order in enumerate(active_orders[:3]):
                print(f"  {i+1}. Order ID: {order[0]}, Status: {order[1]}, Total: ${order[2]:.2f}")
    except Exception as e:
        print(f"Error getting active orders: {e}")

def main():
    """Main test function"""
    print("FAST FOOD KIOSK - BACKEND TEST")
    print("=" * 40)
    
    # Test 1: Cart class (no database needed)
    cart = test_cart_class()
    
    # Test 2: Database connection
    db = test_database_connection()
    
    if db and db.connection:
        # Test 3: Staff login
        db = test_staff_login(db)
        
        # Test 4: Menu retrieval
        db = test_menu_retrieval(db)
        
        # Test 5: Order saving
        db = test_order_saving(db, cart)
        
        # Test 6: Active orders
        test_active_orders(db)
        
        # Close database connection
        db.close()
        print("\n✓ Database connection closed")
    
    print("\n" + "=" * 40)
    print("TEST COMPLETE")
    print("\nNext steps:")
    print("1. Run the SQL script to create database tables")
    print("2. Add some test data to the tables")
    print("3. Run this test again to verify everything works")
    print("4. When ready, remove this test file and build your GUI")

if __name__ == "__main__":
    main()