# Tech Context - Startup Intelligence System

## Technologies Used

### Core Language
**Python 3.9+**
- Chosen for excellent web scraping libraries
- Strong async/await support for concurrent operations
- Rich ecosystem for data analysis and ML
- Type hints for better code maintainability

### Web Scraping & APIs
**aiohttp** - Async HTTP client for concurrent requests
**BeautifulSoup4** - HTML parsing and data extraction
**feedparser** - RSS feed parsing (GeekWire)
**requests** - Synchronous HTTP for simple operations
**selenium** - Browser automation (future LinkedIn enhancement)

### Database
**PostgreSQL 13+**
- Complex queries for multi-criteria filtering
- JSON support for flexible data storage
- Full-text search capabilities
- Robust transaction support

**asyncpg** - High-performance async PostgreSQL driver
- Connection pooling
- Prepared statements
- Native PostgreSQL protocol

### Data Processing
**pandas** - Data manipulation and analysis
**numpy** - Numerical operations
**python-dateutil** - Date parsing and manipulation

### Configuration & Environment
**python-dotenv** - Environment variable management
**pydantic** - Data validation and settings management

### Testing
**pytest** - Test framework
**pytest-asyncio** - Async test support
**pytest-mock** - Mocking capabilities

### UI/Visualization
**Jinja2** - HTML template generation
**Rich** - Terminal formatting and tables

## Development Setup

### Prerequisites
```bash
# System requirements
- Python 3.9 or higher
- PostgreSQL 13 or higher
- Git
- Virtual environment tool (venv/virtualenv)

# Optional but recommended
- GitHub personal access token
- Crunchbase API key (future)
```

### Installation Steps
```bash
# 1. Clone repository
git clone https://github.com/robandrewford/startup-intelligence-system.git
cd startup-intelligence-system

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env with your configuration

# 5. Initialize database
python setup.py

# 6. Run tests
python test_runner.py
```

### Environment Configuration
```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=startup_intelligence
DB_USER=your_username
DB_PASSWORD=your_password

# API Keys (Optional)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
CRUNCHBASE_API_KEY=xxxxxxxxxxxx
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxx

# Scraper Configuration
SCRAPER_DELAY=1.0  # Seconds between requests
SCRAPER_TIMEOUT=30  # Request timeout
SCRAPER_MAX_RETRIES=3

# Target Criteria
TARGET_LOCATION=Seattle
TARGET_MIN_EMPLOYEES=50
TARGET_MAX_EMPLOYEES=200
TARGET_INDUSTRIES=healthcare,ai,ml,b2b
```

## Technical Constraints

### API Rate Limits
**GitHub API**
- Authenticated: 5,000 requests/hour
- Unauthenticated: 60 requests/hour
- Strategy: Use token, implement caching

**Crunchbase API**
- Free tier: 100 requests/month
- Strategy: Selective enrichment only

**LinkedIn**
- No official API for job scraping
- Strategy: Mock data with manual enrichment

### Performance Requirements
**Discovery Run**
- Target: <30 minutes for full run
- Current: ~20 minutes typical
- Bottleneck: Sequential API calls

**Database Queries**
- Target: <2 seconds for complex filters
- Current: <500ms with indexes
- Optimization: Materialized views planned

**Memory Usage**
- Target: <500MB during discovery
- Current: ~300MB typical
- Strategy: Stream processing, no full loads

### Security Constraints
**API Keys**
- Never commit to repository
- Environment variables only
- Validate on startup

**Data Privacy**
- No PII beyond public profiles
- Local storage only
- No cloud analytics

**Scraping Ethics**
- Respect robots.txt
- Implement rate limiting
- User-agent identification

## Dependencies

### Core Dependencies
```txt
# requirements.txt
aiohttp==3.8.5
asyncpg==0.28.0
beautifulsoup4==4.12.2
feedparser==6.0.10
pandas==2.0.3
pydantic==2.3.0
python-dotenv==1.0.0
rich==13.5.2
jinja2==3.1.2
python-dateutil==2.8.2

# Testing
pytest==7.4.0
pytest-asyncio==0.21.1
pytest-mock==3.11.1
```

### Optional Dependencies
```txt
# For enhanced features
selenium==4.12.0  # Browser automation
webdriver-manager==4.0.0  # Chrome driver
numpy==1.25.2  # Numerical operations
scikit-learn==1.3.0  # Future ML features
```

## Tool Usage Patterns

### Async Pattern
```python
# All I/O operations use async/await
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

# Concurrent operations
results = await asyncio.gather(
    fetch_company_data(),
    fetch_github_info(),
    fetch_news_items()
)
```

### Database Pattern
```python
# Connection pooling
async with db.pool.acquire() as conn:
    # Prepared statements
    stmt = await conn.prepare(query)
    rows = await stmt.fetch(*params)
    
# Transaction handling
async with conn.transaction():
    await conn.execute(insert_query)
    await conn.execute(update_query)
```

### Configuration Pattern
```python
# Pydantic models for validation
class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str
    user: str
    password: SecretStr
    
    @validator('port')
    def valid_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Invalid port')
        return v
```

### Error Handling Pattern
```python
# Comprehensive error handling
try:
    result = await risky_operation()
except aiohttp.ClientError as e:
    logger.error(f"Network error: {e}")
    return fallback_result
except asyncio.TimeoutError:
    logger.error("Operation timed out")
    return None
except Exception as e:
    logger.exception("Unexpected error")
    raise
```

## Development Workflow

### Local Development
```bash
# 1. Activate environment
source venv/bin/activate

# 2. Run discovery
python main.py discover

# 3. Check results
python main.py analyze --top 10

# 4. Generate dashboard
python dashboard.py
open data/outputs/dashboard.html
```

### Testing Workflow
```bash
# Run all tests
python test_runner.py

# Run specific test
pytest tests/test_ai_washing.py -v

# Run with coverage
pytest --cov=src tests/
```

### Database Management
```bash
# Connect to database
psql -U your_user -d startup_intelligence

# Common queries
\dt  # List tables
\d companies  # Describe table
SELECT COUNT(*) FROM companies WHERE ai_washing_score > 7;
```

## Performance Optimization

### Caching Strategy
```python
# In-memory caching for API responses
cache = {}
cache_ttl = 3600  # 1 hour

async def get_cached_or_fetch(key, fetch_func):
    if key in cache:
        data, timestamp = cache[key]
        if time.time() - timestamp < cache_ttl:
            return data
    
    data = await fetch_func()
    cache[key] = (data, time.time())
    return data
```

### Batch Processing
```python
# Process in batches to avoid memory issues
BATCH_SIZE = 100

for i in range(0, len(companies), BATCH_SIZE):
    batch = companies[i:i + BATCH_SIZE]
    await process_batch(batch)
```

### Connection Pooling
```python
# Reuse database connections
pool = await asyncpg.create_pool(
    dsn=database_url,
    min_size=10,
    max_size=20,
    max_queries=50000,
    max_inactive_connection_lifetime=300
)
```

## Monitoring & Debugging

### Logging Configuration
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/discovery.log'),
        logging.StreamHandler()
    ]
)
```

### Performance Monitoring
```python
import time
from contextlib import asynccontextmanager

@asynccontextmanager
async def timed_operation(name):
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        logger.info(f"{name} took {duration:.2f} seconds")
```

### Debug Mode
```python
# Enable debug logging
if os.getenv('DEBUG') == 'true':
    logging.getLogger().setLevel(logging.DEBUG)
    # Enable SQL query logging
    logging.getLogger('asyncpg').setLevel(logging.DEBUG)
```

## Future Technical Enhancements

### Planned Improvements
1. **Redis Integration** - For distributed caching
2. **Celery** - For background task processing
3. **FastAPI** - REST API for web interface
4. **Docker** - Containerization for deployment
5. **Elasticsearch** - Full-text search enhancement

### ML Integration Plans
1. **Company Classification** - Predict strategic fit
2. **Response Prediction** - Optimize outreach timing
3. **Trend Analysis** - Market opportunity identification
4. **NLP Enhancement** - Better blog/content analysis

### Scalability Considerations
1. **Horizontal Scaling** - Multiple worker processes
2. **Queue System** - Decouple scraping from processing
3. **CDN Integration** - For dashboard assets
4. **Database Sharding** - For massive scale

This technical foundation provides a robust, scalable system while maintaining simplicity for the current use case.
