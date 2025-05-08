"""
Tests for UDF registration in DuckDB
"""

import unittest
import os
import sys
import duckdb
from unittest.mock import patch, MagicMock

# Update path to include src directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from duckdb_llm_udf import register_llm_functions

class TestUDFRegistration(unittest.TestCase):
    """Test cases for registering UDFs in DuckDB"""
    
    def setUp(self):
        """Set up test environment"""
        self.conn = duckdb.connect(':memory:')
        
        # Create a simple test table
        self.conn.execute("""
            CREATE TABLE test_data (
                id INTEGER,
                value VARCHAR
            )
        """)
        
        # Insert sample data
        self.conn.execute("""
            INSERT INTO test_data VALUES
            (1, 'apple'),
            (2, 'banana'),
            (3, 'cherry')
        """)
    
    def test_function_registration(self):
        """Test that functions are properly registered in DuckDB"""
        # Register the LLM functions
        register_llm_functions(self.conn)
        
        # Let's verify the functions are registered by trying to call them
        # For the llm_configure function
        try:
            # This should work if the function is registered
            self.conn.execute("SELECT llm_configure('test_key', 'test_value')")
            llm_configure_registered = True
        except Exception:
            llm_configure_registered = False
            
        # For the ask_llm function (with mock to avoid actual LLM calls)
        with patch('duckdb_llm_udf.llm_udf._generate_sql_with_llm', return_value="SELECT 1"):
            try:
                # This should work if the function is registered
                # We use all parameters to avoid issues with optional parameters
                self.conn.execute("SELECT ask_llm('test_question', 'openai', 'gpt-3.5-turbo', 'test-key')")
                ask_llm_registered = True
            except Exception:
                ask_llm_registered = False
        
        # Verify both functions are registered
        self.assertTrue(ask_llm_registered, "ask_llm function was not properly registered")
        self.assertTrue(llm_configure_registered, "llm_configure function was not properly registered")
    
    @patch('duckdb_llm_udf.llm_udf._generate_sql_with_llm')
    def test_ask_llm_function_call(self, mock_generate_sql):
        """Test calling the ask_llm function via SQL"""
        # Set up the mock to return a simple SQL query
        mock_generate_sql.return_value = "SELECT * FROM test_data WHERE id = 1"
        
        # Register the LLM functions
        register_llm_functions(self.conn)
        
        # Configure with a dummy API key
        self.conn.execute("SELECT llm_configure('api_key', 'test-api-key')")
        
        # Test that llm_configure works - this will be used by ask_llm
        config_result = self.conn.execute("""
            SELECT llm_configure('model', 'test-model')
        """).fetchone()[0]
        
        self.assertIn("Configuration updated", config_result)
        
        # Mock user input for confirmation prompt (patching Python's built-in input function)
        with patch('builtins.input', return_value='n'):  # Answer 'no' to execution prompt
            # Call ask_llm with all parameters since optional parameters might be causing issues
            result = self.conn.execute("""
                SELECT ask_llm('Find the apple', 'openai', 'test-model', 'test-api-key')
            """).fetchone()[0]
        
        # Verify ask_llm was called and returned expected output
        self.assertIn("SQL execution cancelled", result)
        
        # Verify our mock was called with appropriate arguments
        mock_generate_sql.assert_called_once()
        
        # Check if the correct question was passed to the LLM
        args, kwargs = mock_generate_sql.call_args
        self.assertEqual(args[0], "Find the apple")
    
    def test_multiple_parameter_formats(self):
        """Test calling UDFs with different parameter formats"""
        # Register the LLM functions
        register_llm_functions(self.conn)
        
        # Set a configuration with standard parameter ordering
        result1 = self.conn.execute("SELECT llm_configure('provider', 'openai')").fetchone()[0]
        
        # Set a configuration with named parameters
        result2 = self.conn.execute("""
            SELECT llm_configure(key => 'model', value => 'gpt-4')
        """).fetchone()[0]
        
        # Verify both calls worked
        self.assertIn("Configuration updated", result1)
        self.assertIn("Configuration updated", result2)

if __name__ == "__main__":
    unittest.main()
