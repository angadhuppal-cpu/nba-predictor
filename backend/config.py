"""
Configuration management for NBA Prediction System
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""

    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    FLASK_APP = os.environ.get('FLASK_APP') or 'app.py'
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'

    # Server Configuration
    PORT = int(os.environ.get('PORT', 5000))
    HOST = os.environ.get('HOST', '0.0.0.0')

    # Database Configuration
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or '../database/nba_data.db'

    # NBA API Configuration
    NBA_STATS_API_URL = os.environ.get('NBA_STATS_API_URL') or 'https://stats.nba.com/stats'
    NBA_API_RATE_LIMIT = int(os.environ.get('NBA_API_RATE_LIMIT', 60))

    # Cache Configuration
    CACHE_TTL = int(os.environ.get('CACHE_TTL', 900))  # 15 minutes
    CACHE_ENABLED = os.environ.get('CACHE_ENABLED', 'true').lower() == 'true'

    # Model Configuration
    MODEL_PATH = os.environ.get('MODEL_PATH') or '../models'
    MODEL_VERSION = os.environ.get('MODEL_VERSION') or '1.0.0'

    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or '../logs/nba_predictor.log'

    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')

    # Data Update Schedule
    DATA_UPDATE_SCHEDULE = os.environ.get('DATA_UPDATE_SCHEDULE') or '0 */6 * * *'

    # Feature Flags
    ENABLE_ML_PREDICTIONS = os.environ.get('ENABLE_ML_PREDICTIONS', 'true').lower() == 'true'
    ENABLE_ADVANCED_ANALYTICS = os.environ.get('ENABLE_ADVANCED_ANALYTICS', 'true').lower() == 'true'

    # Prediction Parameters
    BACK_TO_BACK_PENALTY = float(os.environ.get('BACK_TO_BACK_PENALTY', 0.15))
    HEAVY_MINUTES_THRESHOLD = int(os.environ.get('HEAVY_MINUTES_THRESHOLD', 35))
    MAX_FATIGUE_IMPACT = float(os.environ.get('MAX_FATIGUE_IMPACT', 0.30))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # Additional production-specific settings


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DATABASE_PATH = ':memory:'  # Use in-memory database for tests


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
