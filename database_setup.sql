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

UPDATE menu_items
SET image_path = 'src/sizzlingsisig_e05170d3.jpg'
WHERE LOWER(TRIM(name)) = 'sizzling sisig';

UPDATE menu_items
SET image_path = 'src/sizzlingporkchop_7d517b99.jpg'
WHERE LOWER(TRIM(name)) = 'sizzling porkchop';

UPDATE menu_items
SET image_path = 'src/sizzlingchicken_5ad1cd72.jpg'
WHERE LOWER(TRIM(name)) = 'sizzling chicken';

UPDATE menu_items
SET image_path = 'src/sizzlingtofu_058c8728.jpg'
WHERE LOWER(TRIM(name)) = 'sizzling tofu';

UPDATE menu_items
SET image_path = 'src/sizzlingbangus_2e91b431.jpg'
WHERE LOWER(TRIM(name)) = 'sizzling bangus';

UPDATE menu_items
SET image_path = 'src/tapsilog_5e0e97f7.jpg'
WHERE LOWER(TRIM(name)) = 'tapsilog';

UPDATE menu_items
SET image_path = 'src/longsilog_507594a4.jpg'
WHERE LOWER(TRIM(name)) = 'longsilog';

UPDATE menu_items
SET image_path = 'src/tocilog_0263bf82.jpg'
WHERE LOWER(TRIM(name)) = 'tocilog';

UPDATE menu_items
SET image_path = 'src/bangsilog_1b48ac10.jpg'
WHERE LOWER(TRIM(name)) = 'bangsilog';

UPDATE menu_items
SET image_path = 'src/hotsilog_5d2c2c26.jpg'
WHERE LOWER(TRIM(name)) = 'hotsilog';

UPDATE menu_items
SET image_path = 'src/Iced-Tea-Recipe-OurZestyLife-3_fbd711c7.jpg'
WHERE LOWER(TRIM(name)) = 'iced tea';

UPDATE menu_items
SET image_path = 'src/mismo_b7d2fcaa.jpg'
WHERE LOWER(TRIM(name)) = 'softdrinks (mismo)';

UPDATE menu_items
SET image_path = 'src/calamansi-juice_2c58fc70.jpg'
WHERE LOWER(TRIM(name)) = 'calamansi juice';

UPDATE menu_items
SET image_path = 'src/water_24c165ad.jpg'
WHERE LOWER(TRIM(name)) = 'bottled water';