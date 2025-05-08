-- Example of using the DuckDB LLM UDF extension in SQL

-- Load the extension
-- In a real environment, you would need to install the Python package first
INSTALL 'duckdb_llm_udf';
LOAD 'duckdb_llm_udf';

-- Create a sample database
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name VARCHAR,
    email VARCHAR,
    signup_date DATE
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date DATE,
    total_amount DECIMAL(10, 2),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Insert sample data
INSERT INTO customers VALUES
(1, 'John Smith', 'john@example.com', '2023-01-15'),
(2, 'Alice Brown', 'alice@example.com', '2023-02-20'),
(3, 'Bob Johnson', 'bob@example.com', '2023-03-10'),
(4, 'Emma Davis', 'emma@example.com', '2023-01-05'),
(5, 'Michael Wilson', 'michael@example.com', '2023-02-28');

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
(110, 5, '2023-04-25', 250.50);

-- Configure the LLM 
-- (In a real environment, you would set your API key)
SELECT llm_configure('api_key', 'your-api-key-here');
SELECT llm_configure('provider', 'openai');
SELECT llm_configure('model', 'gpt-3.5-turbo');

-- Use natural language to query the database
-- This will prompt for confirmation before executing
SELECT ask_llm('Show me the top 5 customers by revenue');

-- Alternative syntax with named parameters
SELECT ask_llm(
    question => 'What is the average order amount by month?',
    provider => 'openai',
    model => 'gpt-4'
);
