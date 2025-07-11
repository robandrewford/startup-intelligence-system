# Startup Intelligence System

Automated startup discovery and analysis system designed for strategic job searching in the Seattle AI/ML ecosystem.

## Project Overview

This system automates the discovery and analysis of startup companies, focusing on:
- **AI-washing detection**: Separating real AI companies from ChatGPT integration plays
- **Healthcare focus**: Targeting companies solving expensive healthcare problems
- **Strategic analysis**: 80% strategic analysis, 20% data crunching
- **Seattle ecosystem**: Geographic focus on Pacific Northwest startups

## Key Features

### Phase 1: Discovery Engine ✅
- Y Combinator company discovery (W22, S22, W23 batches)
- GeekWire startup news scraping
- LinkedIn job posting analysis
- Automated deduplication and data enrichment

### Phase 2: AI-Washing Detection ✅
- Engineering blog technical depth analysis
- GitHub ML contribution assessment
- Job posting ML engineer ratio calculation
- Marketing content authenticity scoring

### Phase 3: Intelligence Gathering 🚧
- Crunchbase funding data integration
- Competitive landscape analysis
- Strategic fit scoring
- Healthcare relevance assessment

### Phase 4: Strategic Analysis Tools 📋
- Pattern recognition dashboard
- Market opportunity identification
- Investment stage optimization
- Cultural fit assessment

### Phase 5: Outreach Automation 📋
- Intelligent email generation
- News-based outreach hooks
- Follow-up automation
- Response tracking

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- GitHub API token (recommended)
- Optional: Crunchbase API, LinkedIn credentials

### Installation

1. **Clone and setup environment:**
```bash
cd /Users/robertford/Repos/startup-intelligence-system
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Setup environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys and database credentials
```

3. **Initialize database:**
```bash
python -m src.data.database
```

4. **Run discovery engine:**
```bash
python -m src.discovery.discovery_engine
```

### Environment Variables

Create a `.env` file with:
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=startup_intelligence
DB_USER=your_user
DB_PASSWORD=your_password

# API Keys (optional but recommended)
GITHUB_TOKEN=your_github_token
CRUNCHBASE_API_KEY=your_crunchbase_key
LINKEDIN_EMAIL=your_email
LINKEDIN_PASSWORD=your_password
SENDGRID_API_KEY=your_sendgrid_key
HUGGINGFACE_TOKEN=your_hf_token
```

## Usage Examples

### Daily Discovery Run
```python
from src.discovery.discovery_engine import StartupDiscoveryEngine
from config.settings import Config

config = Config.load_from_env()
engine = StartupDiscoveryEngine(config)
report = await engine.run_daily_discovery()
```

### AI-Washing Analysis
```python
from src.analysis.ai_washing_detector import AIWashingDetector

detector = AIWashingDetector(config)
score = await detector.calculate_ai_washing_score(company_data)
# Score: 1-10 (higher = more authentic AI)
```

### Database Queries
```python
from src.data.database import DatabaseManager

db = DatabaseManager(config.database)
await db.initialize()

# Get top healthcare AI companies
companies = await db.get_companies_by_criteria(
    min_ai_score=7,
    healthcare_only=True,
    location_filter="Seattle"
)
```

## AI-Washing Detection Criteria

Based on Nate's framework for identifying authentic AI companies:

### ✅ Real AI Signals
- Engineering blog posts about ML challenges (not ChatGPT integration)
- ML/AI engineers >20% of engineering team
- Open-source contributions to ML tools
- Published papers or meaningful model benchmarks
- Infrastructure costs >30% of revenue
- Specific AI performance metrics (accuracy, latency, etc.)

### ❌ AI-Washing Red Flags
- Only mentions ChatGPT/OpenAI integration
- Vague "AI-powered" claims without specifics
- No ML engineers on team
- Recent pivot to AI without technical foundation
- Marketing-heavy content with no technical depth

## Target Company Profile

### Ideal Characteristics
- **Stage**: Series A-B (post-PMF, pre-scale)
- **Size**: 50-200 employees (equity still meaningful)
- **Location**: Seattle metro area
- **Focus**: Healthcare AI, B2B SaaS, real-time communications
- **Technology**: Custom ML models, not just API integrations
- **Market**: Clear revenue model with enterprise customers

### Strategic Priorities
1. **Healthcare relevance**: Companies solving expensive healthcare problems
2. **Technical authenticity**: Real AI/ML capabilities
3. **Growth stage**: Established but still scaling
4. **Geographic fit**: Seattle ecosystem for networking
5. **Leadership opportunity**: Senior roles with meaningful impact

## Project Structure

```
startup-intelligence-system/
├── src/
│   ├── discovery/          # Data source scrapers
│   │   ├── discovery_engine.py
│   │   ├── yc_scraper.py
│   │   ├── geekwire_scraper.py
│   │   ├── linkedin_scraper.py
│   │   └── github_analyzer.py
│   ├── analysis/           # AI-washing detection
│   │   └── ai_washing_detector.py
│   ├── data/              # Database operations
│   │   └── database.py
│   └── outreach/          # Email automation (future)
├── config/
│   └── settings.py        # Configuration management
├── context/               # Cline MCP context files
│   ├── project_overview.md
│   ├── technical_specs.md
│   ├── conversation_summary.md
│   └── implementation_roadmap.md
├── data/                  # Data storage
│   ├── raw/              # Raw scraped data
│   ├── processed/        # Cleaned data
│   └── outputs/          # Reports and analysis
├── docs/                 # Documentation
└── requirements.txt
```

## Development Roadmap

### Week 1: Discovery Engine ✅
- [x] Y Combinator scraper
- [x] GeekWire news parser
- [x] Basic AI-washing detection
- [x] Database schema and operations
- [x] Daily automation framework

### Week 2: Analysis Enhancement
- [ ] LinkedIn job posting analysis
- [ ] GitHub organization deep-dive
- [ ] Crunchbase API integration
- [ ] Enhanced AI-washing algorithms
- [ ] Strategic fit scoring refinement

### Week 3: Intelligence Gathering
- [ ] Competitive landscape analysis
- [ ] News monitoring and alerts
- [ ] Company relationship mapping
- [ ] Market timing assessment
- [ ] Healthcare relevance scoring

### Week 4: Strategic Tools
- [ ] Analysis dashboard (Streamlit)
- [ ] Pattern recognition algorithms
- [ ] Opportunity gap identification
- [ ] Performance analytics
- [ ] Target prioritization system

### Week 5+: Outreach Automation
- [ ] Email template generation
- [ ] Personalization algorithms
- [ ] Follow-up scheduling
- [ ] Response tracking
- [ ] A/B testing framework

## Performance Metrics

### Discovery Efficiency
- **Target**: 20+ qualified companies discovered per week
- **Current**: Baseline measurement in progress
- **Quality**: >80% Seattle-area, >60% AI-authentic

### Analysis Depth
- **Target**: 5+ deep strategic analyses per week
- **Focus**: High-potential healthcare AI companies
- **Output**: Comprehensive intelligence reports

### Outreach Effectiveness
- **Target**: 3+ personalized applications per week
- **Quality**: News-based hooks, strategic positioning
- **Tracking**: Response rates, interview conversion

## Contributing

This is a personal project for Rob Ford's job search. For questions or suggestions:
- Email: rob@defact.io
- LinkedIn: /in/robandrewford
- Website: robandrewford.com

## License

Private project - not for public distribution.

## Acknowledgments

- **Nate's AI-washing framework**: Core detection methodology
- **Seattle startup ecosystem**: GeekWire, Madrona, Pioneer Square Labs
- **Y Combinator**: Company discovery methodology
- **Cline MCP**: Project context management
