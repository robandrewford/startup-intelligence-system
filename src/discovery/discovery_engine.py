"""
Phase 1 Discovery Engine - Main automation module
Automated startup discovery from multiple sources with AI-washing detection
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from src.discovery.yc_scraper import YCombinatorScraper
from src.discovery.geekwire_scraper import GeekWireScraper
from src.discovery.linkedin_scraper import LinkedInScraper
from src.discovery.github_analyzer import GitHubAnalyzer
from src.analysis.ai_washing_detector import AIWashingDetector
from src.data.database import DatabaseManager
from config.settings import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StartupDiscoveryEngine:
    """Main discovery engine orchestrating all data sources"""
    
    def __init__(self, config: Config):
        self.config = config
        self.db = DatabaseManager(config.database)
        
        # Initialize scrapers
        self.yc_scraper = YCombinatorScraper(config)
        self.geekwire_scraper = GeekWireScraper(config)
        self.linkedin_scraper = LinkedInScraper(config)
        self.github_analyzer = GitHubAnalyzer(config)
        
        # Initialize analyzers
        self.ai_detector = AIWashingDetector(config)
        
        # Discovery statistics
        self.stats = {
            'companies_discovered': 0,
            'companies_analyzed': 0,
            'high_potential_targets': 0,
            'ai_washing_filtered': 0,
            'run_start_time': None,
            'run_end_time': None
        }
    
    async def run_daily_discovery(self) -> Dict[str, Any]:
        """Main daily discovery run"""
        logger.info("Starting daily startup discovery run")
        self.stats['run_start_time'] = datetime.now()
        
        try:
            # Phase 1: Discover companies from all sources
            companies = await self._discover_companies()
            
            # Phase 2: Deduplicate and enrich data
            unique_companies = await self._deduplicate_companies(companies)
            
            # Phase 3: AI-washing analysis
            analyzed_companies = await self._analyze_companies(unique_companies)
            
            # Phase 4: Store results and generate report
            await self._store_results(analyzed_companies)
            report = await self._generate_discovery_report()
            
            self.stats['run_end_time'] = datetime.now()
            logger.info(f"Discovery run completed. Found {len(analyzed_companies)} companies")
            
            return report
            
        except Exception as e:
            logger.error(f"Discovery run failed: {str(e)}")
            raise
    
    async def _discover_companies(self) -> List[Dict[str, Any]]:
        """Discover companies from all configured sources"""
        all_companies = []
        
        # Y Combinator companies
        try:
            logger.info("Discovering YC companies...")
            yc_companies = await self.yc_scraper.get_seattle_companies()
            all_companies.extend(yc_companies)
            logger.info(f"Found {len(yc_companies)} YC companies")
        except Exception as e:
            logger.error(f"YC scraping failed: {str(e)}")
        
        # GeekWire startup news
        try:
            logger.info("Discovering companies from GeekWire...")
            gw_companies = await self.geekwire_scraper.get_recent_startups()
            all_companies.extend(gw_companies)
            logger.info(f"Found {len(gw_companies)} companies from GeekWire")
        except Exception as e:
            logger.error(f"GeekWire scraping failed: {str(e)}")
        
        # LinkedIn job postings
        try:
            logger.info("Discovering companies from LinkedIn jobs...")
            li_companies = await self.linkedin_scraper.get_companies_hiring_ml()
            all_companies.extend(li_companies)
            logger.info(f"Found {len(li_companies)} companies from LinkedIn")
        except Exception as e:
            logger.error(f"LinkedIn scraping failed: {str(e)}")
        
        self.stats['companies_discovered'] = len(all_companies)
        return all_companies
    
    async def _deduplicate_companies(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates and merge data from multiple sources"""
        logger.info("Deduplicating and merging company data...")
        
        # Simple deduplication by domain name
        seen_domains = set()
        unique_companies = []
        
        for company in companies:
            domain = self._extract_domain(company.get('website', ''))
            company_name = company.get('name', '').lower().strip()
            
            # Create a unique key
            unique_key = domain if domain else company_name
            
            if unique_key and unique_key not in seen_domains:
                seen_domains.add(unique_key)
                unique_companies.append(company)
        
        logger.info(f"Deduplicated to {len(unique_companies)} unique companies")
        return unique_companies
    
    async def _analyze_companies(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze companies for AI authenticity and strategic fit"""
        logger.info("Analyzing companies for AI authenticity...")
        
        analyzed_companies = []
        
        for company in companies:
            try:
                # AI-washing detection
                ai_score = await self.ai_detector.calculate_ai_washing_score(company)
                company['ai_washing_score'] = ai_score
                
                # GitHub analysis
                github_data = await self.github_analyzer.analyze_company_github(company)
                company['github_analysis'] = github_data
                
                # Strategic fit scoring
                fit_score = self._calculate_strategic_fit(company)
                company['strategic_fit_score'] = fit_score
                
                # Healthcare relevance
                company['healthcare_relevance'] = self._assess_healthcare_relevance(company)
                
                analyzed_companies.append(company)
                self.stats['companies_analyzed'] += 1
                
                # Track high-potential targets
                if ai_score >= self.config.targets.min_ai_washing_score and fit_score >= 7:
                    self.stats['high_potential_targets'] += 1
                
                # Track AI-washing filtered out
                if ai_score < self.config.targets.min_ai_washing_score:
                    self.stats['ai_washing_filtered'] += 1
                    
            except Exception as e:
                logger.error(f"Analysis failed for {company.get('name', 'unknown')}: {str(e)}")
                # Still include company with partial data
                company['ai_washing_score'] = 0
                company['analysis_error'] = str(e)
                analyzed_companies.append(company)
        
        return analyzed_companies
    
    def _calculate_strategic_fit(self, company: Dict[str, Any]) -> int:
        """Calculate strategic fit score (1-10) based on Rob's criteria"""
        score = 0
        
        # Location fit (Seattle area)
        location = company.get('location', '').lower()
        if any(city.lower() in location for city in self.config.targets.target_locations):
            score += 2
        
        # Funding stage fit
        funding_stage = company.get('funding_stage', '')
        if funding_stage in self.config.targets.funding_stages:
            score += 2
        
        # Company size fit
        employees = company.get('employees_count', 0)
        if self.config.targets.min_employees <= employees <= self.config.targets.max_employees:
            score += 2
        
        # Industry relevance
        description = company.get('description', '').lower()
        if any(industry.lower() in description for industry in self.config.targets.target_industries):
            score += 2
        
        # Technical depth indicators
        ai_score = company.get('ai_washing_score', 0)
        if ai_score >= 7:
            score += 2
        elif ai_score >= 5:
            score += 1
        
        return min(score, 10)
    
    def _assess_healthcare_relevance(self, company: Dict[str, Any]) -> bool:
        """Assess if company is healthcare-focused"""
        text_fields = [
            company.get('description', ''),
            company.get('name', ''),
            ' '.join(company.get('keywords', []))
        ]
        
        combined_text = ' '.join(text_fields).lower()
        
        healthcare_keywords = [
            'health', 'medical', 'healthcare', 'clinical', 'patient',
            'hospital', 'diagnosis', 'treatment', 'pharma', 'biotech',
            'therapeutic', 'drug', 'medicine', 'doctor', 'physician'
        ]
        
        return any(keyword in combined_text for keyword in healthcare_keywords)
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ''
        
        # Remove protocol
        if '://' in url:
            url = url.split('://', 1)[1]
        
        # Remove path
        if '/' in url:
            url = url.split('/', 1)[0]
        
        # Remove www
        if url.startswith('www.'):
            url = url[4:]
        
        return url.lower()
    
    async def _store_results(self, companies: List[Dict[str, Any]]) -> None:
        """Store analysis results in database"""
        logger.info("Storing results in database...")
        
        for company in companies:
            await self.db.upsert_company(company)
        
        logger.info(f"Stored {len(companies)} companies in database")
    
    async def _generate_discovery_report(self) -> Dict[str, Any]:
        """Generate daily discovery report"""
        runtime = (self.stats['run_end_time'] - self.stats['run_start_time']).total_seconds()
        
        # Get top targets from database
        top_targets = await self.db.get_top_companies(limit=10)
        
        report = {
            'date': datetime.now().isoformat(),
            'runtime_seconds': runtime,
            'statistics': self.stats,
            'top_targets': top_targets,
            'recommendations': self._generate_recommendations(top_targets)
        }
        
        return report
    
    def _generate_recommendations(self, top_targets: List[Dict[str, Any]]) -> List[str]:
        """Generate strategic recommendations based on discovery results"""
        recommendations = []
        
        if self.stats['high_potential_targets'] > 0:
            recommendations.append(
                f"Found {self.stats['high_potential_targets']} high-potential targets. "
                "Focus deep analysis on these companies."
            )
        
        if self.stats['ai_washing_filtered'] > self.stats['high_potential_targets']:
            recommendations.append(
                "High ratio of AI-washing companies detected. "
                "Current filters are working effectively."
            )
        
        healthcare_targets = [t for t in top_targets if t.get('healthcare_relevance', False)]
        if healthcare_targets:
            recommendations.append(
                f"Found {len(healthcare_targets)} healthcare-relevant targets. "
                "Leverage FDA experience in outreach."
            )
        
        return recommendations

# Main execution function
async def main():
    """Main execution function for daily discovery"""
    config = Config.load_from_env()
    
    # Validate configuration
    issues = config.validate()
    if issues:
        logger.error("Configuration issues found:")
        for issue in issues:
            logger.error(f"  - {issue}")
        return
    
    # Run discovery
    engine = StartupDiscoveryEngine(config)
    report = await engine.run_daily_discovery()
    
    # Output report
    print("\n" + "="*50)
    print("DAILY DISCOVERY REPORT")
    print("="*50)
    print(json.dumps(report, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
