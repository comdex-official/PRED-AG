from dotenv import load_dotenv
import os

def load_config():
    """Load all environment variables"""
    load_dotenv()
    return {
        'db': load_db_config(),
        'question': {
            'default_count': int(os.getenv('DEFAULT_QUESTION_COUNT', 10)),
            'min_count': int(os.getenv('MIN_QUESTION_COUNT', 1)),
            'max_count': int(os.getenv('MAX_QUESTION_COUNT', 10))
        }
    }

def load_db_config():
    """Load database configuration"""
    return {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'database': os.getenv('DB_NAME')
    }

def get_database_url():
    """Get database URL from config"""
    config = load_db_config()
    return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?sslmode=disable" 