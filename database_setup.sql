CREATE DATABASE IF NOT EXISTS kiosk_db;
USE kiosk_db;

CREATE TABLE IF NOT EXISTS staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(64) NOT NULL,
    full_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS menu_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(50),
    is_available BOOLEAN DEFAULT TRUE,
    image_path VARCHAR(255) DEFAULT 'src/no-image.jpg'
);

INSERT INTO staff (username, password_hash, full_name) VALUES
('admin', SHA2('admin123', 256), 'System Administrator');


INSERT INTO menu_items (name, category, price, description) VALUES 
('Sizzling Sisig', 'Main Course', 120.00, 'Classic Filipino sizzling pork sisig'),
('Sizzling Porkchop', 'Main Course', 130.00, 'Tender porkchop on a hot plate'),
('Sizzling Chicken', 'Main Course', 125.00, 'Fried chicken served sizzling with gravy'),
('Sizzling Tofu', 'Main Course', 100.00, 'Healthy and savory sizzling tofu cubes'),
('Sizzling Bangus', 'Main Course', 135.00, 'Sizzling milkfish with garlic'),
('Tapsilog', 'Main Course', 95.00, 'Tapa, Sinangag, at Itlog'),
('Longsilog', 'Main Course', 85.00, 'Longganisa, Sinangag, at Itlog'),
('Tocilog', 'Main Course', 90.00, 'Tocino, Sinangag, at Itlog'),
('Bangsilog', 'Main Course', 100.00, 'Bangus, Sinangag, at Itlog'),
('Hotsilog', 'Main Course', 80.00, 'Hotdog, Sinangag, at Itlog'),
('Lumpiang Shanghai', 'Appetizer', 70.00, 'Crunchy spring rolls with sweet chili dip'),
('Leche Flan', 'Dessert', 55.00, 'Classic caramel custard dessert'),
('French Fries', 'Side', 65.00, 'Crispy golden fries'),
('Iced Tea', 'Beverage', 25.00, 'Refreshing chilled iced tea'),
('Softdrinks (Mismo)', 'Beverage', 20.00, 'Assorted soda flavors (300ml)'),
('Calamansi Juice', 'Beverage', 25.00, 'Freshly squeezed calamansi'),
('Bottled Water', 'Beverage', 20.00, 'Purified drinking water (500ml)');