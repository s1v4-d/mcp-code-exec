#!/usr/bin/env python3
"""Setup script for PostgreSQL database during initialization."""

import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def check_postgres_connection():
    """Check if PostgreSQL is accessible."""
    try:
        import asyncpg
    except ImportError:
        print("ERROR: asyncpg not installed. Run: pip install asyncpg")
        return False
    
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    print(f"Checking PostgreSQL connection at {host}:{port}...")
    
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database="postgres",
        )
        await conn.close()
        print(f"PostgreSQL is accessible at {host}:{port}")
        return True
        
    except Exception as e:
        print(f"Cannot connect to PostgreSQL: {e}")
        print("\nTo start PostgreSQL:")
        print("  - Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:14")
        print("  - Local: sudo service postgresql start")
        return False


async def create_database():
    """Create MCP demo database if it doesn't exist."""
    import asyncpg
    
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    database = os.getenv("POSTGRES_DB", "mcp_demo")
    
    print(f"\nCreating database '{database}'...")
    
    # Connect to default postgres database
    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database="postgres",
    )
    
    try:
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", database
        )
        
        if exists:
            print(f"✓ Database '{database}' already exists")
        else:
            # Create database
            await conn.execute(f'CREATE DATABASE {database}')
            print(f"✓ Database '{database}' created")
    
    finally:
        await conn.close()


async def create_schema(database: str):
    """Create database schema."""
    import asyncpg
    
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    print(f"\nSetting up schema in '{database}'...")
    
    # Read schema SQL file
    schema_file = project_root / "servers" / "postgres_mcp" / "setup" / "schema.sql"
    if not schema_file.exists():
        print(f"Schema file not found: {schema_file}")
        return False
    
    schema_sql = schema_file.read_text()
    
    # Connect to the target database
    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
    )
    
    try:
        await conn.execute(schema_sql)
        print("Schema created successfully")
        return True
        
    except Exception as e:
        print(f"Error creating schema: {e}")
        return False
        
    finally:
        await conn.close()


async def seed_data(database: str):
    """Seed sample data into database."""
    import asyncpg
    import random
    from datetime import datetime, timedelta
    
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    print(f"\nSeeding sample data into '{database}'...")
    
    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
    )
    
    try:
        # Sample customers
        customers = [
            ("Alice Johnson", "alice@example.com"),
            ("Bob Smith", "bob@example.com"),
            ("Charlie Brown", "charlie@example.com"),
            ("Diana Prince", "diana@example.com"),
            ("Eve Wilson", "eve@example.com"),
        ]
        
        print("  Seeding customers...")
        for name, email in customers:
            await conn.execute(
                "INSERT INTO customers (name, email) VALUES ($1, $2) ON CONFLICT (email) DO NOTHING",
                name, email
            )
        
        # Sample products
        products = [
            ("Laptop", "High-performance laptop", 999.99, 50, "electronics"),
            ("Mouse", "Wireless mouse", 29.99, 200, "electronics"),
            ("Keyboard", "Mechanical keyboard", 79.99, 150, "electronics"),
            ("Monitor", "27-inch 4K monitor", 399.99, 75, "electronics"),
            ("Desk Chair", "Ergonomic office chair", 249.99, 100, "furniture"),
            ("Desk", "Standing desk", 499.99, 50, "furniture"),
            ("Notebook", "Ruled notebook", 4.99, 500, "stationery"),
            ("Pen Set", "12-piece pen set", 12.99, 300, "stationery"),
        ]
        
        print("  Seeding products...")
        for name, desc, price, stock, category in products:
            await conn.execute(
                "INSERT INTO products (name, description, price, stock_quantity, category) "
                "VALUES ($1, $2, $3, $4, $5) ON CONFLICT DO NOTHING",
                name, desc, price, stock, category
            )
        
        # Sample orders
        print("  Seeding orders...")
        customer_ids = [row["id"] for row in await conn.fetch("SELECT id FROM customers")]
        product_ids = [row["id"] for row in await conn.fetch("SELECT id FROM products")]
        
        # Check if orders already exist
        existing_orders = await conn.fetchval("SELECT COUNT(*) FROM orders")
        if existing_orders > 0:
            print(f"  {existing_orders} orders already exist, skipping seed")
        else:
            for _ in range(20):
                customer_id = random.choice(customer_ids)
                order_date = datetime.now() - timedelta(days=random.randint(0, 90))
                
                # Create order
                order_id = await conn.fetchval(
                    "INSERT INTO orders (customer_id, order_date, total, status) "
                    "VALUES ($1, $2, $3, $4) RETURNING id",
                    customer_id, order_date, 0, random.choice(["pending", "completed", "shipped"])
                )
                
                # Add order items
                num_items = random.randint(1, 4)
                total = 0
                for _ in range(num_items):
                    product_id = random.choice(product_ids)
                    product = await conn.fetchrow("SELECT price FROM products WHERE id = $1", product_id)
                    quantity = random.randint(1, 3)
                    price = product["price"]
                    total += price * quantity
                    
                    await conn.execute(
                        "INSERT INTO order_items (order_id, product_id, quantity, price) "
                        "VALUES ($1, $2, $3, $4)",
                        order_id, product_id, quantity, price
                    )
                
                # Update order total
                await conn.execute("UPDATE orders SET total = $1 WHERE id = $2", total, order_id)
            
            print("  ✓ 20 sample orders created")
        
        # Show summary
        stats = await conn.fetchrow("""
            SELECT 
                (SELECT COUNT(*) FROM customers) as customer_count,
                (SELECT COUNT(*) FROM products) as product_count,
                (SELECT COUNT(*) FROM orders) as order_count
        """)
        
        print(f"\nDatabase seeded successfully!")
        print(f"  - Customers: {stats['customer_count']}")
        print(f"  - Products: {stats['product_count']}")
        print(f"  - Orders: {stats['order_count']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await conn.close()


async def setup_postgres():
    """Main setup function for PostgreSQL."""
    print("=" * 50)
    print("PostgreSQL MCP Server Setup")
    print("=" * 50)
    
    if not await check_postgres_connection():
        print("\nSetup failed: PostgreSQL is not accessible")
        return False
    
    database = os.getenv("POSTGRES_DB", "mcp_demo")
    
    try:
        # Create database
        await create_database()
        
        # Create schema
        schema_ok = await create_schema(database)
        if not schema_ok:
            return False
        
        # Seed data
        seed_ok = await seed_data(database)
        if not seed_ok:
            return False
        
        # Success
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        
        print("\n" + "=" * 50)
        print("PostgreSQL setup complete!")
        print("=" * 50)
        print("\nConnection details:")
        print(f"  Host: {host}:{port}")
        print(f"  Database: {database}")
        print(f"  User: {user}")
        print(f"\nConnection string:")
        print(f"  postgresql://{user}:{password}@{host}:{port}/{database}")
        print("\nTry these queries:")
        print("  SELECT * FROM customers LIMIT 5;")
        print("  SELECT * FROM orders WHERE total > 100;")
        
        return True
        
    except Exception as e:
        print(f"\nSetup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(setup_postgres())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
