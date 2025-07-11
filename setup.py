#!/usr/bin/env python3
"""
Setup script for Startup Intelligence System
Initializes database, checks dependencies, and validates configuration
"""
import asyncio
import os
import sys
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Check Python version compatibility"""
    if sys.version_info < (3, 9):
        logger.error("Python 3.9 or higher is required")
        return False
    
    logger.info(f"Python version: {sys.version}")
    return True

def check_postgresql():
    """Check if PostgreSQL is available"""
    try:
        result = subprocess.run(['psql', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"PostgreSQL found: {result.stdout.strip()}")
            return True
        else:
            logger.warning("PostgreSQL not found in PATH")
            return False
    except FileNotFoundError:
        logger.warning("PostgreSQL not found. Please install PostgreSQL 13+")
        return False

def install_dependencies():
    """Install Python dependencies"""
    logger.info("Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        logger.info("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def setup_environment():
    """Setup environment variables"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists():
        if env_example.exists():
            logger.info("Creating .env file from template...")
            with open(env_example, 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            logger.info("Please edit .env file with your configuration")
        else:
            logger.error(".env.example file not found")
            return False
    else:
        logger.info(".env file already exists")
    
    return True

def create_database():
    """Create PostgreSQL database if it doesn't exist"""
    db_name = 'startup_intelligence'
    
    logger.info(f"Checking if database '{db_name}' exists...")
    
    try:
        # Check if database exists
        result = subprocess.run([
            'psql', '-h', 'localhost', '-U', 'postgres', '-lqt'
        ], capture_output=True, text=True, input='')
        
        if db_name in result.stdout:
            logger.info(f"Database '{db_name}' already exists")
            return True
        
        # Create database
        logger.info(f"Creating database '{db_name}'...")
        subprocess.run([
            'createdb', '-h', 'localhost', '-U', 'postgres', db_name
        ], check=True)
        
        logger.info(f"Database '{db_name}' created successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create database: {e}")
        logger.info("Please create the database manually:")
        logger.info(f"  createdb -U postgres {db_name}")
        return False
    except FileNotFoundError:
        logger.warning("PostgreSQL tools not found. Please create database manually.")
        return False

async def initialize_database():
    """Initialize database tables"""
    logger.info("Initializing database tables...")
    
    try:
        # Import after dependencies are installed
        from config.settings import Config
        from src.data.database import DatabaseManager
        
        config = Config.load_from_env()
        db = DatabaseManager(config.database)
        
        await db.initialize()
        await db.close()
        
        logger.info("Database tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        'data/raw',
        'data/processed', 
        'data/outputs',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def validate_setup():
    """Validate the setup"""
    logger.info("Validating setup...")
    
    try:
        # Try importing main modules
        from config.settings import Config
        from src.discovery.discovery_engine import StartupDiscoveryEngine
        
        config = Config.load_from_env()
        issues = config.validate()
        
        if issues:
            logger.warning("Configuration issues found:")
            for issue in issues:
                logger.warning(f"  - {issue}")
            logger.info("Some features may not work without proper API keys")
        else:
            logger.info("Configuration is valid")
        
        return True
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False

async def main():
    """Main setup routine"""
    logger.info("Starting Startup Intelligence System setup...")
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    # Create directories
    create_directories()
    
    # Setup environment
    if not setup_environment():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Check PostgreSQL
    postgres_available = check_postgresql()
    
    if postgres_available:
        # Create database
        if create_database():
            # Initialize database tables
            if not await initialize_database():
                return False
    else:
        logger.warning("Skipping database setup. Please install PostgreSQL and run setup again.")
    
    # Validate setup
    if not validate_setup():
        return False
    
    logger.info("Setup completed successfully!")
    logger.info("\nNext steps:")
    logger.info("1. Edit .env file with your API keys")
    logger.info("2. Run: python main.py discover")
    logger.info("3. View results: python main.py analyze --top 10")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
