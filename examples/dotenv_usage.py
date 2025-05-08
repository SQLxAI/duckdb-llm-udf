"""
Example showing how to use environment variables with .env files
"""

import os
import duckdb
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from duckdb_llm_udf import register_llm_functions

def main():
    """Demonstrate using the extension with environment variables from .env"""
    
    # The extension automatically loads variables from .env when imported
    # Create a .env file in your project with:
    #
    # OPENAI_API_KEY=sk-your-openai-key-here
    # LLM_PROVIDER=openai
    # LLM_MODEL=gpt-3.5-turbo
    
    # Connect to an in-memory database
    conn = duckdb.connect(':memory:')
    
    # Create a simple example table
    conn.execute("""
        CREATE TABLE products (
            id INTEGER,
            name VARCHAR,
            category VARCHAR,
            price DECIMAL(10, 2)
        )
    """)
    
    conn.execute("""
        INSERT INTO products VALUES
        (1, 'Laptop', 'Electronics', 1299.99),
        (2, 'Smartphone', 'Electronics', 899.50),
        (3, 'Coffee Maker', 'Appliances', 89.99),
        (4, 'Headphones', 'Electronics', 199.99),
        (5, 'Blender', 'Appliances', 69.95)
    """)
    
    # Register the LLM functions
    register_llm_functions(conn)
    
    # Print the current environment variable configuration
    print("Current configuration:")
    print(f"  LLM Provider: {os.environ.get('LLM_PROVIDER', '(not set)')}")
    print(f"  LLM Model: {os.environ.get('LLM_MODEL', '(not set)')}")
    print(f"  OpenAI API Key: {'✓ Set' if os.environ.get('OPENAI_API_KEY') else '✗ Not set'}")
    print(f"  Anthropic API Key: {'✓ Set' if os.environ.get('ANTHROPIC_API_KEY') else '✗ Not set'}")
    
    # Check if we have an API key configured
    if not (os.environ.get('OPENAI_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')):
        print("\nNo API key found in environment variables!")
        print("Please create a .env file with your API key, or set it using:")
        print("  conn.execute(\"SELECT llm_configure('api_key', 'your-api-key')\")")
        return
    
    # Example natural language query
    print("\nQuerying the database using natural language...")
    question = "What electronic products do we have?"
    
    print(f"\nQuestion: {question}")
    
    # First get the SQL without executing it
    from duckdb_llm_udf.llm_udf import ask_llm
    try:
        sql = ask_llm(question, conn, execute=False)
        print(f"\nGenerated SQL:\n{sql}")
        
        # Execute the SQL directly
        print("\nExecuting SQL...")
        result = conn.execute(sql).fetchall()
        print("\nResults:")
        for row in result:
            print(row)
    except Exception as e:
        print(f"Error: {e}")
        
if __name__ == "__main__":
    main()
