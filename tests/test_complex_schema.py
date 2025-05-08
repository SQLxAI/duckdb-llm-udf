"""
Tests for schema extraction with complex database structures
"""

import unittest
import os
import sys
import duckdb

# Update path to include src directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from duckdb_llm_udf.llm_udf import _extract_schema_metadata, _generate_prompt

class TestComplexSchema(unittest.TestCase):
    """Test cases for schema extraction on complex database structures"""
    
    def setUp(self):
        """Set up test environment with a more complex database schema"""
        self.conn = duckdb.connect(':memory:')
        
        # Create complex test database with multiple tables and relationships
        self.conn.execute("""
            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                first_name VARCHAR,
                last_name VARCHAR,
                email VARCHAR UNIQUE,
                phone VARCHAR,
                address VARCHAR,
                city VARCHAR,
                state VARCHAR,
                zip VARCHAR,
                country VARCHAR DEFAULT 'USA',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                loyalty_points INTEGER DEFAULT 0
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE products (
                product_id INTEGER PRIMARY KEY,
                product_name VARCHAR NOT NULL,
                description VARCHAR,
                category VARCHAR,
                price DECIMAL(10, 2) NOT NULL,
                cost DECIMAL(10, 2),
                stock_quantity INTEGER DEFAULT 0,
                reorder_level INTEGER DEFAULT 10,
                discontinued BOOLEAN DEFAULT FALSE
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR DEFAULT 'pending',
                shipping_address VARCHAR,
                shipping_city VARCHAR,
                shipping_zip VARCHAR,
                payment_method VARCHAR,
                total_amount DECIMAL(12, 2),
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE order_items (
                item_id INTEGER PRIMARY KEY,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10, 2) NOT NULL,
                discount DECIMAL(5, 2) DEFAULT 0.00,
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE product_reviews (
                review_id INTEGER PRIMARY KEY,
                product_id INTEGER,
                customer_id INTEGER,
                rating INTEGER CHECK (rating BETWEEN 1 AND 5),
                review_text VARCHAR,
                review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        """)
        
        # Insert sample data
        self.conn.execute("""
            INSERT INTO customers (customer_id, first_name, last_name, email, phone)
            VALUES 
            (1, 'John', 'Smith', 'john@example.com', '555-123-4567'),
            (2, 'Alice', 'Johnson', 'alice@example.com', '555-987-6543')
        """)
        
        self.conn.execute("""
            INSERT INTO products (product_id, product_name, category, price, stock_quantity)
            VALUES 
            (101, 'Premium Headphones', 'Electronics', 149.99, 75),
            (102, 'Wireless Mouse', 'Electronics', 29.99, 150),
            (103, 'Ergonomic Keyboard', 'Electronics', 89.99, 60)
        """)
    
    def test_complex_schema_extraction(self):
        """Test schema extraction with a complex database schema"""
        # Extract schema metadata
        schema = _extract_schema_metadata(self.conn)
        
        # Verify schema contains all tables
        tables = ['customers', 'products', 'orders', 'order_items', 'product_reviews']
        for table in tables:
            self.assertIn(table, schema)
        
        # Check for column presence - note that our extractor only includes column names and types, not constraints
        columns = ['customer_id', 'product_name', 'order_date', 'quantity', 'rating']
        for column in columns:
            self.assertIn(column, schema)
        
        # Check for foreign key relationships
        self.assertIn('Foreign key', schema)
        self.assertIn('references', schema)
        
        # Ensure different data types are captured
        data_types = ['INTEGER', 'VARCHAR', 'DECIMAL', 'TIMESTAMP', 'BOOLEAN']
        for data_type in data_types:
            self.assertIn(data_type.upper(), schema.upper())
    
    def test_complex_prompt_generation(self):
        """Test prompt generation with complex schema"""
        # Extract schema
        schema = _extract_schema_metadata(self.conn)
        
        # Generate prompt with a complex question
        question = "What are the top 3 most reviewed products, and what is their average rating?"
        prompt = _generate_prompt(question, schema)
        
        # Check prompt content
        self.assertIn(question, prompt)
        self.assertIn('products', prompt)
        self.assertIn('product_reviews', prompt)
        self.assertIn('rating', prompt)
        self.assertIn('SQL Query:', prompt)
        
        # Check if the prompt has instructions for JOINs
        self.assertIn('Include appropriate JOINs', prompt)

if __name__ == "__main__":
    unittest.main()
