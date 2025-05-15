import os
import time
import json
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from redis import Redis
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@postgres_db:5432/postgres")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

def get_redis_connection() -> Redis:
    """Create and return Redis connection"""
    return Redis.from_url(REDIS_URL, decode_responses=True)

def wait_for_dependencies():
    """Wait for both database and Redis to be ready"""
    engine = create_engine(DATABASE_URL)
    redis = get_redis_connection()
    
    attempts = 0
    max_attempts = 20
    db_ready = False
    redis_ready = False
    
    while attempts < max_attempts and not (db_ready and redis_ready):
        try:
            if not db_ready:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    db_ready = True
                    logger.info("Database connection established")
        except OperationalError as e:
            logger.warning(f"Database not ready (attempt {attempts + 1}/{max_attempts}): {e}")
        
        try:
            if not redis_ready:
                redis.ping()
                redis_ready = True
                logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis not ready (attempt {attempts + 1}/{max_attempts}): {e}")
        
        if not (db_ready and redis_ready):
            time.sleep(5)
            attempts += 1
    
    if not db_ready or not redis_ready:
        raise ConnectionError("Failed to connect to dependencies")

def clear_redis_cache(redis: Redis):
    """Clear all Redis cache keys"""
    try:
        redis.flushall()
        logger.info("Redis cache cleared")
    except Exception as e:
        logger.error(f"Error clearing Redis cache: {e}")
        raise

def initialize_database():
    """Initialize database schema and sample data"""
    engine = create_engine(DATABASE_URL)
    
    with engine.begin() as conn:  # Automatically commits/rolls back
        # Drop tables if they exist
        conn.execute(text("""
        DROP TABLE IF EXISTS cart_items CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
        DROP TABLE IF EXISTS products CASCADE;
        """))
        
        # Create tables with improved schema
        conn.execute(text("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE,
            role VARCHAR(20) DEFAULT 'user',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP WITH TIME ZONE,
            login_count INTEGER DEFAULT 0
        );
        """))
        
        conn.execute(text("""
        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            price NUMERIC(10, 2) NOT NULL CHECK (price > 0),
            stock_quantity INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE
        );
        """))
        
        conn.execute(text("""
        CREATE TABLE cart_items (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
            price_at_add NUMERIC(10, 2) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE,
            CONSTRAINT unique_user_product UNIQUE (user_id, product_id)
        );
        """))
        
        # Create indexes
        conn.execute(text("""
        CREATE INDEX idx_user_email ON users(email);
        CREATE INDEX idx_product_name ON products(name);
        CREATE INDEX idx_cart_user ON cart_items(user_id);
        """))
        
        # Insert sample data
        conn.execute(text("""
        INSERT INTO users (username, email, password_hash, full_name, role)
        VALUES 
            ('admin', 'admin@example.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Admin User', 'admin'),
            ('alice', 'alice@example.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Alice Smith', 'user'),
            ('bob', 'bob@example.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Bob Johnson', 'user');
        """))
        
        conn.execute(text("""
        INSERT INTO products (name, description, price, stock_quantity)
        VALUES 
            ('Книга', 'Интересная книга', 1200.00, 50),
            ('Ноутбук', 'Мощный ноутбук', 75000.00, 10),
            ('Кофе', 'Арабика 250г', 250.00, 100),
            ('Телефон', 'Смартфон последней модели', 50000.00, 25);
        """))
        
        conn.execute(text("""
        INSERT INTO cart_items (user_id, product_id, quantity, price_at_add)
        VALUES 
            (2, 1, 2, 1200.00),
            (2, 3, 1, 250.00),
            (3, 2, 1, 75000.00),
            (3, 4, 1, 50000.00);
        """))
        
        logger.info("Database schema initialized with sample data")

def initialize_redis(redis: Redis):
    """Initialize Redis with default values"""
    try:
        # Set configuration values
        redis.config_set("maxmemory", "100mb")
        redis.config_set("maxmemory-policy", "allkeys-lru")
        
        # Create sample cache entries
        sample_users = [
            {"id": 1, "username": "admin", "role": "admin"},
            {"id": 2, "username": "alice", "role": "user"}
        ]
        
        for user in sample_users:
            redis.set(f"user:{user['id']}", json.dumps(user))
        
        logger.info("Redis initialized with sample data")
    except Exception as e:
        logger.error(f"Error initializing Redis: {e}")
        raise

if __name__ == "__main__":
    try:
        logger.info("Starting initialization process")
        wait_for_dependencies()
        
        redis = get_redis_connection()
        clear_redis_cache(redis)
        
        initialize_database()
        initialize_redis(redis)
        
        logger.info("Initialization completed successfully")
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        raise