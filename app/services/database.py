import json
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- Data Loading ---
# Construct the path to the data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def load_json_data(filename):
	"""Loads data from a JSON file."""
	with open(os.path.join(DATA_DIR, filename), 'r') as f:
		return json.load(f)

# Load the dummy data when the module is imported
customers_data = load_json_data('customers.json')
products_data = load_json_data('products.json')
orders_data = load_json_data('orders.json')

# --- Service Functions ---

def get_warranty_status_from_order(customer_id: str, order_id: str, product_name: str) -> dict:
	"""Finds warranty status from the loaded JSON data."""
	print(f"---SERVICE: Querying JSON for Cust: {customer_id}, Order: {order_id}, Product: {product_name}---")

	# Find the order using a list comprehension
	order = next((o for o in orders_data if o['order_id'] == order_id and o['customer_id'] == customer_id), None)
	if not order:
		return {"status": "Error", "message": "Order or Customer not found."}

	# Find the product within the order's items
	found_item = next((item for item in order["items"] if product_name.lower() in item["product_name"].lower()), None)
	if not found_item:
		return {"status": "Error", "message": f"Product '{product_name}' not found in order {order_id}."}

	# Find the product's standard warranty period
	product_details = next((p for p in products_data if p['product_id'] == found_item['product_id']), None)
	if not product_details:
		return {"status": "Error", "message": "Product details not found."}

	# Calculate expiry
	warranty_months = product_details["warranty_period_months"]
	# Parse the date string from JSON into a datetime object
	order_date = datetime.fromisoformat(order["order_date"])
	expiry_date = order_date + relativedelta(months=+warranty_months)
    
	status = "Active" if datetime.now() < expiry_date else "Expired"
        
	return {
		"status": status,
		"expiry_date": expiry_date.strftime("%Y-%m-%d"),
		"order_date": order_date.strftime("%Y-%m-%d"),
	}

def fetch_warranty_details_by_sn(serial_number: str) -> dict:
	"""Fetches warranty based on a unique serial number."""
	print(f"---SERVICE: Querying JSON for SN: {serial_number}---")
	return {"status": "Not Implemented", "message": "Serial number lookup is not yet implemented."}
