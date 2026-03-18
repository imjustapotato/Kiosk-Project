import os
import shutil
import sys
import uuid
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QFileDialog,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from kiosk_backend import Cart, Database, MENU_CATEGORIES, format_php


class KioskQtApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kiosk POS")
        self.resize(1600, 920)
        self.setMinimumSize(1280, 760)

        self.db = Database()
        self.customer_cart = Cart()
        self.admin_manual_cart = Cart()
        self.customer_cart_image_map: Dict[int, str] = {}
        self.admin_manual_cart_image_map: Dict[int, str] = {}

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.images_dir = os.path.join(self.base_dir, "src")
        self.placeholder_image_rel = "src/no-image.jpg"
        self.placeholder_image_abs = os.path.join(self.base_dir, "src", "no-image.jpg")
        self.image_cache: Dict[str, QPixmap] = {}

        self.order_type = "Dine-in"
        self.customer_search = ""
        self.customer_category = "All"
        self.category_options = MENU_CATEGORIES.copy()
        self.current_user = None
        self.admin_view = "queue"
        self.admin_manual_order_type = "Dine-in"
        self.admin_manual_search = ""
        self.admin_manual_category = "All"
        self.inventory_search = ""
        self.inventory_category = "All"
        self.inventory_add_image_source: Optional[str] = None
        self._max_image_cache_items = 1024

        self._manual_refresh_timer = QTimer(self)
        self._manual_refresh_timer.setSingleShot(True)
        self._manual_refresh_timer.timeout.connect(self._refresh_admin_manual_if_visible)

        self._inventory_refresh_timer = QTimer(self)
        self._inventory_refresh_timer.setSingleShot(True)
        self._inventory_refresh_timer.timeout.connect(self._refresh_inventory_if_visible)

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._apply_manual_panel_sizing)

        self._last_customer_cart_signature = None
        self._last_admin_manual_cart_signature = None
        self._last_customer_view_signature = None
        self._last_manual_view_signature = None
        self._last_inventory_view_signature = None

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.root_layout = QVBoxLayout(self.central)
        self.root_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        self.root_layout.addWidget(self.stack)

        self._build_landing_page()
        self._build_customer_page()
        self._build_admin_login_page()
        self._build_admin_page()

        self._apply_styles()
        self.show_landing()

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QWidget {
                background: #111315;
                color: #f5f5f5;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QFrame#surface {
                background: #1b1f24;
                border-radius: 12px;
                border: 1px solid #2a3138;
            }
            QFrame#card {
                background: #222831;
                border-radius: 12px;
                border: 1px solid #313943;
            }
            QLineEdit, QComboBox, QListWidget {
                background: #171b20;
                border: 1px solid #343d47;
                border-radius: 8px;
                padding: 6px;
                color: #f5f5f5;
                selection-background-color: #f97316;
                selection-color: #0f1114;
            }
            QLabel {
                color: #f5f5f5;
                background: transparent;
            }
            QPushButton {
                background: #f97316;
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: 600;
                color: #14171a;
            }
            QPushButton:hover {
                background: #ea580c;
            }
            QPushButton[variant="ghost"] {
                background: #252d36;
                color: #f5f5f5;
            }
            QPushButton[variant="danger"] {
                background: #dc2626;
                color: #fef2f2;
            }
            QPushButton[variant="success"] {
                background: #16a34a;
                color: #f0fdf4;
            }
            QPushButton[variant="mode"] {
                background: #2a3138;
                color: #fdba74;
                border: 1px solid #f97316;
            }
            """
        )

    def _build_landing_page(self):
        self.page_landing = QWidget()
        layout = QVBoxLayout(self.page_landing)
        layout.setContentsMargins(24, 24, 24, 24)

        center = QVBoxLayout()
        center.setAlignment(Qt.AlignCenter)

        title = QLabel("WELCOME! TO ORDERING KIOSK")
        title.setStyleSheet("font-size: 48px; font-weight: 800;")
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("Please select your order type to get started.")
        subtitle.setStyleSheet("font-size: 18px; color: #9ca3af;")
        subtitle.setAlignment(Qt.AlignCenter)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(18)

        dine_in_btn = QPushButton("DINE IN")
        dine_in_btn.setFixedSize(320, 120)
        dine_in_btn.clicked.connect(lambda: self.show_customer("Dine-in"))

        takeaway_btn = QPushButton("TAKE OUT")
        takeaway_btn.setFixedSize(320, 120)
        takeaway_btn.setStyleSheet("QPushButton { background: #f97316; border-radius: 10px; font-weight: 700; } QPushButton:hover { background: #ea580c; }")
        takeaway_btn.clicked.connect(lambda: self.show_customer("Takeaway"))

        btn_row.addWidget(dine_in_btn)
        btn_row.addWidget(takeaway_btn)

        admin_btn = QPushButton("Staff Login")
        admin_btn.setProperty("variant", "ghost")
        admin_btn.setFixedWidth(180)
        admin_btn.clicked.connect(self.show_admin_login)

        center.addWidget(title)
        center.addWidget(subtitle)
        center.addSpacing(24)
        center.addLayout(btn_row)
        center.addSpacing(18)
        center.addWidget(admin_btn, alignment=Qt.AlignCenter)

        layout.addLayout(center)
        self.stack.addWidget(self.page_landing)

    def _build_customer_page(self):
        self.page_customer = QWidget()
        page_layout = QVBoxLayout(self.page_customer)
        page_layout.setContentsMargins(14, 14, 14, 14)
        page_layout.setSpacing(10)

        top_bar = QFrame()
        top_bar.setObjectName("surface")
        top_layout = QHBoxLayout(top_bar)

        title = QLabel("Customer POS")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")

        self.mode_indicator = QPushButton("Mode: Dine-in")
        self.mode_indicator.setProperty("variant", "mode")
        self.mode_indicator.setEnabled(False)

        back_btn = QPushButton("Back")
        back_btn.setProperty("variant", "ghost")
        back_btn.clicked.connect(self.show_landing)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setProperty("variant", "ghost")
        refresh_btn.clicked.connect(self.refresh_customer_view)

        queue_btn = QPushButton("View Queue")
        queue_btn.setProperty("variant", "ghost")
        queue_btn.clicked.connect(self._show_customer_queue_popup)

        track_btn = QPushButton("Track Order")
        track_btn.setProperty("variant", "ghost")
        track_btn.clicked.connect(self._show_customer_track_order_popup)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search item or description")
        self.search_input.returnPressed.connect(self._apply_customer_filter)

        self.category_menu = QComboBox()
        self.category_menu.addItems(["All"] + self.category_options)
        self.category_menu.currentTextChanged.connect(self._set_customer_category)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply_customer_filter)

        clear_cart_btn = QPushButton("Clear Cart")
        clear_cart_btn.setProperty("variant", "danger")
        clear_cart_btn.clicked.connect(self._clear_customer_cart)

        top_layout.addWidget(title)
        top_layout.addWidget(self.search_input, 1)
        top_layout.addWidget(self.category_menu)
        top_layout.addWidget(apply_btn)
        top_layout.addWidget(self.mode_indicator)
        top_layout.addStretch()

        body = QHBoxLayout()
        body.setSpacing(12)

        self.left_panel = QFrame()
        self.left_panel.setObjectName("surface")
        self.left_panel.setFixedWidth(260)
        left_layout = QVBoxLayout(self.left_panel)

        left_title = QLabel("Session")
        left_title.setStyleSheet("font-size: 18px; font-weight: 700;")
        left_layout.addWidget(left_title)

        self.session_mode_label = QLabel("Order Mode: Dine-in")
        self.session_mode_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #fdba74;")
        left_layout.addWidget(self.session_mode_label)

        left_layout.addWidget(queue_btn)
        left_layout.addWidget(track_btn)
        left_layout.addWidget(refresh_btn)
        left_layout.addWidget(clear_cart_btn)
        left_layout.addWidget(back_btn)
        left_layout.addStretch()

        self.menu_panel = QFrame()
        self.menu_panel.setObjectName("surface")
        menu_layout = QVBoxLayout(self.menu_panel)

        menu_header = QLabel("Menu")
        menu_header.setStyleSheet("font-size: 22px; font-weight: 700;")

        self.menu_scroll = QScrollArea()
        self.menu_scroll.setWidgetResizable(True)
        self.menu_container = QWidget()
        self.menu_grid = QGridLayout(self.menu_container)
        self.menu_grid.setSpacing(10)
        self.menu_scroll.setWidget(self.menu_container)

        menu_layout.addWidget(menu_header)
        menu_layout.addWidget(self.menu_scroll)

        self.cart_panel = QFrame()
        self.cart_panel.setObjectName("surface")
        self.cart_panel.setFixedWidth(390)
        cart_layout = QVBoxLayout(self.cart_panel)

        cart_title = QLabel("Order Details")
        cart_title.setStyleSheet("font-size: 21px; font-weight: 700;")

        self.cart_list = QListWidget()
        self.cart_total_label = QLabel("Total: PHP 0.00")
        self.cart_total_label.setStyleSheet("font-size: 24px; font-weight: 800; color: #67e8f9;")

        checkout_btn = QPushButton("Checkout")
        checkout_btn.setProperty("variant", "success")
        checkout_btn.clicked.connect(self._checkout_customer_order)

        cart_layout.addWidget(cart_title)
        cart_layout.addWidget(self.cart_list)
        cart_layout.addWidget(self.cart_total_label)
        cart_layout.addWidget(checkout_btn)

        body.addWidget(self.left_panel)
        body.addWidget(self.menu_panel)
        body.addWidget(self.cart_panel)

        page_layout.addWidget(top_bar)
        page_layout.addLayout(body)

        self.stack.addWidget(self.page_customer)

    def _build_admin_login_page(self):
        self.page_admin_login = QWidget()
        outer = QVBoxLayout(self.page_admin_login)
        outer.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("surface")
        card.setFixedSize(460, 300)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Admin Login")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")

        self.admin_user_input = QLineEdit()
        self.admin_user_input.setPlaceholderText("Username")

        self.admin_pass_input = QLineEdit()
        self.admin_pass_input.setEchoMode(QLineEdit.Password)
        self.admin_pass_input.setPlaceholderText("Password")

        btn_row = QHBoxLayout()
        back_btn = QPushButton("Back")
        back_btn.setProperty("variant", "ghost")
        back_btn.clicked.connect(self.show_landing)

        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self._handle_admin_login)

        btn_row.addWidget(back_btn)
        btn_row.addWidget(login_btn)

        layout.addWidget(title)
        layout.addSpacing(8)
        layout.addWidget(self.admin_user_input)
        layout.addWidget(self.admin_pass_input)
        layout.addStretch()
        layout.addLayout(btn_row)

        outer.addWidget(card)
        self.stack.addWidget(self.page_admin_login)

    def _build_admin_page(self):
        self.page_admin = QWidget()
        page_layout = QVBoxLayout(self.page_admin)
        page_layout.setContentsMargins(14, 14, 14, 14)
        page_layout.setSpacing(10)

        top_bar = QFrame()
        top_bar.setObjectName("surface")
        top_layout = QHBoxLayout(top_bar)

        title = QLabel("Admin POS")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        self.admin_subtitle = QLabel("Signed in as: admin")
        self.admin_subtitle.setStyleSheet("color: #9ca3af;")

        subtitle_wrap = QVBoxLayout()
        subtitle_wrap.addWidget(title)
        subtitle_wrap.addWidget(self.admin_subtitle)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setProperty("variant", "ghost")
        refresh_btn.clicked.connect(self._refresh_admin_active_view)

        logout_btn = QPushButton("Logout")
        logout_btn.setProperty("variant", "ghost")
        logout_btn.clicked.connect(self.show_landing)

        top_layout.addLayout(subtitle_wrap)
        top_layout.addStretch()
        top_layout.addWidget(refresh_btn)
        top_layout.addWidget(logout_btn)

        body = QHBoxLayout()
        body.setSpacing(12)

        self.admin_left_panel = QFrame()
        self.admin_left_panel.setObjectName("surface")
        self.admin_left_panel.setFixedWidth(250)
        left_layout = QVBoxLayout(self.admin_left_panel)

        left_title = QLabel("Admin Controls")
        left_title.setStyleSheet("font-size: 18px; font-weight: 700;")
        left_layout.addWidget(left_title)

        self.admin_queue_btn = QPushButton("Queue")
        self.admin_queue_btn.clicked.connect(lambda: self._set_admin_view("queue"))

        self.admin_manual_btn = QPushButton("Create Order")
        self.admin_manual_btn.setProperty("variant", "ghost")
        self.admin_manual_btn.clicked.connect(lambda: self._set_admin_view("manual-order"))

        self.admin_inventory_btn = QPushButton("Inventory")
        self.admin_inventory_btn.setProperty("variant", "ghost")
        self.admin_inventory_btn.clicked.connect(lambda: self._set_admin_view("inventory"))

        self.admin_history_btn = QPushButton("View All Orders")
        self.admin_history_btn.setProperty("variant", "ghost")
        self.admin_history_btn.clicked.connect(self._show_orders_history_popup)

        left_layout.addWidget(self.admin_queue_btn)
        left_layout.addWidget(self.admin_manual_btn)
        left_layout.addWidget(self.admin_inventory_btn)
        left_layout.addWidget(self.admin_history_btn)
        left_layout.addStretch()

        self.admin_content_stack = QStackedWidget()

        self.queue_page = QWidget()
        queue_layout = QHBoxLayout(self.queue_page)
        queue_layout.setContentsMargins(0, 0, 0, 0)
        queue_layout.setSpacing(12)

        self.queue_center_panel = QFrame()
        self.queue_center_panel.setObjectName("surface")
        center_layout = QVBoxLayout(self.queue_center_panel)
        queue_title = QLabel("Active Queue")
        queue_title.setStyleSheet("font-size: 22px; font-weight: 700;")
        center_layout.addWidget(queue_title)

        self.queue_scroll = QScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        self.queue_container = QWidget()
        self.queue_list_layout = QVBoxLayout(self.queue_container)
        self.queue_list_layout.setSpacing(8)
        self.queue_scroll.setWidget(self.queue_container)
        center_layout.addWidget(self.queue_scroll)

        self.queue_right_panel = QFrame()
        self.queue_right_panel.setObjectName("surface")
        self.queue_right_panel.setFixedWidth(380)
        right_layout = QVBoxLayout(self.queue_right_panel)
        right_title = QLabel("Dashboard")
        right_title.setStyleSheet("font-size: 21px; font-weight: 700;")
        right_layout.addWidget(right_title)
        self.summary_total = QLabel("Total Orders: 0")
        self.summary_active = QLabel("Active: 0")
        self.summary_completed = QLabel("Completed: 0")
        self.summary_cancelled = QLabel("Cancelled: 0")
        for label in [self.summary_total, self.summary_active, self.summary_completed, self.summary_cancelled]:
            label.setStyleSheet("font-size: 16px; font-weight: 600;")
            right_layout.addWidget(label)
        right_layout.addStretch()

        queue_layout.addWidget(self.queue_center_panel)
        queue_layout.addWidget(self.queue_right_panel)

        self.manual_page = QWidget()
        manual_layout = QVBoxLayout(self.manual_page)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        manual_layout.setSpacing(10)

        self.manual_action_bar = QFrame()
        self.manual_action_bar.setObjectName("surface")
        manual_action_layout = QHBoxLayout(self.manual_action_bar)

        manual_page_title = QLabel("Create Order")
        manual_page_title.setStyleSheet("font-size: 22px; font-weight: 700;")

        self.create_order_mode_label = QLabel("Mode: Dine-in")
        self.create_order_mode_label.setStyleSheet("font-size: 14px; color: #fdba74; font-weight: 700;")

        self.manual_mode_toggle_btn = QPushButton("Switch to Takeaway")
        self.manual_mode_toggle_btn.setProperty("variant", "ghost")
        self.manual_mode_toggle_btn.clicked.connect(self._toggle_admin_manual_order_type)

        self.admin_manual_search_input = QLineEdit()
        self.admin_manual_search_input.setPlaceholderText("Search menu items")
        self.admin_manual_search_input.setText(self.admin_manual_search)
        self.admin_manual_search_input.returnPressed.connect(self._apply_admin_manual_filter)
        self.admin_manual_search_input.textChanged.connect(self._set_admin_manual_search)

        self.admin_manual_category_menu = QComboBox()
        self.admin_manual_category_menu.addItems(["All"] + self.category_options)
        self.admin_manual_category_menu.setCurrentText(self.admin_manual_category)
        self.admin_manual_category_menu.currentTextChanged.connect(self._set_admin_manual_category)

        self.manual_refresh_btn = QPushButton("Refresh Items")
        self.manual_refresh_btn.setProperty("variant", "ghost")
        self.manual_refresh_btn.clicked.connect(self._apply_admin_manual_filter)

        self.manual_clear_btn = QPushButton("Clear Draft")
        self.manual_clear_btn.setProperty("variant", "danger")
        self.manual_clear_btn.clicked.connect(self._clear_admin_manual_cart)

        self.manual_submit_btn = QPushButton("Submit Draft")
        self.manual_submit_btn.setProperty("variant", "success")
        self.manual_submit_btn.clicked.connect(self._submit_admin_manual_order)

        manual_action_layout.addWidget(manual_page_title)
        manual_action_layout.addWidget(self.create_order_mode_label)
        manual_action_layout.addWidget(self.admin_manual_search_input, 1)
        manual_action_layout.addWidget(self.admin_manual_category_menu)
        manual_action_layout.addStretch()
        manual_action_layout.addWidget(self.manual_refresh_btn)
        manual_action_layout.addWidget(self.manual_mode_toggle_btn)
        manual_action_layout.addWidget(self.manual_clear_btn)
        manual_action_layout.addWidget(self.manual_submit_btn)

        self.manual_body_layout = QHBoxLayout()
        self.manual_body_layout.setSpacing(12)

        self.manual_center_panel = QFrame()
        self.manual_center_panel.setObjectName("surface")
        manual_center_layout = QVBoxLayout(self.manual_center_panel)

        self.admin_manual_menu_scroll = QScrollArea()
        self.admin_manual_menu_scroll.setWidgetResizable(True)
        self.admin_manual_menu_container = QWidget()
        self.admin_manual_menu_grid = QGridLayout(self.admin_manual_menu_container)
        self.admin_manual_menu_grid.setSpacing(10)
        self.admin_manual_menu_scroll.setWidget(self.admin_manual_menu_container)
        manual_center_layout.addWidget(self.admin_manual_menu_scroll)

        self.manual_right_panel = QFrame()
        self.manual_right_panel.setObjectName("surface")
        manual_right_layout = QVBoxLayout(self.manual_right_panel)

        manual_cart_title = QLabel("Draft Order")
        manual_cart_title.setStyleSheet("font-size: 21px; font-weight: 700;")
        self.admin_manual_cart_list = QListWidget()
        self.admin_manual_cart_list.itemDoubleClicked.connect(self._edit_admin_manual_selected_qty)

        manual_cart_actions = QHBoxLayout()
        edit_qty_btn = QPushButton("Edit Qty")
        edit_qty_btn.setProperty("variant", "ghost")
        edit_qty_btn.clicked.connect(self._edit_admin_manual_selected_qty)
        remove_item_btn = QPushButton("Remove Item")
        remove_item_btn.setProperty("variant", "danger")
        remove_item_btn.clicked.connect(self._remove_admin_manual_selected_item)
        manual_cart_actions.addWidget(edit_qty_btn)
        manual_cart_actions.addWidget(remove_item_btn)

        self.admin_manual_cart_total = QLabel("Total: PHP 0.00")
        self.admin_manual_cart_total.setStyleSheet("font-size: 24px; font-weight: 800; color: #67e8f9;")

        manual_right_layout.addWidget(manual_cart_title)
        manual_right_layout.addWidget(self.admin_manual_cart_list)
        manual_right_layout.addLayout(manual_cart_actions)
        manual_right_layout.addWidget(self.admin_manual_cart_total)
        manual_layout.addWidget(self.manual_action_bar)
        self.manual_body_layout.addWidget(self.manual_center_panel, 1)
        self.manual_body_layout.addWidget(self.manual_right_panel)
        manual_layout.addLayout(self.manual_body_layout)

        self.inventory_page = QWidget()
        inventory_layout = QVBoxLayout(self.inventory_page)
        inventory_layout.setContentsMargins(0, 0, 0, 0)
        inventory_layout.setSpacing(10)

        inventory_action_bar = QFrame()
        inventory_action_bar.setObjectName("surface")
        inventory_action_layout = QHBoxLayout(inventory_action_bar)
        inventory_title = QLabel("Inventory Management")
        inventory_title.setStyleSheet("font-size: 22px; font-weight: 700;")
        inventory_refresh_btn = QPushButton("Refresh")
        inventory_refresh_btn.setProperty("variant", "ghost")
        inventory_refresh_btn.clicked.connect(self.refresh_inventory_view)
        inventory_action_layout.addWidget(inventory_title)
        inventory_action_layout.addStretch()
        inventory_action_layout.addWidget(inventory_refresh_btn)

        self.inventory_form_panel = QFrame()
        self.inventory_form_panel.setObjectName("surface")
        form_layout = QGridLayout(self.inventory_form_panel)
        form_layout.setHorizontalSpacing(8)
        form_layout.setVerticalSpacing(8)

        self.inventory_name_input = QLineEdit()
        self.inventory_name_input.setPlaceholderText("Item Name")
        self.inventory_desc_input = QLineEdit()
        self.inventory_desc_input.setPlaceholderText("Description")
        self.inventory_price_input = QLineEdit()
        self.inventory_price_input.setPlaceholderText("Price")
        self.inventory_category_input = QComboBox()
        self.inventory_category_input.addItems(self.category_options)
        if self.category_options:
            self.inventory_category_input.setCurrentText(self.category_options[0])

        self.inventory_add_image_status = QLabel("Image: Placeholder (no-image.jpg)")
        self.inventory_add_image_status.setStyleSheet("color: #9ca3af;")

        add_choose_image_btn = QPushButton("Choose Image")
        add_choose_image_btn.setProperty("variant", "ghost")
        add_choose_image_btn.clicked.connect(self._pick_inventory_add_image)

        add_placeholder_btn = QPushButton("Use Placeholder")
        add_placeholder_btn.setProperty("variant", "ghost")
        add_placeholder_btn.clicked.connect(self._use_inventory_add_placeholder)

        add_submit_btn = QPushButton("Add New Item")
        add_submit_btn.setProperty("variant", "success")
        add_submit_btn.clicked.connect(self._create_inventory_item)

        form_layout.addWidget(self.inventory_name_input, 0, 0)
        form_layout.addWidget(self.inventory_desc_input, 0, 1)
        form_layout.addWidget(self.inventory_price_input, 0, 2)
        form_layout.addWidget(self.inventory_category_input, 0, 3)
        form_layout.addWidget(add_submit_btn, 0, 4, 2, 1)
        form_layout.addWidget(add_choose_image_btn, 1, 0)
        form_layout.addWidget(add_placeholder_btn, 1, 1)
        form_layout.addWidget(self.inventory_add_image_status, 1, 2, 1, 2)

        self.inventory_filter_panel = QFrame()
        self.inventory_filter_panel.setObjectName("surface")
        filter_layout = QHBoxLayout(self.inventory_filter_panel)

        self.inventory_search_input = QLineEdit()
        self.inventory_search_input.setPlaceholderText("Search inventory")
        self.inventory_search_input.textChanged.connect(self._set_inventory_search)

        self.inventory_category_menu = QComboBox()
        self.inventory_category_menu.addItems(["All"] + self.category_options)
        self.inventory_category_menu.setCurrentText(self.inventory_category)
        self.inventory_category_menu.currentTextChanged.connect(self._set_inventory_category)

        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.inventory_search_input, 1)
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.inventory_category_menu)

        self.inventory_scroll = QScrollArea()
        self.inventory_scroll.setWidgetResizable(True)
        self.inventory_container = QWidget()
        self.inventory_items_layout = QVBoxLayout(self.inventory_container)
        self.inventory_items_layout.setSpacing(8)
        self.inventory_scroll.setWidget(self.inventory_container)

        inventory_layout.addWidget(inventory_action_bar)
        inventory_layout.addWidget(self.inventory_form_panel)
        inventory_layout.addWidget(self.inventory_filter_panel)
        inventory_layout.addWidget(self.inventory_scroll)

        self.admin_content_stack.addWidget(self.queue_page)
        self.admin_content_stack.addWidget(self.manual_page)
        self.admin_content_stack.addWidget(self.inventory_page)

        self._apply_manual_panel_sizing()

        body.addWidget(self.admin_left_panel)
        body.addWidget(self.admin_content_stack)

        page_layout.addWidget(top_bar)
        page_layout.addLayout(body)

        self.stack.addWidget(self.page_admin)

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "manual_right_panel"):
            self._resize_timer.start(120)

    def show_landing(self):
        self.customer_cart.clear_cart()
        self.customer_cart_image_map.clear()
        self.search_input.setText("")
        self.customer_search = ""
        self.customer_category = "All"
        self.category_menu.setCurrentText("All")
        self.stack.setCurrentWidget(self.page_landing)

    def show_customer(self, order_type: str):
        self.order_type = order_type
        self.mode_indicator.setText(f"Mode: {order_type}")
        self.session_mode_label.setText(f"Order Mode: {order_type}")
        self.create_order_mode_label.setText(f"Mode: {self.admin_manual_order_type}")
        next_mode = "Takeaway" if self.admin_manual_order_type == "Dine-in" else "Dine-in"
        self.manual_mode_toggle_btn.setText(f"Switch to {next_mode}")
        self.stack.setCurrentWidget(self.page_customer)
        self.refresh_customer_view()

    def show_admin_login(self):
        self.admin_user_input.clear()
        self.admin_pass_input.clear()
        self.stack.setCurrentWidget(self.page_admin_login)

    def show_admin_dashboard(self):
        self.admin_subtitle.setText(f"Signed in as: {self.current_user or 'admin'}")
        self.stack.setCurrentWidget(self.page_admin)
        self._set_admin_view("queue")

    def _set_admin_view(self, view_name: str):
        self.admin_view = view_name
        self.admin_queue_btn.setProperty("variant", "ghost")
        self.admin_manual_btn.setProperty("variant", "ghost")
        self.admin_inventory_btn.setProperty("variant", "ghost")

        if view_name == "queue":
            self.admin_queue_btn.setProperty("variant", "")
            self.admin_content_stack.setCurrentWidget(self.queue_page)
            self._refresh_admin_queue_view()
        elif view_name == "manual-order":
            self.admin_manual_btn.setProperty("variant", "")
            self.admin_content_stack.setCurrentWidget(self.manual_page)
            self.create_order_mode_label.setText(f"Mode: {self.admin_manual_order_type}")
            next_mode = "Takeaway" if self.admin_manual_order_type == "Dine-in" else "Dine-in"
            self.manual_mode_toggle_btn.setText(f"Switch to {next_mode}")
            self._apply_manual_panel_sizing()
            self.refresh_admin_manual_view()
        elif view_name == "inventory":
            self.admin_inventory_btn.setProperty("variant", "")
            self.admin_content_stack.setCurrentWidget(self.inventory_page)
            self.refresh_inventory_view()
        else:
            self.admin_view = "queue"
            self.admin_queue_btn.setProperty("variant", "")
            self.admin_content_stack.setCurrentWidget(self.queue_page)
            self._refresh_admin_queue_view()

        self.style().unpolish(self.admin_queue_btn)
        self.style().polish(self.admin_queue_btn)
        self.style().unpolish(self.admin_manual_btn)
        self.style().polish(self.admin_manual_btn)
        self.style().unpolish(self.admin_inventory_btn)
        self.style().polish(self.admin_inventory_btn)

    def _refresh_admin_active_view(self):
        if self.admin_view == "queue":
            self._refresh_admin_queue_view()
        elif self.admin_view == "manual-order":
            self._apply_manual_panel_sizing()
            self.refresh_admin_manual_view()
        elif self.admin_view == "inventory":
            self.refresh_inventory_view()

    def _apply_manual_panel_sizing(self):
        width = self.width()
        if width <= 1366:
            right_width = 300
        elif width <= 1600:
            right_width = 330
        else:
            right_width = 350

        self.manual_right_panel.setFixedWidth(right_width)

    def order_row_to_dict(self, row) -> dict:
        return {
            "id": row[0],
            "status": row[1],
            "total_amount": float(row[2]),
            "order_type": row[3],
            "order_time": str(row[4]),
            "customer_name": row[5] if len(row) > 5 else "Guest",
        }

    def _status_color(self, status: str) -> str:
        mapping = {
            "Pending": "#d97706",
            "Preparing": "#0ea5e9",
            "Completed": "#16a34a",
            "Cancelled": "#dc2626",
        }
        return mapping.get(status, "#9ca3af")

    def _clear_layout(self, layout: QVBoxLayout):
        while layout.count():
            child = layout.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()

    def _refresh_admin_queue_view(self):
        self._clear_layout(self.queue_list_layout)

        active_orders = [self.order_row_to_dict(row) for row in self.db.get_active_orders()]
        all_orders = [self.order_row_to_dict(row) for row in self.db.get_all_orders(limit=200)]

        orders = active_orders
        if not orders:
            empty = QLabel("No active orders.")
            empty.setStyleSheet("color: #9ca3af;")
            self.queue_list_layout.addWidget(empty)
        else:
            for order in orders:
                self.queue_list_layout.addWidget(self._build_queue_card(order))

        self.queue_list_layout.addStretch()
        self._refresh_admin_summary_panel(all_orders)

    def _build_queue_card(self, order: dict) -> QWidget:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)

        top = QHBoxLayout()
        title = QLabel(f"Order #{order['id']}")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        status = QLabel(order["status"])
        status.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {self._status_color(order['status'])};")
        top.addWidget(title)
        top.addStretch()
        top.addWidget(status)

        customer = QLabel(f"Customer: {order['customer_name']} | {order['order_type']}")
        customer.setStyleSheet("color: #9ca3af;")
        total = QLabel(f"Total: {format_php(order['total_amount'])}")
        total.setStyleSheet("font-size: 14px;")

        actions = QHBoxLayout()
        preparing_btn = QPushButton("Set Preparing")
        preparing_btn.clicked.connect(lambda: self._update_order_status(order["id"], "Preparing"))
        completed_btn = QPushButton("Set Completed")
        completed_btn.setProperty("variant", "success")
        completed_btn.clicked.connect(lambda: self._update_order_status(order["id"], "Completed"))
        cancel_btn = QPushButton("Cancel Order")
        cancel_btn.setProperty("variant", "danger")
        cancel_btn.clicked.connect(lambda: self._update_order_status(order["id"], "Cancelled"))
        details_btn = QPushButton("View Details")
        details_btn.setProperty("variant", "ghost")
        details_btn.clicked.connect(lambda: self._show_order_details_popup(order["id"]))

        actions.addWidget(preparing_btn)
        actions.addWidget(completed_btn)
        actions.addWidget(cancel_btn)
        actions.addWidget(details_btn)

        layout.addLayout(top)
        layout.addWidget(customer)
        layout.addWidget(total)
        layout.addLayout(actions)
        return card

    def _refresh_admin_summary_panel(self, orders: Optional[List[dict]] = None):
        if orders is None:
            orders = [self.order_row_to_dict(row) for row in self.db.get_all_orders(limit=200)]
        total_orders = len(orders)
        active_orders = len([o for o in orders if o["status"] not in ("Completed", "Cancelled")])
        completed_orders = len([o for o in orders if o["status"] == "Completed"])
        cancelled_orders = len([o for o in orders if o["status"] == "Cancelled"])

        self.summary_total.setText(f"Total Orders: {total_orders}")
        self.summary_active.setText(f"Active: {active_orders}")
        self.summary_completed.setText(f"Completed: {completed_orders}")
        self.summary_cancelled.setText(f"Cancelled: {cancelled_orders}")

    def _update_order_status(self, order_id: int, new_status: str):
        ok = self.db.update_order_status(order_id, new_status)
        if ok:
            self._refresh_admin_queue_view()
        else:
            QMessageBox.critical(self, "Update Failed", f"Could not set order #{order_id} to {new_status}.")

    def _show_order_details_popup(self, order_id: int):
        details = self.db.get_order_details(order_id)
        if not details:
            QMessageBox.critical(self, "Not Found", f"Order #{order_id} was not found.")
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
        QMessageBox.information(self, "Order Details", "\n".join(lines))

    def _show_orders_history_popup(self):
        orders = [self.order_row_to_dict(row) for row in self.db.get_all_orders(limit=100)]
        if not orders:
            QMessageBox.information(self, "Recent Orders", "No orders found.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("All Orders")
        dialog.resize(980, 640)

        root = QVBoxLayout(dialog)
        heading = QLabel("Order History")
        heading.setStyleSheet("font-size: 20px; font-weight: 800;")
        root.addWidget(heading)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        content = QVBoxLayout(container)
        content.setSpacing(8)

        def refresh_rows():
            while content.count():
                child = content.takeAt(0)
                widget = child.widget()
                if widget is not None:
                    widget.deleteLater()

            latest_orders = [self.order_row_to_dict(row) for row in self.db.get_all_orders(limit=100)]
            for order in latest_orders:
                content.addWidget(self._build_order_history_row(order, refresh_rows))
            content.addStretch()

        refresh_rows()
        scroll.setWidget(container)
        root.addWidget(scroll)

        close_btn = QPushButton("Close")
        close_btn.setProperty("variant", "ghost")
        close_btn.clicked.connect(dialog.accept)
        root.addWidget(close_btn, alignment=Qt.AlignRight)

        dialog.exec()

    def _build_order_history_row(self, order: dict, refresh_callback) -> QWidget:
        row = QFrame()
        row.setObjectName("card")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 10, 10, 10)

        info = QLabel(
            f"#{order['id']} | {order['customer_name']} | {order['order_type']} | "
            f"{order['status']} | {format_php(order['total_amount'])}"
        )
        info.setStyleSheet("font-size: 14px; color: #f8fafc;")

        details_btn = QPushButton("View Details")
        details_btn.setProperty("variant", "ghost")
        details_btn.clicked.connect(lambda: self._show_order_details_popup(order["id"]))

        layout.addWidget(info, 1)
        layout.addWidget(details_btn)

        if order["status"] in ("Completed", "Cancelled"):
            reopen_btn = QPushButton("Reopen")
            reopen_btn.setProperty("variant", "success")

            def reopen():
                confirm = QMessageBox.question(
                    self,
                    "Confirm Reopen",
                    f"Reopen order #{order['id']} and set status to Pending?",
                )
                if confirm != QMessageBox.Yes:
                    return
                ok = self.db.update_order_status(order["id"], "Pending")
                if not ok:
                    QMessageBox.critical(self, "Reopen Failed", f"Could not reopen order #{order['id']}.")
                    return
                self._refresh_admin_queue_view()
                refresh_callback()

            reopen_btn.clicked.connect(reopen)
            layout.addWidget(reopen_btn)

        return row

    def _show_customer_queue_popup(self):
        orders = [self.order_row_to_dict(row) for row in self.db.get_active_orders()]
        if not orders:
            QMessageBox.information(self, "Queue", "No active orders in queue.")
            return

        lines = [
            f"#{order['id']} | {order['customer_name']} | {order['status']} | {format_php(order['total_amount'])}"
            for order in orders
        ]
        QMessageBox.information(self, "Queue", "\n".join(lines))

    def _show_customer_track_order_popup(self):
        order_id, ok = QInputDialog.getInt(self, "Track Order", "Enter queue number:", 1, 1, 999999, 1)
        if not ok:
            return

        details = self.db.get_order_details(order_id)
        if not details:
            QMessageBox.critical(self, "Not Found", f"Order #{order_id} does not exist.")
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
            lines.append(f"- {item[5]} x{item[3]} ({format_php(float(item[4]))} each)")
        QMessageBox.information(self, "Order Details", "\n".join(lines))

    def _set_customer_category(self, value: str):
        self.customer_category = value

    def _apply_customer_filter(self):
        self.customer_search = self.search_input.text().strip()
        self.refresh_customer_view()

    def _clear_customer_cart(self):
        self.customer_cart.clear_cart()
        self.customer_cart_image_map.clear()
        self._refresh_cart_panel()

    def _checkout_customer_order(self):
        if self.customer_cart.is_empty():
            QMessageBox.warning(self, "Empty Cart", "Add at least one item before checkout.")
            return

        name, ok = QInputDialog.getText(self, "Checkout", "Enter customer name:")
        if not ok:
            return

        customer_name = (name or "Guest").strip() or "Guest"
        confirm = QMessageBox.question(self, "Confirm Checkout", "Place this order now?")
        if confirm != QMessageBox.Yes:
            return

        queue = self.db.save_new_order(
            self.order_type,
            self.customer_cart.get_items(),
            self.customer_cart.get_total(),
            customer_name,
        )
        if queue:
            QMessageBox.information(self, "Order Placed", f"Queue Number: #{queue}\nCustomer: {customer_name}")
            self.customer_cart.clear_cart()
            self.customer_cart_image_map.clear()
            self.show_landing()
        else:
            QMessageBox.critical(self, "Checkout Failed", "Unable to save order. Check database connection.")

    def _handle_admin_login(self):
        username = self.admin_user_input.text().strip()
        password = self.admin_pass_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Missing Credentials", "Enter both username and password.")
            return

        if self.db.verify_staff_login(username, password):
            self.current_user = username
            self.show_admin_dashboard()
        else:
            QMessageBox.critical(self, "Login Failed", "Invalid admin credentials.")

    def _toggle_admin_manual_order_type(self):
        self.admin_manual_order_type = "Takeaway" if self.admin_manual_order_type == "Dine-in" else "Dine-in"
        self.create_order_mode_label.setText(f"Mode: {self.admin_manual_order_type}")
        next_mode = "Takeaway" if self.admin_manual_order_type == "Dine-in" else "Dine-in"
        self.manual_mode_toggle_btn.setText(f"Switch to {next_mode}")

    def _set_admin_manual_search(self, value: str):
        self.admin_manual_search = value.strip()
        if self.admin_view == "manual-order":
            self._manual_refresh_timer.start(250)

    def _set_admin_manual_category(self, value: str):
        self.admin_manual_category = value
        if self.admin_view == "manual-order":
            self._manual_refresh_timer.start(120)

    def _apply_admin_manual_filter(self):
        self._manual_refresh_timer.stop()
        self.admin_manual_search = self.admin_manual_search_input.text().strip()
        self.refresh_admin_manual_view()

    def _refresh_admin_manual_if_visible(self):
        if self.admin_view == "manual-order":
            self.refresh_admin_manual_view()

    def fetch_admin_manual_items(self) -> List[dict]:
        rows = self.db.search_menu_items(self.admin_manual_search) if self.admin_manual_search else self.db.get_menu()
        items = [self.menu_row_to_dict(row) for row in rows]
        if self.admin_manual_category != "All":
            items = [item for item in items if item["category"] == self.admin_manual_category]
        return items

    def refresh_admin_manual_view(self):
        view_signature = (self.admin_manual_search, self.admin_manual_category, self.manual_center_panel.width())
        if view_signature == self._last_manual_view_signature:
            self._refresh_admin_manual_cart_panel()
            return

        while self.admin_manual_menu_grid.count():
            child = self.admin_manual_menu_grid.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()

        items = self.fetch_admin_manual_items()
        if not items:
            empty = QLabel("No items found for current filter.")
            empty.setStyleSheet("color: #9ca3af;")
            self.admin_manual_menu_grid.addWidget(empty, 0, 0)
            self._refresh_admin_manual_cart_panel()
            return

        center_width = self.manual_center_panel.width()
        if center_width >= 1180:
            col_count = 2
        else:
            col_count = 1
        for idx, item in enumerate(items):
            row = idx // col_count
            col = idx % col_count
            self.admin_manual_menu_grid.addWidget(
                self._build_admin_manual_compact_card(item),
                row,
                col,
            )

        self._refresh_admin_manual_cart_panel()
        self._last_manual_view_signature = view_signature

    def _build_admin_manual_compact_card(self, item: dict) -> QWidget:
        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setMinimumHeight(122)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        thumb_wrap = QFrame()
        thumb_wrap.setStyleSheet("background: #334155; border-radius: 8px;")
        thumb_wrap.setFixedSize(88, 88)
        thumb_layout = QVBoxLayout(thumb_wrap)
        thumb_layout.setContentsMargins(4, 4, 4, 4)
        thumb = QLabel()
        thumb.setAlignment(Qt.AlignCenter)
        pix = self.load_menu_pixmap(item.get("image_path"), QSize(80, 80))
        if pix:
            thumb.setPixmap(pix)
        else:
            thumb.setText("No Image")
            thumb.setStyleSheet("color: #9ca3af; font-weight: 700;")
        thumb_layout.addWidget(thumb)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)

        name = QLabel(item["name"])
        name.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fafc;")
        category = QLabel(item["category"])
        category.setStyleSheet("font-size: 12px; color: #fdba74; font-weight: 700;")
        desc = QLabel(item["description"])
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 12px; color: #cbd5e1;")
        price = QLabel(format_php(item["price"]))
        price.setStyleSheet("font-size: 16px; font-weight: 800; color: #fb923c;")

        info_col.addWidget(name)
        info_col.addWidget(category)
        info_col.addWidget(desc)
        info_col.addStretch()
        info_col.addWidget(price)

        actions_col = QVBoxLayout()
        add_btn = QPushButton("Add to Draft")
        add_btn.clicked.connect(lambda: self._add_to_admin_manual_cart(item))
        actions_col.addStretch()
        actions_col.addWidget(add_btn)

        layout.addWidget(thumb_wrap)
        layout.addLayout(info_col, 1)
        layout.addLayout(actions_col)
        return card

    def _add_to_admin_manual_cart(self, item: dict):
        quantity, ok = QInputDialog.getInt(
            self,
            "Add Quantity",
            f"Quantity for {item['name']}:",
            1,
            1,
            999,
            1,
        )
        if not ok:
            return

        for existing in self.admin_manual_cart.get_items():
            if existing["item_id"] == item["id"]:
                self.admin_manual_cart_image_map[int(item["id"])] = item.get("image_path") or self.placeholder_image_rel
                self.admin_manual_cart.update_quantity(item["id"], int(existing["quantity"]) + int(quantity))
                self._refresh_admin_manual_cart_panel()
                return

        self.admin_manual_cart_image_map[int(item["id"])] = item.get("image_path") or self.placeholder_image_rel
        self.admin_manual_cart.add_item(item["id"], item["name"], item["price"], int(quantity))
        self._refresh_admin_manual_cart_panel()

    def _refresh_admin_manual_cart_panel(self):
        items = self.admin_manual_cart.get_items()
        signature = tuple((int(item["item_id"]), int(item["quantity"]), float(item["price"])) for item in items)
        if signature == self._last_admin_manual_cart_signature:
            return

        self.admin_manual_cart_list.clear()
        for item in items:
            subtotal = float(item["price"]) * int(item["quantity"])
            row = QListWidgetItem()
            row.setData(Qt.UserRole, item["item_id"])

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(6, 4, 6, 4)
            row_layout.setSpacing(8)

            thumb = QLabel()
            thumb.setFixedSize(42, 42)
            thumb.setAlignment(Qt.AlignCenter)
            item_id = int(item["item_id"])
            image_path = self.admin_manual_cart_image_map.get(item_id, self.placeholder_image_rel)
            pix = self.load_menu_pixmap(image_path, QSize(36, 36))
            if pix:
                thumb.setPixmap(pix)
            else:
                thumb.setText("IMG")
                thumb.setStyleSheet("font-size: 10px; color: #9ca3af;")

            details = QLabel(f"{item['name']}\n{format_php(item['price'])} x {item['quantity']} = {format_php(subtotal)}")
            details.setWordWrap(True)
            details.setStyleSheet("color: #f8fafc;")
            details.setMinimumWidth(180)

            row_layout.addWidget(thumb)
            row_layout.addWidget(details, 1)

            row_widget.setMinimumHeight(58)
            row.setSizeHint(QSize(0, 58))
            self.admin_manual_cart_list.addItem(row)
            self.admin_manual_cart_list.setItemWidget(row, row_widget)

        self.admin_manual_cart_total.setText(f"Total: {format_php(self.admin_manual_cart.get_total())}")
        self._last_admin_manual_cart_signature = signature

    def _selected_admin_manual_item_id(self) -> Optional[int]:
        selected = self.admin_manual_cart_list.currentItem()
        if selected is None:
            return None
        value = selected.data(Qt.UserRole)
        return int(value) if value is not None else None

    def _edit_admin_manual_selected_qty(self, *_args):
        item_id = self._selected_admin_manual_item_id()
        if item_id is None:
            QMessageBox.information(self, "Select Item", "Select a draft item first.")
            return

        selected_item = None
        for item in self.admin_manual_cart.get_items():
            if int(item["item_id"]) == item_id:
                selected_item = item
                break

        if selected_item is None:
            QMessageBox.warning(self, "Not Found", "Selected item no longer exists in draft.")
            self._refresh_admin_manual_cart_panel()
            return

        quantity, ok = QInputDialog.getInt(
            self,
            "Edit Quantity",
            f"New quantity for {selected_item['name']}:",
            int(selected_item["quantity"]),
            0,
            999,
            1,
        )
        if not ok:
            return

        self.admin_manual_cart.update_quantity(item_id, int(quantity))
        self._refresh_admin_manual_cart_panel()

    def _remove_admin_manual_selected_item(self):
        item_id = self._selected_admin_manual_item_id()
        if item_id is None:
            QMessageBox.information(self, "Select Item", "Select a draft item first.")
            return

        removed = self.admin_manual_cart.remove_item(item_id)
        if not removed:
            QMessageBox.warning(self, "Not Found", "Selected item no longer exists in draft.")
        self.admin_manual_cart_image_map.pop(int(item_id), None)
        self._refresh_admin_manual_cart_panel()

    def _clear_admin_manual_cart(self):
        if self.admin_manual_cart.is_empty():
            return
        confirm = QMessageBox.question(self, "Clear Draft", "Clear all items from the draft cart?")
        if confirm != QMessageBox.Yes:
            return
        self.admin_manual_cart.clear_cart()
        self.admin_manual_cart_image_map.clear()
        self._refresh_admin_manual_cart_panel()

    def _submit_admin_manual_order(self):
        if self.admin_manual_cart.is_empty():
            QMessageBox.warning(self, "Empty Draft", "Add at least one item before submitting draft.")
            return

        name, ok = QInputDialog.getText(self, "Create Order", "Enter customer name:")
        if not ok:
            return

        customer_name = (name or "Guest").strip() or "Guest"
        confirm = QMessageBox.question(self, "Submit Draft", "Save this draft as a pending order?")
        if confirm != QMessageBox.Yes:
            return

        queue = self.db.save_new_order(
            self.admin_manual_order_type,
            self.admin_manual_cart.get_items(),
            self.admin_manual_cart.get_total(),
            customer_name,
        )
        if queue:
            QMessageBox.information(self, "Draft Submitted", f"Order #{queue} created successfully.")
            self.admin_manual_cart.clear_cart()
            self.admin_manual_cart_image_map.clear()
            self._set_admin_view("queue")
        else:
            QMessageBox.critical(self, "Submit Failed", "Could not save draft order.")

    def _pick_inventory_add_image(self):
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Select Item Image",
            self.images_dir if os.path.isdir(self.images_dir) else self.base_dir,
            "All Files (*.*)",
        )
        if selected:
            self.inventory_add_image_source = selected
            self.inventory_add_image_status.setText(f"Image: {os.path.basename(selected)}")

    def _use_inventory_add_placeholder(self):
        self.inventory_add_image_source = None
        self.inventory_add_image_status.setText("Image: Placeholder (no-image.jpg)")

    def _set_inventory_search(self, value: str):
        self.inventory_search = value.strip()
        if self.admin_view == "inventory":
            self._inventory_refresh_timer.start(250)

    def _set_inventory_category(self, value: str):
        self.inventory_category = value
        if self.admin_view == "inventory":
            self._inventory_refresh_timer.start(120)

    def _refresh_inventory_if_visible(self):
        if self.admin_view == "inventory":
            self.refresh_inventory_view()

    def _invalidate_menu_view_signatures(self):
        self._last_inventory_view_signature = None
        self._last_manual_view_signature = None
        self._last_customer_view_signature = None

    def _clear_inventory_add_form(self):
        self.inventory_name_input.clear()
        self.inventory_desc_input.clear()
        self.inventory_price_input.clear()
        if self.category_options:
            self.inventory_category_input.setCurrentText(self.category_options[0])
        self._use_inventory_add_placeholder()

    def copy_image_to_assets(self, source_path: Optional[str]) -> Optional[str]:
        if not source_path:
            return None

        source_path = source_path.strip()
        if not os.path.isfile(source_path):
            QMessageBox.critical(self, "Image Copy Failed", "Selected image file was not found.")
            return None

        pix = QPixmap(source_path)
        if pix.isNull():
            QMessageBox.critical(self, "Invalid Image", "Selected file is not a readable image.")
            return None

        try:
            os.makedirs(self.images_dir, exist_ok=True)
            stem, ext = os.path.splitext(os.path.basename(source_path))
            if not ext:
                ext = ".jpg"
            safe_stem = "".join(ch if (ch.isalnum() or ch in ("_", "-")) else "_" for ch in stem).strip("_") or "item"
            filename = f"{safe_stem}_{uuid.uuid4().hex[:8]}{ext.lower()}"
            destination = os.path.join(self.images_dir, filename)
            shutil.copy2(source_path, destination)
            return f"src/{filename}"
        except Exception as err:
            QMessageBox.critical(self, "Image Copy Failed", f"Could not copy image file.\n{err}")
            return None

    def fetch_inventory_items(self) -> List[dict]:
        rows = self.db.get_all_menu_items()
        items = [self.menu_row_to_dict(row) for row in rows]

        if self.inventory_search:
            search = self.inventory_search.lower()
            items = [
                item for item in items
                if search in item["name"].lower() or search in (item.get("description") or "").lower()
            ]

        if self.inventory_category != "All":
            items = [item for item in items if item["category"] == self.inventory_category]

        return items

    def _create_inventory_item(self):
        name = self.inventory_name_input.text().strip()
        description = self.inventory_desc_input.text().strip()
        price_text = self.inventory_price_input.text().strip()
        category = self.inventory_category_input.currentText() or (self.category_options[0] if self.category_options else "Main Course")

        if not name:
            QMessageBox.warning(self, "Invalid Input", "Item name is required.")
            return

        try:
            price = float(price_text)
            if price <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Enter a valid positive price.")
            return

        image_path = self.placeholder_image_rel
        if self.inventory_add_image_source:
            copied = self.copy_image_to_assets(self.inventory_add_image_source)
            if copied is None:
                return
            image_path = copied

        item_id = self.db.add_menu_item(name, description, price, category, True, image_path)
        if item_id:
            QMessageBox.information(self, "Added", f"Item #{item_id} added.")
            self._clear_inventory_add_form()
            self._invalidate_menu_view_signatures()
            self.refresh_inventory_view()
        else:
            QMessageBox.critical(self, "Failed", "Could not add item.")

    def _update_inventory_item(self, item_id: int, name: str, description: str, price_text: str, category: str, image_choice: dict):
        name = (name or "").strip()
        if not name:
            QMessageBox.warning(self, "Invalid Input", "Name cannot be empty.")
            return

        try:
            price = float((price_text or "").strip())
            if price <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Enter a valid positive price.")
            return

        update_fields = {
            "name": name,
            "description": (description or "").strip(),
            "price": price,
            "category": category or (self.category_options[0] if self.category_options else "Main Course"),
        }

        mode = image_choice.get("mode", "keep")
        if mode == "new":
            source = image_choice.get("source")
            copied = self.copy_image_to_assets(source)
            if copied is None:
                return
            update_fields["image_path"] = copied
        elif mode == "placeholder":
            update_fields["image_path"] = self.placeholder_image_rel

        ok = self.db.update_menu_item(item_id, **update_fields)
        if ok:
            QMessageBox.information(self, "Updated", f"Item #{item_id} updated.")
            self._invalidate_menu_view_signatures()
            self.refresh_inventory_view()
        else:
            QMessageBox.critical(self, "Failed", f"Could not update item #{item_id}.")

    def _delete_inventory_item(self, item_id: int):
        confirm = QMessageBox.question(self, "Confirm Delete", f"Mark item #{item_id} as unavailable?")
        if confirm != QMessageBox.Yes:
            return

        ok = self.db.delete_menu_item(item_id)
        if ok:
            QMessageBox.information(self, "Deleted", f"Item #{item_id} marked unavailable.")
            self._invalidate_menu_view_signatures()
            self.refresh_inventory_view()
        else:
            QMessageBox.critical(self, "Failed", f"Could not delete item #{item_id}.")

    def _build_inventory_card(self, item: dict) -> QWidget:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)

        top = QHBoxLayout()
        title = QLabel(f"#{item['id']} - {item['name']}")
        title.setStyleSheet("font-size: 17px; font-weight: 700;")
        availability = "Available" if item.get("is_available") else "Unavailable"
        availability_color = "#16a34a" if item.get("is_available") else "#dc2626"
        availability_label = QLabel(availability)
        availability_label.setStyleSheet(f"font-weight: 700; color: {availability_color};")
        top.addWidget(title)
        top.addStretch()
        top.addWidget(availability_label)

        body = QHBoxLayout()

        thumb_wrap = QFrame()
        thumb_wrap.setStyleSheet("background: #334155; border-radius: 10px;")
        thumb_wrap.setFixedSize(120, 120)
        thumb_layout = QVBoxLayout(thumb_wrap)
        thumb_layout.setContentsMargins(5, 5, 5, 5)
        thumb = QLabel()
        thumb.setAlignment(Qt.AlignCenter)
        pix = self.load_menu_pixmap(item.get("image_path"), QSize(110, 110))
        if pix:
            thumb.setPixmap(pix)
        else:
            thumb.setText("No Image")
            thumb.setStyleSheet("color: #9ca3af; font-weight: 700;")
        thumb_layout.addWidget(thumb)

        fields_col = QVBoxLayout()

        name_entry = QLineEdit(item["name"])
        desc_entry = QLineEdit(item.get("description") or "")
        price_entry = QLineEdit(str(item["price"]))
        category_menu = QComboBox()
        category_menu.addItems(self.category_options)
        if self.category_options:
            category_menu.setCurrentText(item["category"] if item["category"] in self.category_options else self.category_options[0])

        display_name = os.path.basename(self.normalize_image_path(item.get("image_path")) or self.placeholder_image_rel)
        image_label = QLabel(f"Image: {display_name}")
        image_label.setStyleSheet("color: #9ca3af;")
        image_state = {"mode": "keep", "source": None}

        image_actions = QHBoxLayout()
        change_image_btn = QPushButton("Change Image")
        change_image_btn.setProperty("variant", "ghost")

        def choose_new_image(state=image_state, status=image_label):
            selected, _ = QFileDialog.getOpenFileName(
                self,
                "Select New Item Image",
                self.images_dir if os.path.isdir(self.images_dir) else self.base_dir,
                "All Files (*.*)",
            )
            if selected:
                state["mode"] = "new"
                state["source"] = selected
                status.setText(f"Selected: {os.path.basename(selected)}")

        change_image_btn.clicked.connect(choose_new_image)

        placeholder_btn = QPushButton("Use Placeholder")
        placeholder_btn.setProperty("variant", "ghost")

        def choose_placeholder(state=image_state, status=image_label):
            state["mode"] = "placeholder"
            state["source"] = None
            status.setText("Will use placeholder")

        placeholder_btn.clicked.connect(choose_placeholder)
        image_actions.addWidget(change_image_btn)
        image_actions.addWidget(placeholder_btn)

        entry_row = QGridLayout()
        entry_row.addWidget(name_entry, 0, 0)
        entry_row.addWidget(desc_entry, 0, 1)
        entry_row.addWidget(price_entry, 0, 2)
        entry_row.addWidget(category_menu, 0, 3)

        action_row = QHBoxLayout()
        update_btn = QPushButton("Update")
        update_btn.setProperty("variant", "success")
        update_btn.clicked.connect(
            lambda: self._update_inventory_item(
                item["id"],
                name_entry.text(),
                desc_entry.text(),
                price_entry.text(),
                category_menu.currentText(),
                image_state,
            )
        )
        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("variant", "danger")
        delete_btn.clicked.connect(lambda: self._delete_inventory_item(item["id"]))
        action_row.addWidget(update_btn)
        action_row.addWidget(delete_btn)
        action_row.addStretch()

        fields_col.addLayout(entry_row)
        fields_col.addWidget(image_label)
        fields_col.addLayout(image_actions)
        fields_col.addLayout(action_row)

        body.addWidget(thumb_wrap)
        body.addLayout(fields_col, 1)

        layout.addLayout(top)
        layout.addLayout(body)
        return card

    def refresh_inventory_view(self):
        view_signature = (self.inventory_search, self.inventory_category)
        if view_signature == self._last_inventory_view_signature:
            return

        while self.inventory_items_layout.count():
            child = self.inventory_items_layout.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()

        items = self.fetch_inventory_items()
        if not items:
            empty = QLabel("No inventory items found.")
            empty.setStyleSheet("color: #9ca3af;")
            self.inventory_items_layout.addWidget(empty)
            self.inventory_items_layout.addStretch()
            return

        for item in items:
            self.inventory_items_layout.addWidget(self._build_inventory_card(item))

        self.inventory_items_layout.addStretch()
        self._last_inventory_view_signature = view_signature

    def fetch_customer_items(self) -> List[dict]:
        rows = self.db.search_menu_items(self.customer_search) if self.customer_search else self.db.get_menu()
        items = [self.menu_row_to_dict(row) for row in rows]
        if self.customer_category != "All":
            items = [item for item in items if item["category"] == self.customer_category]
        return items

    def menu_row_to_dict(self, row) -> dict:
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2] or "No description",
            "price": float(row[3]),
            "category": row[4] or self.category_options[0],
            "is_available": bool(row[5]),
            "image_path": row[6] if len(row) > 6 and row[6] else self.placeholder_image_rel,
        }

    def normalize_image_path(self, image_path: Optional[str]) -> str:
        if not image_path:
            return ""
        return str(image_path).strip().strip('"').strip("'").replace("\\", "/")

    def resolve_image_path(self, image_path: Optional[str]) -> Optional[str]:
        normalized = self.normalize_image_path(image_path)
        if not normalized:
            return None

        if normalized.lower().startswith("file://"):
            normalized = normalized[7:]

        if os.path.isabs(normalized):
            return normalized

        rel_path = normalized.replace("/", os.sep)
        direct_path = os.path.join(self.base_dir, rel_path)
        if os.path.exists(direct_path):
            return direct_path

        src_path = os.path.join(self.images_dir, os.path.basename(rel_path))
        if os.path.exists(src_path):
            return src_path

        return direct_path

    def load_menu_pixmap(self, image_path: Optional[str], size: QSize) -> Optional[QPixmap]:
        requested_path = self.resolve_image_path(image_path)
        candidates = [requested_path, self.placeholder_image_abs]

        cache_key = f"{'|'.join([p for p in candidates if p])}|{size.width()}x{size.height()}"
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]

        for candidate in candidates:
            if not candidate or not os.path.exists(candidate):
                continue
            pixmap = QPixmap(candidate)
            if pixmap.isNull():
                continue
            scaled = pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if len(self.image_cache) >= self._max_image_cache_items:
                self.image_cache.clear()
            self.image_cache[cache_key] = scaled
            return scaled

        return None

    def refresh_customer_view(self):
        view_signature = (self.customer_search, self.customer_category, self.width())
        if view_signature == self._last_customer_view_signature:
            self._refresh_cart_panel()
            return

        # Clear grid widgets
        while self.menu_grid.count():
            child = self.menu_grid.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()

        items = self.fetch_customer_items()
        if not items:
            empty = QLabel("No items found for current filter.")
            empty.setStyleSheet("color: #9ca3af;")
            self.menu_grid.addWidget(empty, 0, 0)
            self._refresh_cart_panel()
            return

        col_count = 3 if self.width() >= 1500 else 2
        for idx, item in enumerate(items):
            row = idx // col_count
            col = idx % col_count
            self.menu_grid.addWidget(self._build_menu_card(item), row, col)

        self._refresh_cart_panel()
        self._last_customer_view_signature = view_signature

    def _build_menu_card(self, item: dict, button_text: str = "Add to Cart", add_callback=None) -> QWidget:
        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setMinimumHeight(350)
        layout = QVBoxLayout(card)

        image_wrap = QFrame()
        image_wrap.setStyleSheet("background: #334155; border-radius: 10px;")
        image_wrap.setFixedHeight(190)
        image_layout = QVBoxLayout(image_wrap)
        image_layout.setContentsMargins(8, 8, 8, 8)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        pix = self.load_menu_pixmap(item.get("image_path"), QSize(180, 180))
        if pix:
            image_label.setPixmap(pix)
        else:
            image_label.setText("Image Unavailable")
            image_label.setStyleSheet("color: #9ca3af; font-weight: 700;")
        image_layout.addWidget(image_label)

        name = QLabel(item["name"])
        name.setStyleSheet("font-size: 18px; font-weight: 700;")
        desc = QLabel(item["description"])
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #9ca3af;")
        category = QLabel(item["category"])
        category.setStyleSheet("color: #93c5fd;")
        price = QLabel(format_php(item["price"]))
        price.setStyleSheet("font-size: 20px; font-weight: 800; color: #22d3ee;")

        add_btn = QPushButton(button_text)
        if add_callback is None:
            add_callback = self._add_to_cart_increment
        add_btn.clicked.connect(lambda: add_callback(item))

        layout.addWidget(image_wrap)
        layout.addWidget(name)
        layout.addWidget(desc)
        layout.addWidget(category)
        layout.addWidget(price)
        layout.addStretch()
        layout.addWidget(add_btn)

        return card

    def _add_to_cart_increment(self, item: dict):
        for existing in self.customer_cart.get_items():
            if existing["item_id"] == item["id"]:
                self.customer_cart_image_map[int(item["id"])] = item.get("image_path") or self.placeholder_image_rel
                self.customer_cart.update_quantity(item["id"], existing["quantity"] + 1)
                self._refresh_cart_panel()
                return

        self.customer_cart_image_map[int(item["id"])] = item.get("image_path") or self.placeholder_image_rel
        self.customer_cart.add_item(item["id"], item["name"], item["price"], 1)
        self._refresh_cart_panel()

    def _adjust_customer_cart_item_qty(self, item_id: int, delta: int):
        for existing in self.customer_cart.get_items():
            if int(existing["item_id"]) == int(item_id):
                new_qty = int(existing["quantity"]) + int(delta)
                self.customer_cart.update_quantity(int(item_id), int(new_qty))
                self._refresh_cart_panel()
                return

    def _remove_customer_cart_item(self, item_id: int):
        self.customer_cart.remove_item(int(item_id))
        self.customer_cart_image_map.pop(int(item_id), None)
        self._refresh_cart_panel()

    def _refresh_cart_panel(self):
        items = self.customer_cart.get_items()
        signature = tuple((int(item["item_id"]), int(item["quantity"]), float(item["price"])) for item in items)
        if signature == self._last_customer_cart_signature:
            return

        self.cart_list.clear()
        for item in items:
            subtotal = float(item["price"]) * int(item["quantity"])
            row = QListWidgetItem()
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(6, 4, 6, 4)
            row_layout.setSpacing(8)

            thumb = QLabel()
            thumb.setFixedSize(42, 42)
            thumb.setAlignment(Qt.AlignCenter)
            item_id = int(item["item_id"])
            image_path = self.customer_cart_image_map.get(item_id, self.placeholder_image_rel)
            pix = self.load_menu_pixmap(image_path, QSize(36, 36))
            if pix:
                thumb.setPixmap(pix)
            else:
                thumb.setText("IMG")
                thumb.setStyleSheet("font-size: 10px; color: #9ca3af;")

            details = QLabel(f"{item['name']}\n{format_php(item['price'])} x {item['quantity']} = {format_php(subtotal)}")
            details.setWordWrap(True)
            details.setStyleSheet("color: #f8fafc;")
            details.setMinimumWidth(180)

            dec_btn = QPushButton("-")
            dec_btn.setFixedWidth(30)
            dec_btn.clicked.connect(lambda _checked=False, iid=int(item["item_id"]): self._adjust_customer_cart_item_qty(iid, -1))

            inc_btn = QPushButton("+")
            inc_btn.setFixedWidth(30)
            inc_btn.clicked.connect(lambda _checked=False, iid=int(item["item_id"]): self._adjust_customer_cart_item_qty(iid, 1))

            remove_btn = QPushButton("Remove")
            remove_btn.setProperty("variant", "danger")
            remove_btn.setFixedWidth(84)
            remove_btn.clicked.connect(lambda _checked=False, iid=int(item["item_id"]): self._remove_customer_cart_item(iid))

            row_layout.addWidget(thumb)
            row_layout.addWidget(details, 1)
            row_layout.addWidget(dec_btn)
            row_layout.addWidget(inc_btn)
            row_layout.addWidget(remove_btn)

            row_widget.setMinimumHeight(58)
            row.setSizeHint(QSize(0, 58))
            self.cart_list.addItem(row)
            self.cart_list.setItemWidget(row, row_widget)

        self.cart_total_label.setText(f"Total: {format_php(self.customer_cart.get_total())}")
        self._last_customer_cart_signature = signature


def main():
    app = QApplication(sys.argv)
    window = KioskQtApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
