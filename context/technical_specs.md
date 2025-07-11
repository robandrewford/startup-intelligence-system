# Technical Specifications - Startup Intelligence System

## Architecture Overview
Automated intelligence gathering system with strategic analysis focus.

## Phase 1: Discovery Engine (Current Priority)
**Goal**: Automated startup discovery from multiple sources

### Data Sources
1. **Y Combinator API**: W22, S22, W23 batches, Seattle filter
2. **GeekWire RSS**: Funding announcements, startup news
3. **LinkedIn Jobs API**: ML Engineer positions in Seattle
4. **GitHub API**: Seattle tech repositories and contributors
5. **Crunchbase API**: Funding data and company profiles
6. **HuggingFace API**: Model releases and download metrics

### Core Functions
```python
def daily_discovery_run():
    # Automated discovery from all sources
    # Deduplication and initial filtering
    # Database storage with metadata
    
def ai_washing_score(company_url):
    # Technical depth analysis
    # Engineering blog assessment
    # GitHub contribution analysis
    # Job posting ML engineer ratio
    
def generate_company_profile(company_name, company_url):
    # Complete intelligence gathering
    # SWOT analysis generation
    # Strategic fit scoring
```

## AI-Washing Detection Criteria
**Real AI Signals (Nate's Framework):**
- Engineering blog posts about actual ML challenges
- ML/AI engineers >20% of engineering team
- Open-source contributions to ML tools
- Published papers or meaningful model benchmarks
- Infrastructure costs >30% of revenue
- Specific, measurable AI performance metrics

**Red Flags:**
- Only ChatGPT/OpenAI integration mentions
- Vague "AI-powered" marketing claims
- No ML engineers on LinkedIn
- Recent pivot to AI without technical foundation

## Technology Stack
- **Language**: Python 3.9+
- **Web Scraping**: Scrapy, BeautifulSoup, Selenium
- **APIs**: requests, official API clients
- **Database**: PostgreSQL for structured data
- **Analysis**: pandas, numpy, nltk for content analysis
- **Automation**: GitHub Actions for scheduled runs
- **Dashboard**: Streamlit for data visualization
- **Email**: SendGrid API for outreach tracking

## Data Pipeline
1. **Raw Data Collection**: Multi-source automated scraping
2. **Data Cleaning**: Deduplication, validation, enrichment
3. **AI-Washing Analysis**: Automated scoring algorithms
4. **Company Profiling**: Intelligence report generation
5. **Strategic Scoring**: Fit analysis based on user criteria
6. **Output Generation**: Reports, dashboards, outreach recommendations

## Security & Privacy
- **API Keys**: Environment variables, never committed
- **Data Storage**: Local PostgreSQL, no cloud storage of scraped data
- **Rate Limiting**: Respectful API usage, robots.txt compliance
- **Personal Data**: Minimal collection, LinkedIn public data only

## Performance Requirements
- **Discovery Runtime**: <30 minutes for complete daily run
- **Database Size**: Support for 10,000+ company records
- **API Limits**: Stay within free tier limits where possible
- **Update Frequency**: Daily automated runs, weekly deep analysis

## Monitoring & Alerts
- **Data Quality**: Missing fields, duplicate detection
- **API Health**: Rate limit monitoring, error tracking
- **Discovery Performance**: New companies found per run
- **Analysis Quality**: AI-washing score accuracy validation
