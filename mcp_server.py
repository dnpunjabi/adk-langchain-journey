import asyncio
import sqlite3
import os
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Acme Product Server")

# Initialize a simple SQLite database in memory for demonstration
def init_db():
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            price REAL,
            stock INTEGER
        )
    ''')
    
    # Insert some dummy data if empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        products = [
            ("Quantum Laptop", "Electronics", 120000.0, 15),
            ("Neural Headphones", "Audio", 15000.0, 50),
            ("Smart Coffee Mug", "Lifestyle", 2500.0, 100),
            ("Ergo Desk Lamp", "Office", 4500.0, 30),
            ("Wireless Mech Keyboard", "Electronics", 8500.0, 25)
        ]
        cursor.executemany("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", products)
        conn.commit()
    return conn

@mcp.tool()
def search_products(query: str) -> str:
    """Search for products in the Acme catalog by name or category.
    
    Args:
        query: The search term for product name or category.
    """
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    # Normalize query: lowercase and remove trailing 's' for simple plural handling
    clean_query = query.lower().rstrip('s')
    search_term = f"%{clean_query}%"
    cursor.execute("SELECT name, category, price, stock FROM products WHERE name LIKE ? OR category LIKE ?", (search_term, search_term))
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        return f"No products found for '{query}'."
    
    output = "Found the following products:\n"
    for r in results:
        output += f"- {r[0]} ({r[1]}): ₹{r[2]} | Stock: {r[3]}\n"
    return output

if __name__ == "__main__":
    init_db()
    mcp.run()
