"""
Tests for error handling in the DuckDB LLM UDF extension
"""

import unittest
import os
import sys
import duckdb

# Update path to include src directory  
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from duckdb_llm_udf.llm_udf import (
    _generate_sql_with_llm,
    llm_configure,
    _get_config
)

class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling in the LLM UDF functions"""
    
    def setUp(self):
        """Set up test environment"""
        self.conn = duckdb.connect(':memory:')
        
        # Create a simple test table
        self.conn.execute("""
            CREATE TABLE test_table (
                id INTEGER,
                name VARCHAR
            )
        """)
    
    def test_invalid_provider(self):
        """Test handling of invalid provider"""
        schema = "Table: test_table\nColumns: id INTEGER, name VARCHAR"
        question = "Get all data"
        
        # Test with an invalid provider
        result = _generate_sql_with_llm(
            question=question, 
            schema=schema, 
            provider="invalid_provider", 
            model="gpt-3.5-turbo", 
            api_key="dummy-key"
        )
        
        # Should return an error message
        self.assertIn("ERROR", result)
        self.assertIn("Unsupported provider", result)
    
    def test_invalid_config_key(self):
        """Test handling of invalid configuration key"""
        result = llm_configure("invalid_key", "some_value")
        
        # Should return an error message
        self.assertIn("ERROR", result)
        self.assertIn("Invalid configuration key", result)
    
    def test_missing_api_key(self):
        """Test handling of missing API key"""
        # Clear any existing API key
        llm_configure("api_key", "")
        
        schema = "Table: test_table\nColumns: id INTEGER, name VARCHAR"
        question = "Get all data"
        
        # Test with an empty API key
        result = _generate_sql_with_llm(
            question=question, 
            schema=schema, 
            provider="openai", 
            model="gpt-3.5-turbo", 
            api_key=""
        )
        
        # OpenAI will return an error for empty API key
        self.assertIn("ERROR", result)
    
    def test_config_persistence(self):
        """Test that configuration changes persist"""
        # Set a config value
        llm_configure("model", "gpt-4")
        
        # Get the current config
        config = _get_config()
        
        # Verify the value was set
        self.assertEqual(config["model"], "gpt-4")
        
        # Change it again
        llm_configure("model", "claude-3-opus")
        
        # Verify it was updated
        config = _get_config()
        self.assertEqual(config["model"], "claude-3-opus")

if __name__ == "__main__":
    unittest.main()
