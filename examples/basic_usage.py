"""
Example of using the DuckDB LLM UDF extension to query a database using natural language.
"""

import os
from dotenv import load_dotenv
import duckdb
from duckdb_llm_udf import register_llm_functions

# Sample database creation for demonstration
def create_sample_database(conn):
    """Create a sample database with customer and order data"""
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
        (3, 'Bob Johnson', 'bob@example.com', '2023-03-10'),
        (4, 'Emma Davis', 'emma@example.com', '2023-01-05'),
        (5, 'Michael Wilson', 'michael@example.com', '2023-02-28')
    """)
    
    conn.execute("""
        INSERT INTO orders VALUES
        (101, 1, '2023-03-10', 150.00),
        (102, 2, '2023-03-15', 230.50),
        (103, 1, '2023-04-05', 75.25),
        (104, 3, '2023-03-20', 310.75),
        (105, 2, '2023-04-10', 160.00),
        (106, 4, '2023-03-25', 90.50),
        (107, 5, '2023-03-30', 120.25),
        (108, 3, '2023-04-15', 200.00),
        (109, 1, '2023-04-20', 180.75),
        (110, 5, '2023-04-25', 250.50)
    """)

def main():
    # Create an in-memory database
    conn = duckdb.connect(':memory:')
    
    # Create sample data
    create_sample_database(conn)
    
    # Register the LLM functions
    register_llm_functions(conn)
    
    # Load .env file from current working directory
    load_dotenv()
    
    # Set API key in DuckDB (required for LLM queries)
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        print("Warning: No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")
        print("Alternatively, you can set it with: conn.execute(\"SELECT llm_configure('api_key', 'your-api-key')\")")
    else:
        conn.execute(f"SELECT llm_configure('api_key', '{api_key}')")
    
    # Configure the LLM (optional)
    conn.execute("SELECT llm_configure('model', 'gpt-3.5-turbo')")
    
    # Example natural language queries
    queries = [
        "Show me the top 3 customers by total order amount",
        "What's the average order amount per customer?",
        "Find all orders placed in March 2023"
    ]
    
    for query in queries:
        print(f"\n\nQuery: {query}")
        try:
            # First get the SQL without executing it
            sql = ask_llm(query, conn, execute=False)
            print(f"Generated SQL:\n{sql}")
            
            # Now ask for confirmation and execute if approved
            if input("\nExecute this SQL? (y/n): ").lower() == 'y':
                result = conn.execute(sql).fetchall()
                print("\nResults:")
                for row in result:
                    print(row)
        except Exception as e:
            print(f"Error: {e}")

# Utility function extracted for demonstration
def ask_llm(question, conn, execute=True):
    """Wrapper for the ask_llm function for direct Python use"""
    from duckdb_llm_udf.llm_udf import ask_llm as _ask_llm
    return _ask_llm(question, conn, execute=execute)

if __name__ == "__main__":
    main()
