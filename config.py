import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-should-really-change-this'
    # Configure MySQL connection using provided details
    MYSQL_USER = os.environ.get('MYSQL_USER', 'alihasanovm_alien')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '$2y5t4E4f')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'alihasanovm.helioho.st')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'alihasanovm_iris_db')
    # Construct the URI for SQLAlchemy, using pymysql driver
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # OpenAI API Key - Load from environment variable
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

    # File Upload Configuration
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB limit per PRD (FR-02)
    UPLOAD_EXTENSIONS = ['.pdf', '.docx']
    UPLOAD_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')

    # Internationalization (i18n) Settings - Removed

    # Other settings can be added here, e.g., Mail server, etc.

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # Add any development-specific settings here

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # Ensure SECRET_KEY and DATABASE_URL are set in the environment for production
    # Add production-specific settings like logging, etc.

# Dictionary to easily access config classes by name
config_by_name = dict(
    dev=DevelopmentConfig,
    prod=ProductionConfig
)

key = Config.SECRET_KEY
