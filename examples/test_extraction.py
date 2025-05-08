"""
Test script to verify schema extraction functionality without making LLM API calls
"""

import os
import sys
import time
import duckdb
import logging

# Configure logging to match the module's logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_extraction')

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the internal functions directly for testing
from duckdb_llm_udf.llm_udf import _extract_schema_metadata, _generate_prompt

def create_sample_database():
    """Create a sample database for testing"""
    logger.info("Creating sample database")
    start_time = time.time()
    conn = duckdb.connect(':memory:')
    
    # Create sample tables
    conn.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            name VARCHAR,
            email VARCHAR,
            signup_date DATE
        )
    """)
    
    conn.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            order_date DATE,
            total_amount DECIMAL(10, 2),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    
    # Insert sample data
    conn.execute("""
        INSERT INTO customers VALUES
        (1, 'John Smith', 'john@example.com', '2023-01-15'),
        (2, 'Alice Brown', 'alice@example.com', '2023-02-20'),
        (3, 'Bob Johnson', 'bob@example.com', '2023-03-10')
    """)
    
    conn.execute("""
        INSERT INTO orders VALUES
        (101, 1, '2023-03-10', 150.00),
        (102, 2, '2023-03-15', 230.50),
        (103, 1, '2023-04-05', 75.25),
        (104, 3, '2023-03-20', 310.75)
    """)
    
    end_time = time.time()
    logger.info(f"Sample database created in {end_time - start_time:.2f} seconds")
    return conn

def main():
    logger.info("Starting test extraction script")
    total_start_time = time.time()
    
    # Create a sample database
    logger.info("Step 1: Creating sample database")
    conn = create_sample_database()
    
    # Extract schema metadata
    logger.info("Step 2: Extracting schema metadata")
    schema_start_time = time.time()
    schema = _extract_schema_metadata(conn)
    schema_end_time = time.time()
    logger.info(f"Schema extraction completed in {schema_end_time - schema_start_time:.2f} seconds")
    print("=== EXTRACTED SCHEMA METADATA ===")
    print(schema)
    print("\n")
    
    # Generate a sample prompt with natural language question
    logger.info("Step 3: Generating prompt")
    question = "Show me the top 2 customers by total order amount"
    prompt_start_time = time.time()
    prompt = _generate_prompt(question, schema)
    prompt_end_time = time.time()
    logger.info(f"Prompt generation completed in {prompt_end_time - prompt_start_time:.2f} seconds")
    print("=== GENERATED PROMPT ===")
    print(prompt)
    
    # Test schema extraction with SQL
    logger.info("Step 4: Verifying database content with SQL queries")
    sql_start_time = time.time()
    print("\n=== VERIFYING DATABASE CONTENT ===")
    result = conn.execute("SELECT * FROM customers").fetchall()
    print("Customers table:")
    for row in result:
        print(row)
    
    result = conn.execute("SELECT * FROM orders").fetchall()
    print("\nOrders table:")
    for row in result:
        print(row)
    sql_end_time = time.time()
    logger.info(f"SQL verification completed in {sql_end_time - sql_start_time:.2f} seconds")
    
    # This would be the expected SQL for our question
    logger.info("Step 5: Showing expected SQL")
    print("\n=== EXPECTED SQL FOR THE QUESTION ===")
    expected_sql = """
    SELECT c.customer_id, c.name, SUM(o.total_amount) as total_spent
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, c.name
    ORDER BY total_spent DESC
    LIMIT 2
    """
    print(expected_sql)
    
    # Execute the expected SQL to verify it works
    logger.info("Step 6: Executing the expected SQL")
    exec_start_time = time.time()
    print("\n=== RESULT OF EXECUTING THE EXPECTED SQL ===")
    result = conn.execute(expected_sql).fetchall()
    for row in result:
        print(row)
    exec_end_time = time.time()
    logger.info(f"SQL execution completed in {exec_end_time - exec_start_time:.2f} seconds")
    
    # Show total runtime
    total_end_time = time.time()
    logger.info(f"Total script runtime: {total_end_time - total_start_time:.2f} seconds")

if __name__ == "__main__":
    main()
