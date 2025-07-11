"""
Configuration file for Startup Intelligence System
"""
import os
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class APIConfig:
    """API configuration settings"""
    # Y Combinator (if available)
    yc_api_key: str = os.getenv('YC_API_KEY', '')
    
    # Crunchbase API
    crunchbase_api_key: str = os.getenv('CRUNCHBASE_API_KEY', '')
    
    # LinkedIn (requires careful usage)
    linkedin_email: str = os.getenv('LINKEDIN_EMAIL', '')
    linkedin_password: str = os.getenv('LINKEDIN_PASSWORD', '')
    
    # GitHub API
    github_token: str = os.getenv('GITHUB_TOKEN', '')
    
    # HuggingFace API
    huggingface_token: str = os.getenv('HUGGINGFACE_TOKEN', '')
    
    # SendGrid for outreach tracking
    sendgrid_api_key: str = os.getenv('SENDGRID_API_KEY', '')

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    name: str = os.getenv('DB_NAME', 'startup_intelligence')
    user: str = os.getenv('DB_USER', 'postgres')
    password: str = os.getenv('DB_PASSWORD', '')

@dataclass
class ScrapingConfig:
    """Web scraping configuration"""
    # Rate limiting
    request_delay: float = 2.0  # seconds between requests
    max_retries: int = 3
    timeout: int = 30
    
    # User agent rotation
    user_agents: List[str] = None
    
    def __post_init__(self):
        if self.user_agents is None:
            self.user_agents = [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            ]

@dataclass
class TargetCriteria:
    """Target company criteria for Rob Ford's search"""
    # Geographic focus
    target_locations: List[str] = None
    
    # Company stage and size
    funding_stages: List[str] = None
    min_employees: int = 10
    max_employees: int = 200
    
    # Industry focus
    target_industries: List[str] = None
    healthcare_focused: bool = True
    
    # AI authenticity requirements
    min_ai_washing_score: int = 6  # out of 10
    require_ml_engineers: bool = True
    min_ml_engineer_ratio: float = 0.15  # 15% of engineering team
    
    # Technical requirements
    require_engineering_blog: bool = True
    require_github_presence: bool = True
    min_github_ml_contributions: int = 5
    
    def __post_init__(self):
        if self.target_locations is None:
            self.target_locations = ['Seattle', 'Bellevue', 'Redmond', 'Kirkland']
        
        if self.funding_stages is None:
            self.funding_stages = ['Series A', 'Series B', 'Early Stage VC']
        
        if self.target_industries is None:
            self.target_industries = [
                'Healthcare', 'Health Tech', 'Medical Devices',
                'E-commerce', 'Enterprise Software', 'SaaS',
                'Real-time Communications', 'Video Conferencing',
                'AI/ML Infrastructure', 'Data Analytics'
            ]

class Config:
    """Main configuration class"""
    def __init__(self):
        self.api = APIConfig()
        self.database = DatabaseConfig()
        self.scraping = ScrapingConfig()
        self.targets = TargetCriteria()
    
    @classmethod
    def load_from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        return cls()
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check required API keys
        if not self.api.github_token:
            issues.append("GitHub token required for API access")
        
        # Check database connection info
        if not self.database.password and self.database.host != 'localhost':
            issues.append("Database password required for remote connections")
        
        return issues

# Data source configurations
DATA_SOURCES = {
    'yc_companies': {
        'name': 'Y Combinator Companies',
        'url_template': 'https://api.ycombinator.com/companies',
        'rate_limit': 100,  # requests per hour
        'priority': 1
    },
    'geekwire_rss': {
        'name': 'GeekWire Startup News',
        'url': 'https://www.geekwire.com/feed/',
        'rate_limit': 60,
        'priority': 2
    },
    'crunchbase': {
        'name': 'Crunchbase Company Data',
        'url_template': 'https://api.crunchbase.com/api/v4/entities/organizations',
        'rate_limit': 1000,  # requests per day
        'priority': 3
    },
    'linkedin_jobs': {
        'name': 'LinkedIn Job Postings',
        'search_terms': ['Machine Learning Engineer Seattle', 'Data Scientist Seattle', 'AI Engineer Seattle'],
        'rate_limit': 100,
        'priority': 4
    },
    'github_orgs': {
        'name': 'GitHub Organizations',
        'url_template': 'https://api.github.com/orgs/{org}',
        'rate_limit': 5000,  # requests per hour
        'priority': 5
    }
}

# AI-washing detection configuration
AI_DETECTION_CONFIG = {
    'blog_keywords': {
        'positive': [
            'model training', 'neural network', 'machine learning pipeline',
            'feature engineering', 'hyperparameter tuning', 'model evaluation',
            'data preprocessing', 'algorithm optimization', 'inference latency',
            'model deployment', 'MLOps', 'model monitoring', 'A/B testing',
            'gradient descent', 'backpropagation', 'transformer architecture'
        ],
        'negative': [
            'ChatGPT integration', 'OpenAI API', 'prompt engineering only',
            'AI-powered' without specifics, 'machine learning magic',
            'artificial intelligence revolution', 'AI transformation'
        ]
    },
    'job_title_weights': {
        'Machine Learning Engineer': 3,
        'ML Engineer': 3,
        'Data Scientist': 2,
        'AI Engineer': 2.5,
        'Research Scientist': 3,
        'MLOps Engineer': 2.5,
        'AI Product Manager': 1.5,
        'Software Engineer': 0.5
    },
    'github_ml_indicators': [
        'pytorch', 'tensorflow', 'scikit-learn', 'numpy', 'pandas',
        'jupyter', 'keras', 'xgboost', 'lightgbm', 'transformers',
        'mlflow', 'kubeflow', 'airflow', 'docker', 'kubernetes'
    ]
}
