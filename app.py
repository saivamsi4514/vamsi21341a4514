from flask import Flask, request, jsonify
import sys
import os
import requests
from dataclasses import dataclass

# Define __file__ if not defined (for environments like Jupyter Notebook)
if '__file__' not in globals():
    __file__ = os.path.abspath("app.py")

# Ensure the current directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Data class for the Product
@dataclass
class Product:
    id: str
    name: str
    category: str
    price: float
    rating: float
    company: str
    discount: float

# ECommerceService class to interact with the e-commerce APIs
class ECommerceService:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_products(self, category):
        url = f"{self.base_url}/categories/{category}/products"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch products from {self.base_url}")
        
        products = [Product(**product_data) for product_data in response.json()]
        return products

    def get_product_by_id(self, category, product_id):
        url = f"{self.base_url}/categories/{category}/products/{product_id}"
        response = requests.get(url)
        if response.status_code == 200:
            return Product(**response.json())
        return None

# Pagination function to handle paginated data
def paginate(data, page, page_size):
    start = (page - 1) * page_size
    end = start + page_size
    return data[start:end]

# Flask application setup
app = Flask(__name__)

# Initialize services for each e-commerce API
ecommerce_services = [
    ECommerceService('https://ecommerce1.com/api'),
    ECommerceService('https://ecommerce2.com/api'),
    # Add more services as required
]

# Route to get top products in a category with optional sorting and pagination
@app.route('/categories/<category_name>/products', methods=['GET'])
def get_top_products(category_name):
    n = int(request.args.get('n', 10))
    if n > 10:
        return jsonify({"error": "'n' should not exceed 10"}), 400

    page = int(request.args.get('page', 1))
    sort_by = request.args.get('sort_by')
    sort_order = request.args.get('sort_order', 'asc')

    all_products = []
    for service in ecommerce_services:
        products = service.get_products(category_name)
        all_products.extend(products)

    # Sort products if needed
    if sort_by:
        reverse = (sort_order == 'desc')
        all_products.sort(key=lambda x: getattr(x, sort_by), reverse=reverse)

    # Pagination
    paginated_products = paginate(all_products, page, n)
    
    # Generate unique IDs for each product
    for i, product in enumerate(paginated_products):
        product.id = f"{category_name}_{page}_{i + 1}"

    response = {
        "products": [product.__dict__ for product in paginated_products],
        "total": len(all_products)
    }

    return jsonify(response)

# Route to get product details by category and product ID
@app.route('/categories/<category_name>/products/<product_id>', methods=['GET'])
def get_product_details(category_name, product_id):
    for service in ecommerce_services:
        product = service.get_product_by_id(category_name, product_id)
        if product:
            return jsonify(product.__dict__)
    return jsonify({"error": "Product not found"}), 404

# Main entry point for running the Flask app
if __name__ == '__main__':
    app.run(debug=True)
