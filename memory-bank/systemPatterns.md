# System Patterns - Startup Intelligence System

## System Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   CLI Tool  │  │  Dashboard   │  │  Future: Web UI  │   │
│  │  (main.py)  │  │(dashboard.py)│  │                  │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │          Discovery Engine (discovery_engine.py)      │    │
│  │  - Coordinates all scrapers                          │    │
│  │  - Manages deduplication                             │    │
│  │  - Calculates strategic scores                       │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Data Source Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │    YC    │  │ GeekWire │  │ LinkedIn │  │  GitHub  │   │
│  │ Scraper  │  │ Scraper  │  │ Scraper  │  │ Analyzer │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Analysis Layer                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │        AI-Washing Detector (ai_washing_detector.py)  │    │
│  │  - Blog analysis                                     │    │
│  │  - Job posting analysis                              │    │
│  │  - GitHub contribution scoring                       │    │
│  │  - Marketing authenticity                            │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Data Storage Layer                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │          PostgreSQL Database (database.py)           │    │
│  │  - Companies table                                   │    │
│  │  - Funding rounds table                              │    │
│  │  - Company intelligence table                        │    │
│  │  - Discovery runs table                              │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Key Technical Decisions

### 1. Asynchronous Architecture
**Pattern**: All I/O operations use Python's asyncio
**Rationale**: Enables concurrent API calls and web scraping
**Implementation**:
```python
async def discover_companies():
    tasks = [
        scrape_yc_companies(),
        scrape_geekwire(),
        analyze_github_orgs(),
        scrape_linkedin_jobs()
    ]
    results = await asyncio.gather(*tasks)
```

### 2. Modular Scraper Design
**Pattern**: Each data source has independent scraper module
**Rationale**: Fault isolation and easy maintenance
**Benefits**:
- Single scraper failure doesn't break system
- Easy to add new data sources
- Independent testing and updates

### 3. Configuration Management
**Pattern**: Environment variables + settings.py
**Rationale**: Security and flexibility
**Structure**:
```python
class Config:
    database: DatabaseConfig
    apis: APIConfig
    scrapers: ScraperConfig
    target_criteria: TargetCriteria
```

### 4. Database Design
**Pattern**: Normalized relational schema with PostgreSQL
**Rationale**: Complex queries and relationship tracking
**Key Tables**:
- companies: Core entity
- funding_rounds: Investment history
- company_intelligence: Analysis results
- discovery_runs: Performance tracking

## Design Patterns in Use

### 1. Factory Pattern
**Usage**: Creating scraper instances
```python
class ScraperFactory:
    @staticmethod
    def create_scraper(source: str) -> BaseScraper:
        if source == "yc":
            return YCombinatorScraper()
        elif source == "geekwire":
            return GeekWireScraper()
        # etc...
```

### 2. Strategy Pattern
**Usage**: AI-washing detection algorithms
```python
class AIWashingDetector:
    def __init__(self):
        self.strategies = [
            BlogAnalysisStrategy(),
            JobPostingStrategy(),
            GitHubContributionStrategy(),
            MarketingContentStrategy()
        ]
```

### 3. Observer Pattern
**Usage**: Discovery run notifications (future)
```python
class DiscoveryEngine:
    def notify_observers(self, event: str, data: dict):
        for observer in self.observers:
            observer.update(event, data)
```

### 4. Repository Pattern
**Usage**: Database operations abstraction
```python
class CompanyRepository:
    async def find_by_criteria(self, criteria: dict) -> List[Company]:
        # Complex query logic abstracted
```

## Component Relationships

### Data Flow
```
External APIs → Scrapers → Discovery Engine → AI-Washing Detector → Database → UI
                              ↓                      ↓
                        Deduplication          Strategic Scoring
```

### Dependency Graph
```
main.py
  └── discovery_engine.py
        ├── yc_scraper.py
        ├── geekwire_scraper.py
        ├── linkedin_scraper.py
        ├── github_analyzer.py
        └── ai_washing_detector.py
              └── database.py
                    └── config/settings.py
```

## Critical Implementation Paths

### 1. Discovery Pipeline
```python
async def run_daily_discovery():
    # 1. Gather from all sources concurrently
    raw_companies = await gather_all_sources()
    
    # 2. Deduplicate by domain/name
    unique_companies = deduplicate(raw_companies)
    
    # 3. Enrich with additional data
    enriched = await enrich_companies(unique_companies)
    
    # 4. Calculate AI-washing scores
    scored = await calculate_ai_scores(enriched)
    
    # 5. Apply strategic filters
    filtered = apply_target_criteria(scored)
    
    # 6. Store in database
    await store_companies(filtered)
    
    # 7. Generate report
    return generate_discovery_report(filtered)
```

### 2. AI-Washing Detection Pipeline
```python
async def calculate_ai_washing_score(company):
    scores = {
        'blog_depth': await analyze_engineering_blog(company),
        'ml_engineers': await calculate_ml_engineer_ratio(company),
        'github_activity': await analyze_github_contributions(company),
        'marketing_authenticity': await assess_marketing_content(company)
    }
    
    # Weighted average with emphasis on technical signals
    weights = {
        'blog_depth': 0.3,
        'ml_engineers': 0.3,
        'github_activity': 0.25,
        'marketing_authenticity': 0.15
    }
    
    return calculate_weighted_score(scores, weights)
```

### 3. Strategic Scoring Pipeline
```python
def calculate_strategic_fit(company, user_criteria):
    scores = {
        'location_match': score_location(company, user_criteria.location),
        'stage_match': score_funding_stage(company, user_criteria.stage),
        'size_match': score_company_size(company, user_criteria.size_range),
        'industry_match': score_industry_fit(company, user_criteria.industries),
        'healthcare_relevance': score_healthcare_focus(company)
    }
    
    # Rob's specific weightings
    weights = {
        'healthcare_relevance': 0.35,  # Highest priority
        'location_match': 0.25,        # Seattle focus
        'stage_match': 0.20,           # Series A-B
        'industry_match': 0.15,        # AI/ML focus
        'size_match': 0.05             # Team size
    }
    
    return calculate_weighted_score(scores, weights)
```

## Error Handling Patterns

### 1. Graceful Degradation
```python
async def scrape_with_fallback(scraper, fallback_data=None):
    try:
        return await scraper.scrape()
    except Exception as e:
        logger.error(f"Scraper failed: {e}")
        if fallback_data:
            return fallback_data
        return []
```

### 2. Rate Limiting
```python
class RateLimiter:
    def __init__(self, calls_per_second=1):
        self.delay = 1.0 / calls_per_second
        self.last_call = 0
    
    async def wait(self):
        elapsed = time.time() - self.last_call
        if elapsed < self.delay:
            await asyncio.sleep(self.delay - elapsed)
        self.last_call = time.time()
```

### 3. Retry Logic
```python
async def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # Exponential backoff
            await asyncio.sleep(wait_time)
```

## Performance Optimizations

### 1. Connection Pooling
```python
class DatabaseManager:
    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            min_size=10,
            max_size=20,
            command_timeout=60
        )
```

### 2. Caching Strategy
```python
class CachedScraper:
    def __init__(self, cache_ttl=3600):
        self.cache = {}
        self.cache_ttl = cache_ttl
    
    async def get_or_fetch(self, key, fetch_func):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return data
        
        data = await fetch_func()
        self.cache[key] = (data, time.time())
        return data
```

### 3. Batch Processing
```python
async def process_in_batches(items, batch_size=10, process_func):
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[process_func(item) for item in batch]
        )
        results.extend(batch_results)
    return results
```

## Security Patterns

### 1. API Key Management
- All keys in environment variables
- Never logged or exposed in errors
- Validation on startup

### 2. Data Privacy
- No PII collection beyond public LinkedIn data
- Local database only (no cloud storage)
- Scraping respects robots.txt

### 3. Rate Limiting Compliance
- Configurable delays between requests
- Respectful scraping patterns
- API quota monitoring

## Testing Patterns

### 1. Unit Testing
```python
class TestAIWashingDetector:
    async def test_blog_analysis(self):
        detector = AIWashingDetector()
        score = await detector.analyze_blog_content(
            "We use transformer models for..."
        )
        assert score > 7  # High technical content
```

### 2. Integration Testing
```python
async def test_full_discovery_pipeline():
    engine = DiscoveryEngine(test_config)
    results = await engine.run_discovery()
    assert len(results.companies) > 0
    assert all(c.ai_washing_score is not None for c in results.companies)
```

### 3. Mock Data Patterns
```python
class MockLinkedInScraper:
    async def scrape_jobs(self, query):
        return [
            {"title": "ML Engineer", "company": "Test Corp"},
            # ... mock data
        ]
```

## Future Architecture Considerations

### 1. Microservices Migration
- Each scraper as independent service
- Message queue for coordination
- Separate analysis service

### 2. Machine Learning Integration
- Train models on successful matches
- Predict response likelihood
- Optimize outreach timing

### 3. Real-time Processing
- WebSocket connections for alerts
- Stream processing for news
- Instant notification system

This architecture provides a solid foundation for the current system while allowing for future enhancements and scaling as needed.
