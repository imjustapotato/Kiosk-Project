import os
import shutil
import uuid

import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog

try:
    from PIL import Image
except ImportError:
    Image = None

from kiosk_backend import Cart, Database, MENU_CATEGORIES, format_php


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class KioskApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Kiosk POS")
        self.root.geometry("1600x900")
        self.root.minsize(1280, 760)

        self.colors = {
            "bg": "#0f172a",
            "surface": "#111827",
            "panel": "#1f2937",
            "card": "#273449",
            "muted": "#9ca3af",
            "text": "#f3f4f6",
            "primary": "#0ea5e9",
            "primary_hover": "#0284c7",
            "success": "#16a34a",
            "success_hover": "#15803d",
            "danger": "#dc2626",
            "danger_hover": "#b91c1c",
            "warning": "#d97706",
        }

        self.db = Database()
        self.customer_cart = Cart()
        self.admin_draft_cart = Cart()

        self.current_user = None
        self.order_type = "Dine-in"
        self.category_options = MENU_CATEGORIES.copy()
        self.active_view = "landing"
        self.admin_view = "queue"
        self.customer_search = ""
        self.customer_category = "All"
        self.admin_search = ""
        self.admin_category = "All"

        self.main_container = ctk.CTkFrame(self.root, fg_color=self.colors["bg"])
        self.main_container.pack(fill="both", expand=True)

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.images_dir = os.path.join(self.base_dir, "src")
        self.placeholder_image_rel = "src/no-image.jpg"
        self.placeholder_image_abs = os.path.join(self.base_dir, "src", "no-image.jpg")
        self._menu_image_cache = {}

        self.show_landing_view()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.db.close()
        self.root.destroy()

    def clear_view(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def menu_row_to_dict(self, row):
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2] or "No description",
            "price": float(row[3]),
            "category": row[4] or self.category_options[0],
            "is_available": bool(row[5]),
            "image_path": row[6] if len(row) > 6 and row[6] else self.placeholder_image_rel,
        }

    def normalize_image_path(self, image_path):
        if not image_path:
            return ""
        return image_path.replace("\\", "/").strip()

    def resolve_image_path(self, image_path):
        normalized = self.normalize_image_path(image_path)
        if not normalized:
            return None
        if os.path.isabs(normalized):
            return normalized
        return os.path.join(self.base_dir, normalized.replace("/", os.sep))

    def get_fallback_image_path(self, image_path):
        candidate = self.resolve_image_path(image_path)
        if candidate and os.path.exists(candidate):
            return candidate
        if os.path.exists(self.placeholder_image_abs):
            return self.placeholder_image_abs
        return None

    def load_menu_image(self, image_path, size=(180, 180)):
        resolved = self.get_fallback_image_path(image_path)
        if not resolved or Image is None:
            return None

        cache_key = f"{resolved}|{size[0]}x{size[1]}"
        cached = self._menu_image_cache.get(cache_key)
        if cached:
            return cached

        try:
            with Image.open(resolved) as source:
                prepared = source.convert("RGB")
            image = ctk.CTkImage(light_image=prepared, dark_image=prepared, size=size)
            self._menu_image_cache[cache_key] = image
            return image
        except Exception:
            return None

    def copy_image_to_assets(self, source_path):
        if not source_path:
            return self.placeholder_image_rel

        extension = os.path.splitext(source_path)[1].lower()
        if extension not in {".jpg", ".jpeg", ".png"}:
            messagebox.showwarning("Invalid Image", "Only JPG, JPEG, and PNG files are allowed.")
            return None

        try:
            os.makedirs(self.images_dir, exist_ok=True)
            stem = os.path.splitext(os.path.basename(source_path))[0]
            safe_stem = "".join(ch for ch in stem if ch.isalnum() or ch in ("-", "_")) or "item"
            target_name = f"{safe_stem}_{uuid.uuid4().hex[:8]}{extension}"
            target_abs = os.path.join(self.images_dir, target_name)
            shutil.copy2(source_path, target_abs)
            return f"src/{target_name}"
        except OSError as err:
            messagebox.showerror("Image Copy Failed", f"Could not copy image file.\n{err}")
            return None

    def order_row_to_dict(self, row):
        return {
            "id": row[0],
            "status": row[1],
            "total_amount": float(row[2]),
            "order_type": row[3],
            "order_time": str(row[4]),
            "customer_name": row[5] if len(row) > 5 else "Guest",
        }

    def status_color(self, status):
        mapping = {
            "Pending": self.colors["warning"],
            "Preparing": self.colors["primary"],
            "Completed": self.colors["success"],
            "Cancelled": self.colors["danger"],
        }
        return mapping.get(status, self.colors["muted"])

    def action_button(self, parent, text, command, color=None, hover=None, width=0):
        kwargs = {
            "master": parent,
            "text": text,
            "command": command,
            "height": 36,
            "corner_radius": 10,
            "font": ("Segoe UI", 14, "bold"),
        }
        if width:
            kwargs["width"] = width
        if color:
            kwargs["fg_color"] = color
        if hover:
            kwargs["hover_color"] = hover
        return ctk.CTkButton(**kwargs)

    def title_bar(self, title, subtitle, right_buttons):
        header = ctk.CTkFrame(self.main_container, fg_color=self.colors["surface"], height=78, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="y", padx=18, pady=10)
        ctk.CTkLabel(left, text=title, font=("Segoe UI", 28, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        ctk.CTkLabel(left, text=subtitle, font=("Segoe UI", 13), text_color=self.colors["muted"]).pack(anchor="w")

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", padx=18, pady=16)
        for btn in right_buttons:
            self.action_button(right, btn[0], btn[1], btn[2], btn[3], width=130).pack(side="right", padx=6)

    def show_landing_view(self):
        self.active_view = "landing"
        self.clear_view()
        self.customer_cart.clear_cart()

        hero = ctk.CTkFrame(self.main_container, fg_color="transparent")
        hero.pack(expand=True)

        ctk.CTkLabel(hero, text="FAST FOOD KIOSK", font=("Segoe UI", 50, "bold")).pack(pady=(20, 4))
        ctk.CTkLabel(
            hero,
            text="Choose your order mode to start",
            font=("Segoe UI", 18),
            text_color=self.colors["muted"],
        ).pack(pady=(0, 34))

        btn_row = ctk.CTkFrame(hero, fg_color="transparent")
        btn_row.pack()

        self.action_button(
            btn_row,
            "DINE IN",
            lambda: self.show_customer_view("Dine-in"),
            color=self.colors["primary"],
            hover=self.colors["primary_hover"],
            width=360,
        ).pack(side="left", padx=16, ipady=46)

        self.action_button(
            btn_row,
            "TAKE OUT",
            lambda: self.show_customer_view("Takeaway"),
            color="#f97316",
            hover="#ea580c",
            width=360,
        ).pack(side="left", padx=16, ipady=46)

        self.action_button(
            self.main_container,
            "Staff Login",
            self.show_admin_login,
            color="transparent",
            hover=self.colors["panel"],
            width=110,
        ).pack(side="bottom", pady=16)

    def show_customer_view(self, order_type=None):
        self.active_view = "customer"
        if order_type:
            self.order_type = order_type
        self.clear_view()
        self.title_bar(
            "Customer POS",
            f"Order Type: {self.order_type}",
            [
                ("Back", self.show_landing_view, self.colors["panel"], "#374151"),
                ("View Queue", self.show_queue_popup, self.colors["panel"], "#374151"),
            ],
        )

        body = ctk.CTkFrame(self.main_container, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=14, pady=14)
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_columnconfigure(2, weight=0)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(body, fg_color=self.colors["surface"], width=230)
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        left.grid_propagate(False)

        self.build_customer_left_panel(left)

        center = ctk.CTkFrame(body, fg_color=self.colors["surface"])
        center.grid(row=0, column=1, sticky="nsew", padx=(0, 12))
        self.build_customer_menu_grid(center)

        right = ctk.CTkFrame(body, fg_color=self.colors["surface"], width=430)
        right.grid(row=0, column=2, sticky="nse", padx=0)
        right.grid_propagate(False)
        self.build_cart_panel(right, self.customer_cart, self.checkout_customer_order)

    def build_customer_left_panel(self, parent):
        ctk.CTkLabel(parent, text="Customer Actions", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=14, pady=(14, 6))

        order_mode = ctk.CTkSegmentedButton(
            parent,
            values=["Dine-in", "Takeaway"],
            command=self.change_order_type,
        )
        order_mode.pack(fill="x", padx=14, pady=(4, 16))
        order_mode.set(self.order_type)

        ctk.CTkLabel(parent, text="Search", text_color=self.colors["muted"]).pack(anchor="w", padx=14)
        search = ctk.CTkEntry(parent, placeholder_text="Search item or description")
        search.pack(fill="x", padx=14, pady=(4, 10))
        search.insert(0, self.customer_search)

        def on_search(*_):
            self.customer_search = search.get().strip()
            self.show_customer_view()

        search.bind("<Return>", on_search)

        categories = ["All"] + self.category_options
        category_menu = ctk.CTkOptionMenu(parent, values=categories, command=self.change_customer_category)
        category_menu.pack(fill="x", padx=14, pady=4)
        category_menu.set(self.customer_category if self.customer_category in categories else "All")

        self.action_button(parent, "Apply Filter", on_search, self.colors["primary"], self.colors["primary_hover"]).pack(fill="x", padx=14, pady=(8, 4))
        self.action_button(parent, "Track Order", self.track_order_popup, self.colors["panel"], "#374151").pack(fill="x", padx=14, pady=4)
        self.action_button(parent, "Clear Cart", self.clear_customer_cart, self.colors["danger"], self.colors["danger_hover"]).pack(fill="x", padx=14, pady=4)
        self.action_button(parent, "Refresh", self.show_customer_view, self.colors["panel"], "#374151").pack(fill="x", padx=14, pady=4)

    def build_customer_menu_grid(self, parent):
        title = ctk.CTkFrame(parent, fg_color="transparent")
        title.pack(fill="x", padx=14, pady=(14, 8))
        ctk.CTkLabel(title, text="Menu", font=("Segoe UI", 22, "bold")).pack(anchor="w")

        items = self.fetch_customer_items()
        if not items:
            ctk.CTkLabel(parent, text="No items found for current filter.", text_color=self.colors["muted"]).pack(pady=22)
            return

        grid = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        col_count = 3 if self.root.winfo_width() >= 1500 else 2
        for col in range(col_count):
            grid.grid_columnconfigure(col, weight=1)

        for idx, item in enumerate(items):
            row = idx // col_count
            col = idx % col_count
            self.render_menu_card(grid, item).grid(row=row, column=col, sticky="nsew", padx=8, pady=8)

    def fetch_customer_items(self):
        rows = self.db.search_menu_items(self.customer_search) if self.customer_search else self.db.get_menu()
        items = [self.menu_row_to_dict(row) for row in rows]
        if self.customer_category != "All":
            items = [item for item in items if item["category"] == self.customer_category]
        return items

    def render_menu_card(self, parent, item):
        card = ctk.CTkFrame(parent, fg_color=self.colors["card"], corner_radius=14)

        image_placeholder = ctk.CTkFrame(card, fg_color="#334155", width=180, height=180, corner_radius=10)
        image_placeholder.pack(fill="x", padx=12, pady=(12, 8))
        image_placeholder.pack_propagate(False)

        menu_image = self.load_menu_image(item.get("image_path"), size=(180, 180))
        if menu_image:
            preview = ctk.CTkLabel(image_placeholder, text="", image=menu_image)
            preview.image = menu_image
            preview.pack(expand=True)
        else:
            ctk.CTkLabel(
                image_placeholder,
                text="No Image\nAvailable",
                font=("Segoe UI", 14),
                text_color=self.colors["muted"],
            ).pack(expand=True)

        ctk.CTkLabel(card, text=item["name"], font=("Segoe UI", 18, "bold"), anchor="w").pack(fill="x", padx=12)
        ctk.CTkLabel(card, text=item["description"], font=("Segoe UI", 12), text_color=self.colors["muted"], justify="left", wraplength=260).pack(fill="x", padx=12, pady=(4, 4))
        ctk.CTkLabel(card, text=item["category"], font=("Segoe UI", 11), text_color="#93c5fd").pack(anchor="w", padx=12)
        ctk.CTkLabel(card, text=format_php(item["price"]), font=("Segoe UI", 18, "bold"), text_color="#22d3ee").pack(anchor="w", padx=12, pady=(4, 10))

        self.action_button(
            card,
            "Add to Cart",
            lambda i=item: self.add_to_cart_increment(self.customer_cart, i),
            color=self.colors["primary"],
            hover=self.colors["primary_hover"],
        ).pack(fill="x", padx=12, pady=(0, 12))
        return card

    def build_cart_panel(self, parent, cart, checkout_handler):
        ctk.CTkLabel(parent, text="Order Details", font=("Segoe UI", 21, "bold")).pack(anchor="w", padx=14, pady=(14, 6))

        cart_list = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        cart_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        items = cart.get_items()
        if not items:
            ctk.CTkLabel(cart_list, text="Cart is empty.", text_color=self.colors["muted"]).pack(pady=18)
        else:
            for item in items:
                self.render_cart_item_card(cart_list, cart, item)

        footer = ctk.CTkFrame(parent, fg_color=self.colors["panel"], corner_radius=12)
        footer.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(footer, text=f"Items: {cart.get_item_count()}", font=("Segoe UI", 13), text_color=self.colors["muted"]).pack(anchor="w", padx=12, pady=(10, 0))
        ctk.CTkLabel(footer, text=f"Total: {format_php(cart.get_total())}", font=("Segoe UI", 24, "bold"), text_color="#67e8f9").pack(anchor="w", padx=12, pady=(2, 8))
        self.action_button(footer, "Checkout", checkout_handler, self.colors["success"], self.colors["success_hover"]).pack(fill="x", padx=12, pady=(0, 12))

    def render_cart_item_card(self, parent, cart, item):
        row = ctk.CTkFrame(parent, fg_color=self.colors["card"], corner_radius=10)
        row.pack(fill="x", pady=6)

        text = ctk.CTkFrame(row, fg_color="transparent")
        text.pack(fill="x", expand=True, padx=10, pady=(10, 2))
        ctk.CTkLabel(text, text=item["name"], font=("Segoe UI", 14, "bold")).pack(anchor="w")
        subtotal = float(item["price"]) * int(item["quantity"])
        ctk.CTkLabel(
            text,
            text=f"{format_php(item['price'])} x {item['quantity']} = {format_php(subtotal)}",
            text_color=self.colors["muted"],
        ).pack(anchor="w")

        controls = ctk.CTkFrame(row, fg_color="transparent")
        controls.pack(fill="x", padx=10, pady=(0, 10))

        qty_controls = ctk.CTkFrame(controls, fg_color="transparent")
        qty_controls.pack(side="left")
        ctk.CTkButton(
            qty_controls,
            text="-",
            width=34,
            command=lambda: self.adjust_cart_qty(cart, item["item_id"], item["quantity"] - 1),
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            qty_controls,
            text="+",
            width=34,
            command=lambda: self.adjust_cart_qty(cart, item["item_id"], item["quantity"] + 1),
        ).pack(side="left")

        self.action_button(
            controls,
            "Remove",
            lambda: self.remove_from_cart(cart, item["item_id"]),
            self.colors["danger"],
            self.colors["danger_hover"],
            width=92,
        ).pack(side="right")

    def change_order_type(self, value):
        self.order_type = value
        self.show_customer_view()

    def change_customer_category(self, value):
        self.customer_category = value

    def add_to_cart_increment(self, cart, item):
        for existing in cart.get_items():
            if existing["item_id"] == item["id"]:
                cart.update_quantity(item["id"], existing["quantity"] + 1)
                self.refresh_active_cart_panel()
                return
        cart.add_item(item["id"], item["name"], item["price"], 1)
        self.refresh_active_cart_panel()

    def adjust_cart_qty(self, cart, item_id, quantity):
        cart.update_quantity(item_id, quantity)
        self.refresh_active_cart_panel()

    def remove_from_cart(self, cart, item_id):
        cart.remove_item(item_id)
        self.refresh_active_cart_panel()

    def clear_customer_cart(self):
        self.customer_cart.clear_cart()
        self.show_customer_view()

    def refresh_active_cart_panel(self):
        if self.active_view == "customer":
            self.show_customer_view()
        elif self.active_view == "admin":
            self.show_admin_view()

    def checkout_customer_order(self):
        if self.customer_cart.is_empty():
            messagebox.showwarning("Empty Cart", "Add at least one item before checkout.")
            return

        name_input = ctk.CTkInputDialog(text="Enter customer name", title="Checkout").get_input()
        customer_name = (name_input or "Guest").strip() or "Guest"

        if not messagebox.askyesno("Confirm Checkout", "Place this order now?"):
            return

        queue = self.db.save_new_order(
            self.order_type,
            self.customer_cart.get_items(),
            self.customer_cart.get_total(),
            customer_name,
        )
        if queue:
            messagebox.showinfo("Order Placed", f"Queue Number: #{queue}\nCustomer: {customer_name}")
            self.customer_cart.clear_cart()
            self.show_landing_view()
        else:
            messagebox.showerror("Checkout Failed", "Unable to save order. Check database connection.")

    def show_queue_popup(self):
        orders = [self.order_row_to_dict(row) for row in self.db.get_active_orders()]
        if not orders:
            messagebox.showinfo("Queue", "No active orders in queue.")
            return

        lines = []
        for order in orders:
            lines.append(f"#{order['id']} | {order['customer_name']} | {order['status']} | {format_php(order['total_amount'])}")
        messagebox.showinfo("Queue", "\n".join(lines))

    def track_order_popup(self):
        order_id = simpledialog.askinteger("Track Order", "Enter queue number:", parent=self.root)
        if not order_id:
            return
        details = self.db.get_order_details(order_id)
        if not details:
            messagebox.showerror("Not Found", f"Order #{order_id} does not exist.")
            return

        order = details["order_info"]
        lines = [
            f"Order #{order[0]}",
            f"Customer: {order[5] if len(order) > 5 else 'Guest'}",
            f"Status: {order[1]}",
            f"Type: {order[3]}",
            f"Total: {format_php(float(order[2]))}",
            "",
            "Items:",
        ]
        for item in details["items"]:
            lines.append(f"- {item[5]} x{item[3]} ({format_php(float(item[4]))} each)")
        messagebox.showinfo("Order Details", "\n".join(lines))

    def show_admin_login(self):
        self.active_view = "admin-login"
        self.clear_view()

        wrapper = ctk.CTkFrame(self.main_container, fg_color="transparent")
        wrapper.pack(expand=True)
        card = ctk.CTkFrame(wrapper, fg_color=self.colors["surface"], width=420, height=320, corner_radius=14)
        card.pack(padx=20, pady=20)
        card.pack_propagate(False)

        ctk.CTkLabel(card, text="Admin Login", font=("Segoe UI", 28, "bold")).pack(pady=(26, 20))
        username_entry = ctk.CTkEntry(card, placeholder_text="Username")
        username_entry.pack(fill="x", padx=34, pady=8)
        password_entry = ctk.CTkEntry(card, placeholder_text="Password", show="*")
        password_entry.pack(fill="x", padx=34, pady=8)

        action_row = ctk.CTkFrame(card, fg_color="transparent")
        action_row.pack(fill="x", padx=34, pady=(12, 0))
        self.action_button(action_row, "Back", self.show_landing_view, self.colors["panel"], "#374151").pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.action_button(
            action_row,
            "Login",
            lambda: self.handle_admin_login(username_entry.get().strip(), password_entry.get().strip()),
            self.colors["primary"],
            self.colors["primary_hover"],
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

    def handle_admin_login(self, username, password):
        if not username or not password:
            messagebox.showwarning("Missing Credentials", "Enter both username and password.")
            return
        if self.db.verify_staff_login(username, password):
            self.current_user = username
            self.show_admin_view()
        else:
            messagebox.showerror("Login Failed", "Invalid admin credentials.")

    def show_admin_view(self):
        self.active_view = "admin"
        self.clear_view()
        self.title_bar(
            "Admin POS",
            f"Signed in as: {self.current_user or 'admin'}",
            [
                ("Logout", self.show_landing_view, self.colors["panel"], "#374151"),
                ("Refresh", self.show_admin_view, self.colors["panel"], "#374151"),
            ],
        )

        body = ctk.CTkFrame(self.main_container, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=14, pady=14)
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_columnconfigure(2, weight=0)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(body, fg_color=self.colors["surface"], width=250)
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        left.grid_propagate(False)
        self.build_admin_left_panel(left)

        center = ctk.CTkFrame(body, fg_color=self.colors["surface"])
        center.grid(row=0, column=1, sticky="nsew", padx=(0, 12))

        right = ctk.CTkFrame(body, fg_color=self.colors["surface"], width=430)
        right.grid(row=0, column=2, sticky="nse")
        right.grid_propagate(False)

        if self.admin_view == "queue":
            self.build_admin_queue_view(center, right)
        elif self.admin_view == "manual-order":
            self.build_admin_manual_order_view(center, right)
        elif self.admin_view == "inventory":
            self.build_admin_inventory_view(center, right)
        else:
            self.admin_view = "queue"
            self.build_admin_queue_view(center, right)

    def build_admin_left_panel(self, parent):
        ctk.CTkLabel(parent, text="Admin Controls", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=14, pady=(14, 10))
        self.action_button(parent, "Queue", lambda: self.set_admin_view("queue"), self.colors["primary"], self.colors["primary_hover"]).pack(fill="x", padx=14, pady=4)
        self.action_button(parent, "Manual Order", lambda: self.set_admin_view("manual-order"), self.colors["panel"], "#374151").pack(fill="x", padx=14, pady=4)
        self.action_button(parent, "Inventory", lambda: self.set_admin_view("inventory"), self.colors["panel"], "#374151").pack(fill="x", padx=14, pady=4)
        self.action_button(parent, "View All Orders", self.show_orders_history_popup, self.colors["panel"], "#374151").pack(fill="x", padx=14, pady=4)

    def set_admin_view(self, view_name):
        self.admin_view = view_name
        self.show_admin_view()

    def build_admin_queue_view(self, center, right):
        ctk.CTkLabel(center, text="Active Queue", font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=14, pady=(14, 8))
        queue_wrap = ctk.CTkScrollableFrame(center, fg_color="transparent")
        queue_wrap.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        orders = [self.order_row_to_dict(row) for row in self.db.get_active_orders()]
        if not orders:
            ctk.CTkLabel(queue_wrap, text="No active orders.", text_color=self.colors["muted"]).pack(pady=16)

        for order in orders:
            card = ctk.CTkFrame(queue_wrap, fg_color=self.colors["card"], corner_radius=12)
            card.pack(fill="x", padx=4, pady=6)
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(12, 4))
            ctk.CTkLabel(top, text=f"Order #{order['id']}", font=("Segoe UI", 18, "bold")).pack(side="left")
            ctk.CTkLabel(top, text=order["status"], text_color=self.status_color(order["status"]), font=("Segoe UI", 13, "bold")).pack(side="right")

            ctk.CTkLabel(card, text=f"Customer: {order['customer_name']} | {order['order_type']}", text_color=self.colors["muted"]).pack(anchor="w", padx=12)
            ctk.CTkLabel(card, text=f"Total: {format_php(order['total_amount'])}", font=("Segoe UI", 14)).pack(anchor="w", padx=12, pady=(0, 8))

            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.pack(fill="x", padx=10, pady=(0, 10))
            self.action_button(actions, "Set Preparing", lambda oid=order["id"]: self.update_order_and_refresh(oid, "Preparing"), self.colors["warning"], "#b45309").pack(side="left", padx=4)
            self.action_button(actions, "Set Completed", lambda oid=order["id"]: self.update_order_and_refresh(oid, "Completed"), self.colors["success"], self.colors["success_hover"]).pack(side="left", padx=4)
            self.action_button(actions, "Cancel Order", lambda oid=order["id"]: self.update_order_and_refresh(oid, "Cancelled"), self.colors["danger"], self.colors["danger_hover"]).pack(side="left", padx=4)
            self.action_button(actions, "View Details", lambda oid=order["id"]: self.show_order_details_popup(oid), self.colors["panel"], "#374151").pack(side="left", padx=4)

        self.build_admin_summary_panel(right)

    def build_admin_summary_panel(self, right):
        ctk.CTkLabel(right, text="Dashboard", font=("Segoe UI", 21, "bold")).pack(anchor="w", padx=14, pady=(14, 8))
        orders = [self.order_row_to_dict(row) for row in self.db.get_all_orders(limit=200)]

        total_orders = len(orders)
        active_orders = len([o for o in orders if o["status"] not in ("Completed", "Cancelled")])
        completed_orders = len([o for o in orders if o["status"] == "Completed"])
        cancelled_orders = len([o for o in orders if o["status"] == "Cancelled"])

        for label, value in [
            ("Total Orders", total_orders),
            ("Active", active_orders),
            ("Completed", completed_orders),
            ("Cancelled", cancelled_orders),
        ]:
            box = ctk.CTkFrame(right, fg_color=self.colors["card"], corner_radius=10)
            box.pack(fill="x", padx=12, pady=6)
            ctk.CTkLabel(box, text=label, text_color=self.colors["muted"], font=("Segoe UI", 12)).pack(anchor="w", padx=12, pady=(8, 0))
            ctk.CTkLabel(box, text=str(value), font=("Segoe UI", 28, "bold")).pack(anchor="w", padx=12, pady=(0, 8))

    def build_admin_manual_order_view(self, center, right):
        ctk.CTkLabel(center, text="Manual Order Builder (Draft)", font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=14, pady=(14, 8))

        top_filters = ctk.CTkFrame(center, fg_color="transparent")
        top_filters.pack(fill="x", padx=12, pady=(0, 8))

        admin_search = ctk.CTkEntry(top_filters, placeholder_text="Search menu items")
        admin_search.pack(side="left", fill="x", expand=True, padx=(0, 8))
        admin_search.insert(0, self.admin_search)
        admin_search.bind("<Return>", lambda *_: self.apply_admin_search(admin_search.get().strip()))

        categories = ["All"] + self.category_options
        admin_cat = ctk.CTkOptionMenu(top_filters, values=categories, command=self.change_admin_category)
        admin_cat.pack(side="left")
        admin_cat.set(self.admin_category if self.admin_category in categories else "All")

        self.action_button(top_filters, "Apply", lambda: self.apply_admin_search(admin_search.get().strip()), self.colors["primary"], self.colors["primary_hover"], width=90).pack(side="left", padx=(8, 0))

        grid = ctk.CTkScrollableFrame(center, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        items = self.fetch_admin_items()
        col_count = 3 if self.root.winfo_width() >= 1500 else 2
        for col in range(col_count):
            grid.grid_columnconfigure(col, weight=1)

        for idx, item in enumerate(items):
            row = idx // col_count
            col = idx % col_count
            card = self.render_menu_card(grid, item)
            btn = card.winfo_children()[-1]
            btn.configure(command=lambda i=item: self.add_to_cart_increment(self.admin_draft_cart, i), text="Add to Draft")
            card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)

        ctk.CTkLabel(right, text="Draft Order", font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=14, pady=(14, 8))

        mode = ctk.CTkSegmentedButton(right, values=["Dine-in", "Takeaway"], command=self.set_manual_order_type)
        mode.pack(fill="x", padx=12, pady=(0, 10))
        mode.set(self.order_type)

        self.build_cart_panel(right, self.admin_draft_cart, self.submit_admin_draft_order)

    def fetch_admin_items(self):
        rows = self.db.search_menu_items(self.admin_search) if self.admin_search else self.db.get_menu()
        items = [self.menu_row_to_dict(row) for row in rows]
        if self.admin_category != "All":
            items = [item for item in items if item["category"] == self.admin_category]
        return items

    def apply_admin_search(self, value):
        self.admin_search = value
        self.show_admin_view()

    def change_admin_category(self, value):
        self.admin_category = value

    def set_manual_order_type(self, value):
        self.order_type = value

    def submit_admin_draft_order(self):
        if self.admin_draft_cart.is_empty():
            messagebox.showwarning("Empty Draft", "Add items to draft first.")
            return
        customer_name = ctk.CTkInputDialog(text="Customer name for manual order", title="Manual Order").get_input()
        customer_name = (customer_name or "Guest").strip() or "Guest"

        if not messagebox.askyesno("Submit Draft", "Save this draft as a pending order?"):
            return

        queue = self.db.save_new_order(
            self.order_type,
            self.admin_draft_cart.get_items(),
            self.admin_draft_cart.get_total(),
            customer_name,
        )
        if queue:
            messagebox.showinfo("Draft Submitted", f"Order #{queue} created successfully.")
            self.admin_draft_cart.clear_cart()
            self.admin_view = "queue"
            self.show_admin_view()
        else:
            messagebox.showerror("Failed", "Could not save draft order.")

    def build_admin_inventory_view(self, center, right):
        ctk.CTkLabel(center, text="Inventory Management", font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=14, pady=(14, 8))

        form = ctk.CTkFrame(center, fg_color=self.colors["panel"], corner_radius=12)
        form.pack(fill="x", padx=12, pady=(0, 12))

        for col in range(5):
            form.grid_columnconfigure(col, weight=1)

        name_entry = ctk.CTkEntry(form, placeholder_text="Item Name")
        desc_entry = ctk.CTkEntry(form, placeholder_text="Description")
        price_entry = ctk.CTkEntry(form, placeholder_text="Price")
        category_entry = ctk.CTkOptionMenu(form, values=self.category_options)
        category_entry.set(self.category_options[0])
        name_entry.grid(row=0, column=0, padx=6, pady=(10, 6), sticky="ew")
        desc_entry.grid(row=0, column=1, padx=6, pady=(10, 6), sticky="ew")
        price_entry.grid(row=0, column=2, padx=6, pady=(10, 6), sticky="ew")
        category_entry.grid(row=0, column=3, padx=6, pady=(10, 6), sticky="ew")

        add_image_state = {"source": None}
        image_label = ctk.CTkLabel(form, text="Image: Placeholder (no-image.jpg)", text_color=self.colors["muted"])

        def pick_new_image():
            selected = filedialog.askopenfilename(
                title="Select Item Image",
                filetypes=[("Image files", "*.jpg *.jpeg *.png")],
                initialdir=self.images_dir if os.path.isdir(self.images_dir) else self.base_dir,
            )
            if selected:
                add_image_state["source"] = selected
                image_label.configure(text=f"Image: {os.path.basename(selected)}")

        def clear_new_image():
            add_image_state["source"] = None
            image_label.configure(text="Image: Placeholder (no-image.jpg)")

        self.action_button(
            form,
            "Choose Image",
            pick_new_image,
            self.colors["panel"],
            "#374151",
            width=120,
        ).grid(row=1, column=0, padx=6, pady=(0, 10), sticky="w")

        self.action_button(
            form,
            "Use Placeholder",
            clear_new_image,
            self.colors["panel"],
            "#374151",
            width=140,
        ).grid(row=1, column=1, padx=6, pady=(0, 10), sticky="w")

        image_label.grid(row=1, column=2, columnspan=2, padx=6, pady=(0, 10), sticky="w")

        self.action_button(
            form,
            "Add New Item",
            lambda: self.create_inventory_item(
                name_entry,
                desc_entry,
                price_entry,
                category_entry,
                add_image_state["source"],
            ),
            self.colors["primary"],
            self.colors["primary_hover"],
            width=130,
        ).grid(row=0, column=4, rowspan=2, padx=6, pady=10, sticky="ns")

        scroll = ctk.CTkScrollableFrame(center, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        rows = [self.menu_row_to_dict(row) for row in self.db.get_all_menu_items()]
        if not rows:
            ctk.CTkLabel(scroll, text="No inventory items.", text_color=self.colors["muted"]).pack(pady=16)

        for item in rows:
            card = ctk.CTkFrame(scroll, fg_color=self.colors["card"], corner_radius=12)
            card.pack(fill="x", pady=6)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=10, pady=(10, 4))
            ctk.CTkLabel(top, text=f"#{item['id']} {item['name']}", font=("Segoe UI", 16, "bold")).pack(side="left")
            status_text = "Available" if item["is_available"] else "Unavailable"
            ctk.CTkLabel(top, text=status_text, text_color="#93c5fd").pack(side="right")

            current_image_text = os.path.basename(item.get("image_path") or self.placeholder_image_rel)
            ctk.CTkLabel(
                card,
                text=f"Image: {current_image_text}",
                text_color=self.colors["muted"],
            ).pack(anchor="w", padx=10, pady=(0, 4))

            image_change_state = {"mode": "keep", "source": None}
            image_actions = ctk.CTkFrame(card, fg_color="transparent")
            image_actions.pack(fill="x", padx=10, pady=(0, 6))

            image_status = ctk.CTkLabel(image_actions, text="No image change", text_color=self.colors["muted"])

            def choose_existing_image(state=image_change_state, status=image_status):
                selected = filedialog.askopenfilename(
                    title="Select New Item Image",
                    filetypes=[("Image files", "*.jpg *.jpeg *.png")],
                    initialdir=self.images_dir if os.path.isdir(self.images_dir) else self.base_dir,
                )
                if selected:
                    state["mode"] = "new"
                    state["source"] = selected
                    status.configure(text=f"Selected: {os.path.basename(selected)}")

            def use_existing_placeholder(state=image_change_state, status=image_status):
                state["mode"] = "placeholder"
                state["source"] = None
                status.configure(text="Will use placeholder")

            self.action_button(
                image_actions,
                "Change Image",
                choose_existing_image,
                self.colors["panel"],
                "#374151",
                width=120,
            ).pack(side="left")

            self.action_button(
                image_actions,
                "Use Placeholder",
                use_existing_placeholder,
                self.colors["panel"],
                "#374151",
                width=140,
            ).pack(side="left", padx=(8, 10))
            image_status.pack(side="left")

            edit = ctk.CTkFrame(card, fg_color="transparent")
            edit.pack(fill="x", padx=10, pady=(0, 10))
            name = ctk.CTkEntry(edit)
            name.insert(0, item["name"])
            desc = ctk.CTkEntry(edit)
            desc.insert(0, item["description"])
            price = ctk.CTkEntry(edit)
            price.insert(0, str(item["price"]))
            category = ctk.CTkOptionMenu(edit, values=self.category_options)
            category.set(item["category"] if item["category"] in self.category_options else self.category_options[0])
            for widget in [name, desc, price, category]:
                widget.pack(side="left", fill="x", expand=True, padx=4)

            self.action_button(
                edit,
                "Update",
                lambda i=item["id"], n=name, d=desc, p=price, c=category, image_state=image_change_state: self.update_inventory_item(
                    i,
                    n.get(),
                    d.get(),
                    p.get(),
                    c.get(),
                    image_state,
                ),
                self.colors["primary"],
                self.colors["primary_hover"],
                width=86,
            ).pack(side="left", padx=4)

            self.action_button(
                edit,
                "Delete",
                lambda i=item["id"]: self.delete_inventory_item(i),
                self.colors["danger"],
                self.colors["danger_hover"],
                width=86,
            ).pack(side="left", padx=4)

        ctk.CTkLabel(right, text="Inventory Notes", font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=14, pady=(14, 8))
        notes = [
            "- Add form is at the top.",
            "- Update and Delete are on each item card.",
            "- Delete is soft delete (set unavailable).",
            "- Supported images: JPG, JPEG, PNG.",
            "- Missing images use no-image.jpg fallback.",
        ]
        note_box = ctk.CTkFrame(right, fg_color=self.colors["card"], corner_radius=10)
        note_box.pack(fill="x", padx=12)
        for line in notes:
            ctk.CTkLabel(note_box, text=line, anchor="w", justify="left", text_color=self.colors["muted"]).pack(fill="x", padx=10, pady=4)

    def create_inventory_item(self, name_entry, desc_entry, price_entry, category_entry, image_source_path=None):
        name = name_entry.get().strip()
        description = desc_entry.get().strip()
        category = category_entry.get().strip() or self.category_options[0]
        if not name:
            messagebox.showwarning("Invalid Input", "Item name is required.")
            return
        try:
            price = float(price_entry.get().strip())
            if price <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Input", "Enter a valid positive price.")
            return

        image_path = self.copy_image_to_assets(image_source_path)
        if image_path is None:
            return

        item_id = self.db.add_menu_item(name, description, price, category, True, image_path)
        if item_id:
            messagebox.showinfo("Added", f"Item #{item_id} added.")
            self.show_admin_view()
        else:
            messagebox.showerror("Failed", "Could not add item.")

    def update_inventory_item(self, item_id, name, description, price_text, category, image_choice=None):
        if not name.strip():
            messagebox.showwarning("Invalid Input", "Name cannot be empty.")
            return
        try:
            price = float(price_text)
            if price <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Input", "Enter a valid positive price.")
            return

        update_fields = {
            "name": name.strip(),
            "description": description.strip(),
            "price": price,
            "category": (category.strip() or self.category_options[0]),
        }

        if image_choice:
            if image_choice.get("mode") == "new":
                image_path = self.copy_image_to_assets(image_choice.get("source"))
                if image_path is None:
                    return
                update_fields["image_path"] = image_path
            elif image_choice.get("mode") == "placeholder":
                update_fields["image_path"] = self.placeholder_image_rel

        ok = self.db.update_menu_item(item_id, **update_fields)
        if ok:
            messagebox.showinfo("Updated", f"Item #{item_id} updated.")
            self.show_admin_view()
        else:
            messagebox.showerror("Failed", f"Could not update item #{item_id}.")

    def delete_inventory_item(self, item_id):
        if not messagebox.askyesno("Confirm Delete", f"Mark item #{item_id} as unavailable?"):
            return
        if self.db.delete_menu_item(item_id):
            messagebox.showinfo("Deleted", f"Item #{item_id} marked unavailable.")
            self.show_admin_view()
        else:
            messagebox.showerror("Failed", f"Could not delete item #{item_id}.")

    def update_order_and_refresh(self, order_id, status):
        if self.db.update_order_status(order_id, status):
            self.show_admin_view()
        else:
            messagebox.showerror("Update Failed", f"Could not set order #{order_id} to {status}.")

    def show_order_details_popup(self, order_id):
        details = self.db.get_order_details(order_id)
        if not details:
            messagebox.showerror("Not Found", f"Order #{order_id} was not found.")
            return

        order = details["order_info"]
        lines = [
            f"Order #{order[0]}",
            f"Customer: {order[5] if len(order) > 5 else 'Guest'}",
            f"Status: {order[1]}",
            f"Type: {order[3]}",
            f"Total: {format_php(float(order[2]))}",
            f"Time: {order[4]}",
            "",
            "Items:",
        ]
        for item in details["items"]:
            lines.append(f"- {item[5]} x{item[3]} ({format_php(float(item[4]))})")
        messagebox.showinfo("Order Details", "\n".join(lines))

    def show_orders_history_popup(self):
        orders = [self.order_row_to_dict(row) for row in self.db.get_all_orders(limit=100)]
        if not orders:
            messagebox.showinfo("Orders", "No orders found.")
            return
        lines = [
            f"#{order['id']} | {order['customer_name']} | {order['status']} | {format_php(order['total_amount'])}"
            for order in orders
        ]
        messagebox.showinfo("Recent Orders", "\n".join(lines[:40]))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = KioskApp()
    app.run()
