"""
Core implementation of the DuckDB LLM UDF extension.
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple, Union
import duckdb
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('duckdb_llm_udf')

# Import dotenv for .env file support
try:
    from dotenv import load_dotenv
    # Try to load from .env file if it exists
    load_dotenv()
    logger.info("Loaded environment variables from .env file")
except ImportError:
    # python-dotenv is not installed, just continue without it
    logger.warning("python-dotenv not installed, .env file support is disabled")
    pass

# Global configuration
_config = {
    "provider": os.environ.get("LLM_PROVIDER", "openai"),
    "model": os.environ.get("LLM_MODEL", "gpt-3.5-turbo"),
    "api_key": os.environ.get("OPENAI_API_KEY", os.environ.get("ANTHROPIC_API_KEY", "")),
    "temperature": 0.7,
    "max_tokens": 4096
}

# Global configuration lock
_config_lock = threading.Lock()

# Helper functions to get config, always preferring environment variables

def get_provider():
    return os.environ.get("LLM_PROVIDER", _config["provider"])

def get_model():
    return os.environ.get("LLM_MODEL", _config["model"])

def get_api_key():
    return os.environ.get("OPENAI_API_KEY", os.environ.get("ANTHROPIC_API_KEY", _config["api_key"]))

def get_temperature():
    return float(os.environ.get("LLM_TEMPERATURE", _config["temperature"]))

def get_max_tokens():
    return int(os.environ.get("LLM_MAX_TOKENS", _config["max_tokens"]))

def _get_config() -> Dict[str, Any]:
    """Get a copy of the current configuration, with env precedence."""
    with _config_lock:
        return {
            "provider": get_provider(),
            "model": get_model(),
            "api_key": get_api_key(),
            "temperature": get_temperature(),
            "max_tokens": get_max_tokens(),
        }

def _extract_schema_metadata(conn: duckdb.DuckDBPyConnection) -> str:
    """
    Extract schema metadata from the database.
    
    Args:
        conn: DuckDB connection
        
    Returns:
        str: Formatted schema metadata as a string
    """
    logger.info("Extracting schema metadata from the database")
    start_time = time.time()
    schema_info = []
    
    # Get list of tables
    tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()
    
    for table in tables:
        table_name = table[0]
        # Get columns for each table
        columns = conn.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema='main' AND table_name='{table_name}'
        """).fetchall()
        
        column_info = [f"{col[0]} {col[1]}" for col in columns]
        
        # Get sample data (first 3 rows) to help the LLM understand the data better
        try:
            sample_data = conn.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchall()
            sample_str = "\n    - Sample data: " + str(sample_data) if sample_data else ""
        except:
            sample_str = ""
        
        # Get primary keys if available
        try:
            pk_query = f"""
                SELECT column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_name = '{table_name}'
            """
            pks = conn.execute(pk_query).fetchall()
            pk_str = f"\n    - Primary key(s): {', '.join([pk[0] for pk in pks])}" if pks else ""
        except:
            pk_str = ""
        
        # Get foreign keys if available
        try:
            fk_query = f"""
                SELECT kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON tc.constraint_name = ccu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name = '{table_name}'
            """
            fks = conn.execute(fk_query).fetchall()
            fk_str = ""
            if fks:
                fk_str = "\n    - Foreign key(s): "
                for fk in fks:
                    fk_str += f"{fk[0]} references {fk[1]}({fk[2]}), "
                fk_str = fk_str[:-2]  # Remove trailing comma and space
        except:
            fk_str = ""
        
        schema_info.append(f"Table: {table_name}\n  Columns: {', '.join(column_info)}{pk_str}{fk_str}{sample_str}")
    
    schema_text = "\n\n".join(schema_info)
    end_time = time.time()
    logger.info(f"Schema extraction completed in {end_time - start_time:.2f} seconds")
    return schema_text

def _generate_prompt(question: str, schema: str, provider: str = "openai") -> str:
    """
    Generate a prompt for the LLM based on the question and schema.
    
    Args:
        question: User's natural language question
        schema: Database schema information
        provider: LLM provider (to adjust prompt format)
        
    Returns:
        str: Formatted prompt
    """
    logger.info(f"Generating prompt for question: {question}")
    start_time = time.time()
    prompt = f"""You are a SQL expert assistant that helps users generate SQL queries from natural language questions.
    
Database Schema:
{schema}

User Question: {question}

Your task is to generate a valid SQL query that answers the user's question based on the database schema provided.

Important guidelines:
1. Only use tables and columns that exist in the schema
2. Add informative column aliases when appropriate
3. Include appropriate JOINs based on the schema relationships
4. Ensure the SQL is optimized and follows best practices
5. If the question is ambiguous, make reasonable assumptions
6. Only produce a single SQL query
7. Do not include any explanation, just the SQL query
8. Format the SQL nicely with proper indentation

SQL Query:
"""
    end_time = time.time()
    logger.info(f"Prompt generation completed in {end_time - start_time:.2f} seconds")
    return prompt

def _clean_sql_output(sql: str) -> str:
    """
    Clean the SQL output from LLM to remove markdown formatting.
    
    Args:
        sql: SQL string potentially with markdown formatting
        
    Returns:
        str: Clean SQL string without markdown formatting
    """
    # Handle markdown code blocks
    if "```" in sql:
        # Find content between code blocks
        start_idx = sql.find("```")
        if start_idx >= 0:
            # Skip the opening ```
            start_idx += 3
            # Skip the language specifier if present (e.g., "sql")
            if sql[start_idx:].lstrip().startswith("sql"):
                start_idx = sql.find("\n", start_idx) + 1
            elif sql[start_idx] == '\n':
                start_idx += 1
                
            # Find the end of the code block
            end_idx = sql.find("```", start_idx)
            if end_idx >= 0:
                sql = sql[start_idx:end_idx].strip()
    
    # Remove any standalone "sql" markers
    if sql.strip().lower().startswith("sql"):
        sql = sql[3:].strip()
    
    return sql.strip()

def _call_openai_api(prompt: str, model: str, api_key: str, temperature: float = 0.7, max_tokens: int = 1024) -> str:
    """
    Call the OpenAI API to generate SQL from the prompt.
    
    Args:
        prompt: The formatted prompt for the LLM
        model: OpenAI model to use
        api_key: OpenAI API key
        temperature: Temperature parameter for generation
        max_tokens: Maximum tokens to generate
        
    Returns:
        str: Generated SQL query
    """
    logger.info(f"Calling OpenAI API with model: {model}")
    start_time = time.time()
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        result = response.choices[0].message.content.strip()
        end_time = time.time()
        logger.info(f"OpenAI API call completed in {end_time - start_time:.2f} seconds")
        return result
    except ImportError:
        logger.error("OpenAI Python package is not installed")
        return "ERROR: OpenAI Python package is not installed. Install with 'pip install openai'."
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        return f"ERROR: {str(e)}"

def _call_anthropic_api(prompt: str, model: str, api_key: str, temperature: float = 0.7, max_tokens: int = 1024) -> str:
    """
    Call the Anthropic API to generate SQL from the prompt.
    
    Args:
        prompt: The formatted prompt for the LLM
        model: Anthropic model to use
        api_key: Anthropic API key
        temperature: Temperature parameter for generation
        max_tokens: Maximum tokens to generate
        
    Returns:
        str: Generated SQL query
    """
    logger.info(f"Calling Anthropic API with model: {model}")
    start_time = time.time()
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = response.content[0].text
        end_time = time.time()
        logger.info(f"Anthropic API call completed in {end_time - start_time:.2f} seconds")
        return result
    except ImportError:
        logger.error("Anthropic Python package is not installed")
        return "ERROR: Anthropic Python package is not installed. Install with 'pip install anthropic'."
    except Exception as e:
        logger.error(f"Error calling Anthropic API: {str(e)}")
        return f"ERROR: {str(e)}"

def _generate_sql_with_llm(question: str, schema: str, provider: str, model: str, api_key: str, 
                           temperature: float = 0.7, max_tokens: int = 1024) -> str:
    """
    Generate SQL using the specified LLM provider.
    
    Args:
        question: User's natural language question
        schema: Database schema information
        provider: LLM provider ('openai' or 'anthropic')
        model: Model to use
        api_key: API key for the provider
        temperature: Temperature parameter
        max_tokens: Maximum tokens to generate
        
    Returns:
        str: Generated SQL query
    """
    logger.info(f"Generating SQL with provider: {provider}, model: {model}")
    start_time = time.time()
    prompt = _generate_prompt(question, schema, provider)
    
    result = None
    if provider.lower() == 'openai':
        result = _call_openai_api(prompt, model, api_key, temperature, max_tokens)
    elif provider.lower() == 'anthropic':
        result = _call_anthropic_api(prompt, model, api_key, temperature, max_tokens)
    else:
        error_msg = f"ERROR: Unsupported provider '{provider}'. Supported providers are 'openai' and 'anthropic'."
        logger.error(error_msg)
        return error_msg
        
    # Clean the result to handle markdown formatting
    cleaned_result = _clean_sql_output(result)
    
    # Log the result and timing
    logger.info(f"SQL generation completed in {time.time() - start_time:.2f} seconds")
    return cleaned_result

def ask_llm(question: str, conn: duckdb.DuckDBPyConnection, 
            provider: Optional[str] = None, model: Optional[str] = None, 
            api_key: Optional[str] = None, execute: bool = True) -> Union[str, List[Any]]:
    """
    Generate and optionally execute SQL from a natural language question.
    
    Args:
        question: User's natural language question
        conn: DuckDB connection
        provider: LLM provider override (default: use global config)
        model: Model override (default: use global config)
        api_key: API key override (default: use global config)
        execute: Whether to execute the generated SQL (default: True)
    Returns:
        str or list: Generated SQL or query results
    """
    logger.info(f"Processing natural language question: '{question}'")
    total_start_time = time.time()
    # Use environment-variable-respecting config getters unless overridden
    prov = provider if provider is not None else get_provider()
    mdl = model if model is not None else get_model()
    key = api_key if api_key is not None else get_api_key()
    temp = get_temperature()
    max_toks = get_max_tokens()
    
    if not key:
        logger.error("No API key provided")
        return "ERROR: No API key provided. Please set your API key using llm_configure('api_key', 'YOUR-API-KEY')."
    
    schema = _extract_schema_metadata(conn)
    sql = _generate_sql_with_llm(question, schema, prov, mdl, key, temp, max_toks)
    
    if sql.startswith("ERROR:"):
        logger.error(sql)
        return sql
    
    if not execute:
        total_end_time = time.time()
        logger.info(f"Total processing time (no execution): {total_end_time - total_start_time:.2f} seconds")
        return sql
    
    print(f"Generated SQL:\n{sql}\n")
    confirm = input("Do you want to execute this SQL? (y/n): ")
    
    if confirm.lower() == 'y':
        try:
            logger.info("Executing SQL query")
            sql_start_time = time.time()
            result = conn.execute(sql).fetchall()
            sql_end_time = time.time()
            logger.info(f"SQL execution completed in {sql_end_time - sql_start_time:.2f} seconds")
            total_end_time = time.time()
            logger.info(f"Total processing time: {total_end_time - total_start_time:.2f} seconds")
            return result
        except Exception as e:
            logger.error(f"Error executing SQL: {str(e)}")
            return f"ERROR executing SQL: {str(e)}"
    else:
        logger.info("SQL execution cancelled by user")
        return "SQL execution cancelled by user."

def llm_configure(key: str, value: Any) -> str:
    """
    Configure the global LLM settings.
    
    Args:
        key: Configuration key to set
        value: Value to set
        
    Returns:
        str: Confirmation message
    """
    valid_keys = ['provider', 'model', 'api_key', 'temperature', 'max_tokens']
    
    if key not in valid_keys:
        return f"ERROR: Invalid configuration key '{key}'. Valid keys are: {', '.join(valid_keys)}."
    
    with _config_lock:
        _config[key] = value
    
    return f"Configuration updated: {key} = {value if key != 'api_key' else '****'}"

def _register_ask_llm(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Register the ask_llm UDF in DuckDB.
    
    Args:
        conn: DuckDB connection
    """
    logger.info("Registering ask_llm UDF in DuckDB")
    def _ask_llm_wrapper(question: str, provider: Optional[str] = None, 
                        model: Optional[str] = None, api_key: Optional[str] = None) -> str:
        return ask_llm(question, conn, provider, model, api_key)
    
    conn.create_function("ask_llm", _ask_llm_wrapper, [
        duckdb.typing.VARCHAR,  # question
        duckdb.typing.VARCHAR,  # provider (optional)
        duckdb.typing.VARCHAR,  # model (optional)
        duckdb.typing.VARCHAR   # api_key (optional)
    ], duckdb.typing.VARCHAR)

def _register_llm_configure(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Register the llm_configure UDF in DuckDB.
    
    Args:
        conn: DuckDB connection
    """
    logger.info("Registering llm_configure UDF in DuckDB")
    conn.create_function("llm_configure", llm_configure, [
        duckdb.typing.VARCHAR,  # key
        duckdb.typing.VARCHAR   # value
    ], duckdb.typing.VARCHAR)

def register_llm_functions(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Register all LLM UDFs in the given DuckDB connection.
    
    Args:
        conn: DuckDB connection
    """
    logger.info("Registering all LLM UDFs in DuckDB")
    _register_ask_llm(conn)
    _register_llm_configure(conn)
