"""
Unit tests for DuckDB LLM UDF extension
"""

import unittest
import os
import duckdb
from unittest.mock import patch, MagicMock

# Import the module directly for testing
import sys
import os.path
# Update path to include src directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from duckdb_llm_udf import register_llm_functions
from duckdb_llm_udf.llm_udf import (
    _extract_schema_metadata,
    _generate_prompt,
    llm_configure,
    _get_config
)

class TestLLMUDF(unittest.TestCase):
    """Test cases for LLM UDF functions"""
    
    def setUp(self):
        """Set up test environment"""
        self.conn = duckdb.connect(':memory:')
        
        # Create test tables
        self.conn.execute("""
            CREATE TABLE test_customers (
                id INTEGER PRIMARY KEY,
                name VARCHAR,
                email VARCHAR
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE test_orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                amount DECIMAL,
                FOREIGN KEY (customer_id) REFERENCES test_customers(id)
            )
        """)
        
        # Insert test data
        self.conn.execute("""
            INSERT INTO test_customers VALUES 
            (1, 'Test User', 'test@example.com'),
            (2, 'Another User', 'another@example.com')
        """)
        
        self.conn.execute("""
            INSERT INTO test_orders VALUES
            (101, 1, 99.99),
            (102, 2, 149.99),
            (103, 1, 25.50)
        """)
        
        # Register LLM functions
        register_llm_functions(self.conn)
    
    def test_extract_schema_metadata(self):
        """Test schema metadata extraction"""
        schema = _extract_schema_metadata(self.conn)
        
        # Verify schema contains our test tables
        self.assertIn("test_customers", schema)
        self.assertIn("test_orders", schema)
        self.assertIn("id INTEGER", schema)  # Check for column name and type
        self.assertIn("Primary key", schema)  # Check for primary key indication
        self.assertIn("Foreign key", schema)  # Check for foreign key indication
    
    def test_generate_prompt(self):
        """Test prompt generation"""
        schema = "Table: test\nColumns: id, name"
        question = "How many users are there?"
        
        prompt = _generate_prompt(question, schema)
        
        # Verify prompt contains the schema and question
        self.assertIn(schema, prompt)
        self.assertIn(question, prompt)
        self.assertIn("SQL Query:", prompt)
    
    def test_llm_configure(self):
        """Test configuration function"""
        # Test setting a valid configuration
        result = llm_configure('model', 'gpt-4')
        self.assertIn("Configuration updated", result)
        
        # Verify configuration was updated
        config = _get_config()
        self.assertEqual(config['model'], 'gpt-4')
        
        # Test setting an invalid configuration
        result = llm_configure('invalid_key', 'value')
        self.assertIn("ERROR", result)
    
    @patch('duckdb_llm_udf.llm_udf._call_openai_api')
    def test_ask_llm_without_execution(self, mock_openai):
        """Test ask_llm function without executing the SQL"""
        # Configure the mock to return a SQL query
        mock_openai.return_value = "SELECT * FROM test_customers"
        
        # Configure API key
        llm_configure('api_key', 'test_key')
        
        # Test the ask_llm function directly (not via DuckDB)
        from duckdb_llm_udf.llm_udf import ask_llm
        sql = ask_llm("Show me all customers", self.conn, execute=False)
        
        # Verify the SQL is returned as-is
        self.assertEqual(sql, "SELECT * FROM test_customers")
        
        # Verify OpenAI API was called with appropriate arguments
        mock_openai.assert_called_once()
        args = mock_openai.call_args[0]
        self.assertIn("Show me all customers", args[0])  # Check question in prompt

if __name__ == '__main__':
    unittest.main()
