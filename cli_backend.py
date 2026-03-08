# cli_backend.py
# Interactive CLI for testing the Fast Food Kiosk backend
# Run this file to test all backend functionality without GUI

import sys
from kiosk_backend import Cart, Database, MENU_CATEGORIES, format_php

class CLIInterface:
    """Interactive CLI for testing backend functionality."""
    
    def __init__(self):
        self.db = Database()
        self.cart = Cart()
        self.current_user = None
        self.category_options = MENU_CATEGORIES.copy()
    
    def display_menu(self, title, options):
        """Displays a menu with numbered options."""
        print(f"\n{'='*50}")
        print(f"{title}")
        print(f"{'='*50}")
        for i, (text, _) in enumerate(options, 1):
            print(f"{i}. {text}")
        print(f"{'='*50}")
    
    def get_choice(self, min_choice, max_choice):
        """Gets valid menu choice from user."""
        while True:
            try:
                choice = int(input(f"\nEnter choice ({min_choice}-{max_choice}): "))
                if min_choice <= choice <= max_choice:
                    return choice
                print(f"Please enter a number between {min_choice} and {max_choice}")
            except ValueError:
                print("Please enter a valid number")
            except KeyboardInterrupt:
                print("\n\nExiting...")
                if self.db.connection:
                    self.db.close()
                sys.exit(0)

    def choose_category(self, current_category=None):
        """Prompts for a category from fixed options."""
        print("\nSelect category:")
        if current_category:
            print("0. Keep current")
        for idx, category in enumerate(self.category_options, 1):
            print(f"{idx}. {category}")

        while True:
            try:
                if current_category:
                    choice = int(input(f"Enter choice (0-{len(self.category_options)}): "))
                    if choice == 0:
                        return current_category
                else:
                    choice = int(input(f"Enter choice (1-{len(self.category_options)}): "))

                if 1 <= choice <= len(self.category_options):
                    return self.category_options[choice - 1]
                print("❌ Invalid category choice")
            except ValueError:
                print("❌ Please enter a valid number")
    
    def main_menu(self):
        """Main menu of the CLI."""
        while True:
            options = [
                ("Customer Mode", self.customer_mode),
                ("Admin Mode", self.staff_login),
                ("Exit", None)
            ]
            
            self.display_menu("FAST FOOD KIOSK - MAIN MENU", options)
            choice = self.get_choice(1, len(options))
            
            if choice == 3:  # Exit
                print("\nThank you for using Fast Food Kiosk!")
                if self.db.connection:
                    self.db.close()
                break
            
            options[choice-1][1]()  # Call selected function
    
    def customer_mode(self):
        """Customer ordering interface."""
        while True:
            options = [
                ("View Menu", self.view_menu),
                ("Add Item to Cart", self.add_to_cart),
                ("View Cart", self.view_cart),
                ("Remove Item from Cart", self.remove_from_cart),
                ("Update Item Quantity", self.update_cart_quantity),
                ("Checkout", self.checkout),
                ("View Order Status", self.view_order_status),
                ("View Queue", self.view_active_orders),
                ("Back to Main Menu", None)
            ]
            
            self.display_menu("CUSTOMER MODE", options)
            choice = self.get_choice(1, len(options))
            
            if choice == 9:  # Back
                break
            
            options[choice-1][1]()
    
    def staff_login(self):
        """Staff login interface."""
        print("\n" + "="*50)
        print("ADMIN LOGIN")
        print("="*50)
        
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        
        if self.db.verify_staff_login(username, password):
            print(f"\n✅ Login successful! Welcome, {username}!")
            self.current_user = username
            self.staff_mode()
        else:
            print("\n❌ Login failed. Invalid credentials.")
            self.current_user = None
    
    def staff_mode(self):
        """Staff management interface."""
        while True:
            options = [
                ("View All Menu Items", self.view_all_menu_items),
                ("Add New Menu Item", self.add_menu_item_ui),
                ("Update Menu Item", self.update_menu_item_ui),
                ("Delete Menu Item", self.delete_menu_item_ui),
                ("View All Orders", self.view_all_orders),
                ("View Active Orders", self.view_active_orders),
                ("View Order Details", self.view_order_details_ui),
                ("Update Order Status", self.update_order_status_ui),
                ("Cancel Order", self.cancel_order_ui),
                ("Logout", None)
            ]
            
            self.display_menu(f"ADMIN MODE - Logged in as: {self.current_user}", options)
            choice = self.get_choice(1, len(options))
            
            if choice == 10:  # Logout
                self.current_user = None
                break
            
            options[choice-1][1]()
    
    # ========== CUSTOMER MODE METHODS ==========
    
    def view_menu(self):
        """Displays available menu items."""
        menu_items = self.db.get_menu()
        
        if not menu_items:
            print("\n❌ No menu items available.")
            return
        
        print("\n" + "="*60)
        print("AVAILABLE MENU")
        print("="*60)
        
        categories = self.db.get_categories()
        for category in categories:
            category_items = [item for item in menu_items if item[4] == category]
            if category_items:
                print(f"\n【{category.upper()}】")
                for item in category_items:
                    print(f"  ID: {item[0]} - {item[1]}")
                    print(f"     {item[2]}")
                    print(f"     {format_php(item[3])}")
                    print()
    
    def add_to_cart(self):
        """Adds an item to the cart."""
        menu_items = self.db.get_menu()
        
        if not menu_items:
            print("\n❌ No menu items available.")
            return
        
        self.view_menu()
        
        try:
            item_id = int(input("\nEnter item ID to add: "))
            quantity = int(input("Enter quantity: "))
            
            if quantity <= 0:
                print("❌ Quantity must be positive")
                return
            
            # Find the selected item
            selected_item = None
            for item in menu_items:
                if item[0] == item_id:
                    selected_item = item
                    break
            
            if selected_item:
                self.cart.add_item(
                    selected_item[0],
                    selected_item[1],
                    selected_item[3],
                    quantity
                )
                print(f"✅ Added to cart: {selected_item[1]} x{quantity}")
            else:
                print(f"❌ Item with ID {item_id} not found")
                
        except ValueError:
            print("❌ Please enter valid numbers")
    
    def view_cart(self):
        """Displays cart contents."""
        self.cart.display_cart()
    
    def remove_from_cart(self):
        """Removes an item from the cart."""
        if self.cart.is_empty():
            print("\n❌ Cart is empty")
            return
        
        self.view_cart()
        
        try:
            item_id = int(input("\nEnter item ID to remove: "))
            if self.cart.remove_item(item_id):
                print("✅ Item removed from cart")
        except ValueError:
            print("❌ Please enter a valid number")
    
    def update_cart_quantity(self):
        """Updates item quantity in cart."""
        if self.cart.is_empty():
            print("\n❌ Cart is empty")
            return
        
        self.view_cart()
        
        try:
            item_id = int(input("\nEnter item ID to update: "))
            new_quantity = int(input("Enter new quantity: "))
            
            if self.cart.update_quantity(item_id, new_quantity):
                print("✅ Quantity updated")
        except ValueError:
            print("❌ Please enter valid numbers")
    
    def checkout(self):
        """Processes checkout and saves order."""
        if self.cart.is_empty():
            print("\n❌ Cart is empty")
            return
        
        self.view_cart()
        
        print("\nSelect order type:")
        print("1. Dine‑in")
        print("2. Takeaway")
        
        try:
            customer_name = input("Enter customer name: ").strip()
            if not customer_name:
                customer_name = "Guest"

            order_type_choice = int(input("Enter choice (1‑2): "))
            if order_type_choice == 1:
                order_type = "Dine‑in"
            elif order_type_choice == 2:
                order_type = "Takeaway"
            else:
                print("❌ Invalid choice")
                return
            
            confirm = input("\nConfirm checkout? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("❌ Checkout cancelled")
                return
            
            total = self.cart.get_total()
            queue_number = self.db.save_new_order(order_type, self.cart.get_items(), total, customer_name)
            
            if queue_number:
                print(f"\n✅ ORDER PLACED SUCCESSFULLY!")
                print(f"   Queue Number: #{queue_number}")
                print(f"   Customer Name: {customer_name}")
                print(f"   Order Type: {order_type}")
                print(f"   Total Amount: {format_php(total)}")
                print(f"\nPlease remember your queue number: #{queue_number}")
                self.cart.clear_cart()
            else:
                print("❌ Failed to save order. Please try again.")
                
        except ValueError:
            print("❌ Please enter valid numbers")
    
    def view_order_status(self):
        """Checks order status by queue number."""
        try:
            order_id = int(input("\nEnter your queue number: "))
            order_details = self.db.get_order_details(order_id)
            
            if order_details:
                order = order_details['order_info']
                items = order_details['items']
                
                print(f"\n{'='*60}")
                print(f"ORDER #{order[0]} – STATUS: {order[1]}")
                print(f"{'='*60}")
                print(f"Customer Name: {order[5] if len(order) > 5 else 'Guest'}")
                print(f"Order Type: {order[3]}")
                print(f"Total: {format_php(order[2])}")
                print(f"Order Time: {order[4]}")
                print(f"\nITEMS:")
                for item in items:
                    item_total = item[3] * float(item[4])
                    print(f"  • {item[5]} x{item[3]} – {format_php(item[4])} each")
                    print(f"    = {format_php(item_total)}")
                print(f"{'='*60}")
            else:
                print(f"❌ Order #{order_id} not found")
                
        except ValueError:
            print("❌ Please enter a valid queue number")
    
    # ========== STAFF MODE METHODS ==========
    
    def view_all_menu_items(self):
        """Displays all menu items (including unavailable)."""
        menu_items = self.db.get_all_menu_items()
        
        if not menu_items:
            print("\n❌ No menu items found.")
            return
        
        print("\n" + "="*70)
        print("ALL MENU ITEMS")
        print("="*70)
        
        categories = self.db.get_categories()
        for category in categories:
            category_items = [item for item in menu_items if item[4] == category]
            if category_items:
                print(f"\n【{category.upper()}】")
                for item in category_items:
                    status = "✅ Available" if item[5] else "❌ Unavailable"
                    print(f"  ID: {item[0]} – {item[1]}")
                    print(f"     {item[2]}")
                    print(f"     {format_php(item[3])} – {status}")
                    print()
    
    def add_menu_item_ui(self):
        """UI for adding a new menu item."""
        print("\n" + "="*50)
        print("ADD NEW MENU ITEM")
        print("="*50)
        
        name = input("Item name: ").strip()
        if not name:
            print("❌ Item name is required")
            return
        
        description = input("Description: ").strip()
        
        try:
            price = float(input("Price (₱): "))
            if price <= 0:
                print("❌ Price must be positive")
                return
        except ValueError:
            print("❌ Please enter a valid price")
            return
        
        category = self.choose_category()
        
        available_input = input("Available? (yes/no, default=yes): ").strip().lower()
        is_available = available_input != 'no'
        
        item_id = self.db.add_menu_item(name, description, price, category, is_available)
        if item_id:
            print(f"✅ Menu item added with ID: {item_id}")
    
    def update_menu_item_ui(self):
        """UI for updating a menu item."""
        menu_items = self.db.get_all_menu_items()
        
        if not menu_items:
            print("\n❌ No menu items found.")
            return
        
        self.view_all_menu_items()
        
        try:
            item_id = int(input("\nEnter item ID to update: "))
            
            # Get current item details
            current_item = self.db.get_menu_item_by_id(item_id)
            if not current_item:
                print(f"❌ Item with ID {item_id} not found")
                return
            
            print(f"\nCurrent details for Item #{item_id}:")
            print(f"  Name: {current_item[1]}")
            print(f"  Description: {current_item[2]}")
            print(f"  Price: {format_php(current_item[3])}")
            print(f"  Category: {current_item[4]}")
            print(f"  Available: {'Yes' if current_item[5] else 'No'}")
            print()
            
            print("Enter new values (press Enter to keep current):")
            
            new_name = input(f"Name [{current_item[1]}]: ").strip()
            if not new_name:
                new_name = current_item[1]
            
            new_description = input(f"Description [{current_item[2]}]: ").strip()
            if not new_description:
                new_description = current_item[2]
            
            new_price_str = input(f"Price (₱) [{current_item[3]}]: ").strip()
            if not new_price_str:
                new_price = current_item[3]
            else:
                try:
                    new_price = float(new_price_str)
                    if new_price <= 0:
                        print("❌ Price must be positive")
                        return
                except ValueError:
                    print("❌ Please enter a valid price")
                    return
            
            new_category = self.choose_category(current_item[4])
            
            available_input = input(f"Available? (yes/no) [{'yes' if current_item[5] else 'no'}]: ").strip().lower()
            if available_input == '':
                new_available = current_item[5]
            else:
                new_available = available_input != 'no'
            
            # Prepare update dictionary
            update_data = {}
            if new_name != current_item[1]:
                update_data['name'] = new_name
            if new_description != current_item[2]:
                update_data['description'] = new_description
            if new_price != current_item[3]:
                update_data['price'] = new_price
            if new_category != current_item[4]:
                update_data['category'] = new_category
            if new_available != current_item[5]:
                update_data['is_available'] = new_available
            
            if not update_data:
                print("❌ No changes made")
                return
            
            if self.db.update_menu_item(item_id, **update_data):
                print(f"✅ Menu item #{item_id} updated successfully")
            else:
                print(f"❌ Failed to update menu item #{item_id}")
                
        except ValueError:
            print("❌ Please enter valid numbers")
    
    def delete_menu_item_ui(self):
        """UI for deleting a menu item."""
        menu_items = self.db.get_all_menu_items()
        
        if not menu_items:
            print("\n❌ No menu items found.")
            return
        
        self.view_all_menu_items()
        
        try:
            item_id = int(input("\nEnter item ID to delete (mark as unavailable): "))
            
            # Get current item details
            current_item = self.db.get_menu_item_by_id(item_id)
            if not current_item:
                print(f"❌ Item with ID {item_id} not found")
                return
            
            print(f"\nItem to delete: {current_item[1]} ({format_php(current_item[3])})")
            confirm = input("\nAre you sure? This will mark the item as unavailable. (yes/no): ").strip().lower()
            
            if confirm == 'yes':
                if self.db.delete_menu_item(item_id):
                    print(f"✅ Menu item #{item_id} marked as unavailable")
                else:
                    print(f"❌ Failed to delete menu item #{item_id}")
            else:
                print("❌ Deletion cancelled")
                
        except ValueError:
            print("❌ Please enter a valid number")
    
    def view_all_orders(self):
        """Displays all orders."""
        orders = self.db.get_all_orders()
        
        if not orders:
            print("\n❌ No orders found.")
            return
        
        print("\n" + "="*70)
        print("ALL ORDERS")
        print("="*70)
        
        for order in orders:
            status_symbol = "🟡" if order[1] == "Pending" else "🔵" if order[1] == "Preparing" else "🟢" if order[1] == "Completed" else "🔴"
            print(f"\n{status_symbol} Order #{order[0]}")
            print(f"   Status: {order[1]}")
            print(f"   Total: {format_php(order[2])}")
            print(f"   Type: {order[3]}")
            print(f"   Time: {order[4]}")
    
    def view_active_orders(self):
        """Displays active orders."""
        orders = self.db.get_active_orders()
        
        if not orders:
            print("\n❌ No active orders found.")
            return
        
        print("\n" + "="*70)
        print("QUEUE")
        print("="*70)
        
        for order in orders:
            status_symbol = "🟡" if order[1] == "Pending" else "🔵"
            print(f"\n{status_symbol} Order #{order[0]}")
            print(f"   Customer: {order[5] if len(order) > 5 else 'Guest'}")
            print(f"   Status: {order[1]}")
            print(f"   Total: {format_php(order[2])}")
            print(f"   Type: {order[3]}")
            print(f"   Time: {order[4]}")

    def view_order_details_ui(self):
        """UI for viewing order details."""
        try:
            order_id = int(input("\nEnter order ID to view details: "))
            order_details = self.db.get_order_details(order_id)
            
            if order_details:
                order = order_details['order_info']
                items = order_details['items']
                
                print(f"\n{'='*60}")
                print(f"ORDER #{order[0]} – DETAILS")
                print(f"{'='*60}")
                print(f"Status: {order[1]}")
                print(f"Total Amount: {format_php(order[2])}")
                print(f"Order Type: {order[3]}")
                print(f"Order Time: {order[4]}")
                print(f"\nITEMS:")
                for item in items:
                    item_total = item[3] * float(item[4])
                    print(f"  • {item[5]} x{item[3]} – {format_php(item[4])} each")
                    print(f"    Category: {item[6]} | Subtotal: {format_php(item_total)}")
                print(f"{'='*60}")
            else:
                print(f"❌ Order #{order_id} not found")
        except ValueError:
            print("❌ Please enter a valid number")

    def update_order_status_ui(self):
        """UI for updating order status."""
        try:
            order_id = int(input("\nEnter order ID to update: "))
            order_details = self.db.get_order_details(order_id)
            
            if not order_details:
                print(f"❌ Order #{order_id} not found")
                return
            
            current_status = order_details['order_info'][1]
            print(f"Current Status: {current_status}")
            
            print("\nSelect new status:")
            print("1. Pending")
            print("2. Preparing")
            print("3. Completed")
            print("4. Cancelled")
            
            choice = self.get_choice(1, 4)
            statuses = ['Pending', 'Preparing', 'Completed', 'Cancelled']
            new_status = statuses[choice-1]
            
            if self.db.update_order_status(order_id, new_status):
                print(f"✅ Order #{order_id} status updated to {new_status}")
            else:
                print(f"❌ Failed to update order #{order_id}")
                
        except ValueError:
            print("❌ Please enter a valid number")

    def cancel_order_ui(self):
        """UI for cancelling an order."""
        try:
            order_id = int(input("\nEnter order ID to cancel: "))
            confirm = input(f"Are you sure you want to cancel order #{order_id}? (yes/no): ").strip().lower()
            
            if confirm == 'yes':
                if self.db.cancel_order(order_id):
                    print(f"✅ Order #{order_id} has been cancelled")
                else:
                    print(f"❌ Failed to cancel order #{order_id}")
            else:
                print("❌ Cancellation aborted")
        except ValueError:
            print("❌ Please enter a valid number")

if __name__ == "__main__":
    cli = CLIInterface()
    try:
        cli.main_menu()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        if cli.db.connection:
            cli.db.close()
        sys.exit(0)