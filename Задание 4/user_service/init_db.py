import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@postgres_db:5432/postgres")

def wait_for_db():
    engine = create_engine(DATABASE_URL)
    attempts = 0
    while attempts < 10:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print("База данных готова")
                return True
        except OperationalError:
            attempts += 1
            print(f"Ожидание базы данных (попытка {attempts}/10)...")
            time.sleep(5)
    raise Exception("Не удалось подключиться к базе данных")

def init_db():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS cart_items CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS products CASCADE;"))
        conn.commit()

        conn.execute(text("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL
        );
        """))
        
        conn.execute(text("""
        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            price NUMERIC(10, 2) NOT NULL
        );
        """))
        
        conn.execute(text("""
        CREATE TABLE cart_items (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL DEFAULT 1,
            price_at_add NUMERIC(10, 2) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        );
        """))
        
        conn.execute(text("""
        CREATE UNIQUE INDEX idx_user_product ON cart_items(user_id, product_id);
        CREATE INDEX idx_cart_user_id ON cart_items(user_id);
        CREATE INDEX idx_cart_product_id ON cart_items(product_id);
        """))
        conn.commit()

        conn.execute(text("""
        INSERT INTO users (username)
        VALUES ('alice'), ('bob');
        """))
        
        conn.execute(text("""
        INSERT INTO products (name, price)
        VALUES 
            ('Книга', 1200.00),
            ('Ноутбук', 75000.00),
            ('Кофе', 250.00);
        """))
        
        conn.execute(text("""
        INSERT INTO cart_items (user_id, product_id, quantity, price_at_add)
        VALUES 
            (1, 1, 2, 1200.00),
            (1, 3, 1, 250.00),
            (2, 2, 1, 75000.00);
        """))
        conn.commit()
        print("Создание базы данных завершено")

if __name__ == "__main__":
    wait_for_db()
    init_db()