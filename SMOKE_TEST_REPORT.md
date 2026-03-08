# Smoke Test Report

Date: 2026-03-08
Project: Fast Food Kiosk System
Scope: Clean database smoke test for CLI backend flows

## Environment
- OS: Windows
- Python: virtual environment in `.venv`
- Database: MySQL (localhost, user `root`, empty password)
- App under test: `cli_backend.py` + `kiosk_backend.py`

## Test Objective
Validate that a fresh database setup works end-to-end for both customer and admin flows, including queue/customer-name behavior and order management actions.

## Precondition
- Codebase includes latest fixes:
  - cart total Decimal handling fix
  - `customer_name` support in orders
  - `View Queue` naming
  - `View Order Details` tuple-index fix
  - status-update no-op/existence handling

## Database Reset and Seed

### Step 1: Drop existing database
Command:
```powershell
python -c "import mysql.connector; conn=mysql.connector.connect(host='localhost',user='root',password=''); cur=conn.cursor(); cur.execute('DROP DATABASE IF EXISTS kiosk_db'); conn.commit(); cur.close(); conn.close(); print('Dropped kiosk_db')"
```
Expected:
- Database is removed.
Observed:
- `Dropped kiosk_db`
Result: PASS

### Step 2: Import setup SQL
Command:
```powershell
python -c "import mysql.connector, pathlib; sql=pathlib.Path('database_setup.sql').read_text(encoding='utf-8'); conn=mysql.connector.connect(host='localhost',user='root',password=''); cur=conn.cursor(); [None for _ in cur.execute(sql, multi=True)]; conn.commit(); cur.close(); conn.close(); print('Imported database_setup.sql')"
```
Expected:
- Schema/data recreated from `database_setup.sql`.
Observed:
- `Imported database_setup.sql`
Result: PASS

## Customer Flow Smoke Test

### Scripted input used
```text
1
1
2
1
1
3
6
Smoke Tester
1
yes
8
7
1
9
3
```

### Covered functions
- Main Menu -> Customer Mode
- `View Menu`
- `Add Item to Cart`
- `View Cart`
- `Checkout` with customer name
- `View Queue`
- `View Order Status`
- Back/Exit

### Expected behavior
- Menu displays available items.
- Item can be added to cart and cart totals are shown.
- Checkout saves order and returns queue number.
- Queue displays order with customer name.
- Order status details show customer name and items.

### Observed behavior
- Order created successfully with queue number `#1`.
- Customer name shown in queue: `Smoke Tester`.
- Order status view displayed details without crash.
Result: PASS

## Admin Flow Smoke Test

### Scripted input used
```text
2
admin
admin123
6
7
1
8
1
2
5
9
1
yes
10
3
```

### Covered functions
- Main Menu -> Admin Mode
- Admin login
- `View Active Orders`
- `View Order Details`
- `Update Order Status`
- `View All Orders`
- `Cancel Order`
- Logout/Exit

### Expected behavior
- Admin can view active queue and details of order.
- Status update works.
- Cancel order works.
- No crash in order details view.

### Observed behavior
- Active queue shown with customer name.
- Order details opened successfully (no `IndexError`).
- Status changed `Pending -> Preparing`.
- Cancel changed status to `Cancelled`.
Result: PASS

## Summary
- Clean DB setup: PASS
- Customer flow smoke test: PASS
- Admin flow smoke test: PASS
- Regression checks for previously reported crashes: PASS

Overall status: PASS

## Reusable QA Checklist (Quick)
1. Drop and recreate DB from `database_setup.sql`.
2. Run customer path: menu -> add -> cart -> checkout (with name) -> queue -> order status.
3. Run admin path: login -> active orders -> order details -> update status -> all orders -> cancel.
4. Confirm no tracebacks in terminal output.
