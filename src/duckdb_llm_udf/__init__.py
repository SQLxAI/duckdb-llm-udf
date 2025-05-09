"""
DuckDB LLM UDF - A Python extension for natural language querying in DuckDB
"""

from .llm_udf import register_llm_functions, ask_llm

__version__ = "0.1.4"
__all__ = ["register_llm_functions", "ask_llm"]
