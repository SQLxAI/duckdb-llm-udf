"""
Test script to verify LLM API calls with the DuckDB LLM UDF extension.
This script requires a valid API key for either OpenAI or Anthropic.
"""

import os
import sys
import time
import duckdb
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_llm_call')

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the DuckDB LLM UDF
from duckdb_llm_udf import register_llm_functions
from duckdb_llm_udf.llm_udf import (
    _extract_schema_metadata, 
    _generate_prompt,
    _generate_sql_with_llm,
    ask_llm
)

def create_sample_database():
    """Create a sample database for testing"""
    logger.info("Creating sample database")
    start_time = time.time()
    conn = duckdb.connect(':memory:')
    
    # Create sample tables with more realistic data
    conn.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            name VARCHAR,
            category VARCHAR,
            price DECIMAL(10, 2),
            stock INTEGER
        )
    """)
    
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
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    
    conn.execute("""
        CREATE TABLE order_items (
            item_id INTEGER PRIMARY KEY,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price DECIMAL(10, 2),
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)
    
    # Insert sample data
    conn.execute("""
        INSERT INTO products VALUES
        (1, 'Laptop', 'Electronics', 1299.99, 45),
        (2, 'Smartphone', 'Electronics', 799.99, 120),
        (3, 'Headphones', 'Electronics', 199.99, 78),
        (4, 'Coffee Maker', 'Appliances', 89.99, 32),
        (5, 'Blender', 'Appliances', 69.95, 16),
        (6, 'Gaming Monitor', 'Electronics', 349.99, 22),
        (7, 'Desk Chair', 'Furniture', 249.95, 12),
        (8, 'Desk Lamp', 'Furniture', 49.99, 43)
    """)
    
    conn.execute("""
        INSERT INTO customers VALUES
        (1, 'John Smith', 'john@example.com', '2023-01-15'),
        (2, 'Alice Brown', 'alice@example.com', '2023-02-20'),
        (3, 'Bob Johnson', 'bob@example.com', '2023-03-10'),
        (4, 'Emma Davis', 'emma@example.com', '2023-01-05'),
        (5, 'Michael Wilson', 'michael@example.com', '2023-02-28')
    """)
    
    conn.execute("""
        INSERT INTO orders VALUES
        (101, 1, '2023-03-10'),
        (102, 2, '2023-03-15'),
        (103, 1, '2023-04-05'),
        (104, 3, '2023-03-20'),
        (105, 2, '2023-04-10'),
        (106, 4, '2023-03-25'),
        (107, 5, '2023-03-30'),
        (108, 3, '2023-04-15'),
        (109, 1, '2023-04-20'),
        (110, 5, '2023-04-25')
    """)
    
    conn.execute("""
        INSERT INTO order_items VALUES
        (1001, 101, 1, 1, 1299.99),
        (1002, 102, 2, 1, 799.99),
        (1003, 102, 3, 1, 199.99),
        (1004, 103, 4, 1, 89.99),
        (1005, 104, 2, 1, 799.99),
        (1006, 104, 6, 1, 349.99),
        (1007, 105, 7, 1, 249.95),
        (1008, 105, 8, 2, 49.99),
        (1009, 106, 5, 1, 69.95),
        (1010, 107, 3, 1, 199.99),
        (1011, 108, 1, 1, 1299.99),
        (1012, 109, 4, 1, 89.99),
        (1013, 109, 5, 1, 69.95),
        (1014, 110, 6, 1, 349.99)
    """)
    
    end_time = time.time()
    logger.info(f"Sample database created in {end_time - start_time:.2f} seconds")
    return conn

def test_openai_call(schema, question):
    """Test an OpenAI API call"""
    # Check if API key is set
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.error("OpenAI API key not found in environment variables")
        print("Error: OpenAI API key not found. Make sure to set OPENAI_API_KEY in your .env file.")
        return False
    
    # Generate a prompt
    prompt = _generate_prompt(question, schema)
    
    # Make an API call to OpenAI
    logger.info("Making API call to OpenAI")
    start_time = time.time()
    model = os.environ.get('LLM_MODEL', 'gpt-3.5-turbo')
    result = _generate_sql_with_llm(
        question=question, 
        schema=schema,
        provider='openai',
        model=model,
        api_key=api_key
    )
    end_time = time.time()
    
    # Check result
    if result.startswith("ERROR"):
        logger.error(f"OpenAI API call failed: {result}")
        print(f"Error: {result}")
        return False
    
    logger.info(f"OpenAI API call completed in {end_time - start_time:.2f} seconds")
    print(f"\nOpenAI ({model}) generated SQL:")
    print(result)
    return True

def test_anthropic_call(schema, question):
    """Test an Anthropic API call"""
    # Check if API key is set
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        logger.error("Anthropic API key not found in environment variables")
        print("Error: Anthropic API key not found. Make sure to set ANTHROPIC_API_KEY in your .env file.")
        return False
    
    # Generate a prompt
    prompt = _generate_prompt(question, schema)
    
    # Make an API call to Anthropic
    logger.info("Making API call to Anthropic")
    start_time = time.time()
    model = os.environ.get('LLM_MODEL', 'claude-3-sonnet-20240229')
    result = _generate_sql_with_llm(
        question=question, 
        schema=schema,
        provider='anthropic',
        model=model,
        api_key=api_key
    )
    end_time = time.time()
    
    # Check result
    if result.startswith("ERROR"):
        logger.error(f"Anthropic API call failed: {result}")
        print(f"Error: {result}")
        return False
    
    logger.info(f"Anthropic API call completed in {end_time - start_time:.2f} seconds")
    print(f"\nAnthropic ({model}) generated SQL:")
    print(result)
    return True

def main():
    """Test the LLM call functionality with real API calls"""
    logger.info("Starting LLM call test")
    
    # Get provider preference
    provider = os.environ.get('LLM_PROVIDER', 'openai').lower()
    logger.info(f"Using LLM provider: {provider}")
    
    # Create the sample database
    conn = create_sample_database()
    
    # Extract schema metadata
    schema = _extract_schema_metadata(conn)
    print("Database schema extracted successfully")
    
    # Define a natural language query
    question = "Which category generated the most revenue?"
    print(f"\nNatural language question: '{question}'")
    
    # Test the appropriate LLM provider
    if provider == 'openai':
        success = test_openai_call(schema, question)
    elif provider == 'anthropic':
        success = test_anthropic_call(schema, question)
    else:
        logger.error(f"Unsupported provider: {provider}")
        print(f"Error: Unsupported provider '{provider}'. Supported providers are 'openai' and 'anthropic'.")
        return
    
    if success:
        # Now test the full ask_llm function
        print("\nTesting full ask_llm function (execute=False mode)...")
        
        # Register the LLM functions
        register_llm_functions(conn)
        
        # Ask a different question to ensure we're not getting cached results
        new_question = "What are the top 3 most expensive products?"
        
        # Use the ask_llm function directly, but don't execute the SQL
        try:
            sql = ask_llm(new_question, conn, execute=False)
            print(f"\nask_llm function result for '{new_question}':")
            print(sql)
            print("\nLLM API call test completed successfully!")
        except Exception as e:
            logger.error(f"Error using ask_llm function: {str(e)}")
            print(f"Error using ask_llm function: {str(e)}")

if __name__ == "__main__":
    main()
