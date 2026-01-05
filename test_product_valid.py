import requests
import json

# Test creating a product without subcategory_id (should work)
url = "http://127.0.0.1:8000/products/"
payload = {
    "name": "Test Product",
    "description": "A test product",
    "price": 100.0,
    "sku": "TEST123",
    "hsn_code": "1234",
    "category_id": 1,
    "unit": "pcs",
    "vendor_price": 80.0,
    "discount_percentage": 10.0,
    "stock_count": 50,
    "visibility": True,
    "meta_title": "Test Product",
    "meta_description": "Test description",
    "seo_keywords": {"keyword1": "test", "keyword2": "product"},
    "warranty": "1 year"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
