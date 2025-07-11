"""
LinkedIn Job Posting Scraper
Discovers companies from ML engineer job postings
Note: Use carefully to respect LinkedIn's terms of service
"""
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup
import time

from config.settings import Config

logger = logging.getLogger(__name__)

class LinkedInScraper:
    """Scraper for LinkedIn job postings to discover ML-hiring companies"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = None
        self.search_terms = [
            'Machine Learning Engineer Seattle',
            'Data Scientist Seattle', 
            'AI Engineer Seattle',
            'ML Engineer Seattle',
            'Deep Learning Engineer Seattle'
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.scraping.timeout),
            headers={
                'User-Agent': self.config.scraping.user_agents[0],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_companies_hiring_ml(self) -> List[Dict[str, Any]]:
        """Get companies hiring ML engineers in Seattle"""
        all_companies = []
        
        async with self:
            for search_term in self.search_terms:
                try:
                    logger.info(f"Searching LinkedIn jobs: {search_term}")
                    companies = await self._search_jobs(search_term)
                    all_companies.extend(companies)
                    
                    # Respectful rate limiting - LinkedIn is strict
                    await asyncio.sleep(self.config.scraping.request_delay * 2)
                    
                except Exception as e:
                    logger.error(f"LinkedIn search failed for '{search_term}': {str(e)}")
        
        # Deduplicate companies
        unique_companies = self._deduplicate_companies(all_companies)
        logger.info(f"Found {len(unique_companies)} unique companies hiring ML talent")
        
        return unique_companies
    
    async def _search_jobs(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for jobs using public LinkedIn job search"""
        companies = []
        
        # Use LinkedIn's public job search (no authentication required)
        search_url = "https://www.linkedin.com/jobs/search"
        params = {
            'keywords': search_term,
            'location': 'Seattle, Washington, United States',
            'f_TPR': 'r604800',  # Past week
            'f_JT': 'F',  # Full-time
            'position': 1,
            'pageNum': 0
        }
        
        try:
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    html = await response.text()
                    companies = self._parse_job_results(html)
                elif response.status == 429:
                    logger.warning("Rate limited by LinkedIn")
                    await asyncio.sleep(60)  # Wait 1 minute
                else:
                    logger.error(f"LinkedIn search returned status {response.status}")
        
        except Exception as e:
            logger.error(f"LinkedIn request failed: {str(e)}")
        
        return companies
    
    def _parse_job_results(self, html: str) -> List[Dict[str, Any]]:
        """Parse job search results HTML"""
        companies = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find job cards
        job_cards = soup.find_all('div', class_=re.compile(r'job-search-card|base-search-card'))
        
        for card in job_cards:
            try:
                company_data = self._extract_company_from_job_card(card)
                if company_data:
                    companies.append(company_data)
            except Exception as e:
                logger.error(f"Failed to parse job card: {str(e)}")
        
        # Fallback: look for company mentions in text
        if not companies:
            companies = self._extract_companies_from_text(html)
        
        return companies
    
    def _extract_company_from_job_card(self, card) -> Optional[Dict[str, Any]]:
        """Extract company information from job card"""
        try:
            # Company name
            company_elem = card.find('h4', class_=re.compile(r'company-name|base-search-card__subtitle'))
            if not company_elem:
                company_elem = card.find('a', href=re.compile(r'/company/'))
            
            if not company_elem:
                return None
            
            company_name = company_elem.get_text(strip=True)
            if not company_name or len(company_name) < 2:
                return None
            
            # Job title
            title_elem = card.find('h3', class_=re.compile(r'job-title|base-search-card__title'))
            job_title = title_elem.get_text(strip=True) if title_elem else 'Unknown Position'
            
            # Location
            location_elem = card.find('span', class_=re.compile(r'job-location|base-search-card__metadata'))
            location = location_elem.get_text(strip=True) if location_elem else 'Seattle, WA'
            
            # Company link
            company_link = None
            link_elem = card.find('a', href=re.compile(r'/company/'))
            if link_elem:
                href = link_elem.get('href')
                if href and '/company/' in href:
                    company_slug = href.split('/company/')[-1].split('/')[0]
                    company_link = f"https://www.linkedin.com/company/{company_slug}"
            
            return {
                'name': company_name,
                'description': f'Hiring for: {job_title}',
                'location': location,
                'source': 'linkedin_jobs',
                'linkedin_company_url': company_link,
                'hiring_for_ml': True,
                'ml_job_titles': [job_title],
                'discovered_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to extract company from job card: {str(e)}")
            return None
    
    def _extract_companies_from_text(self, html: str) -> List[Dict[str, Any]]:
        """Fallback: extract company names from raw HTML text"""
        companies = []
        
        # Common patterns for company names in job listings
        company_patterns = [
            r'at\s+([A-Z][a-zA-Z0-9\s&.]+?)(?:\s+is\s+|·|,|\n)',
            r'Company:\s*([A-Z][a-zA-Z0-9\s&.]+?)(?:\n|<)',
            r'([A-Z][a-zA-Z0-9\s&.]+?)\s+is\s+hiring',
            r'([A-Z][a-zA-Z0-9\s&.]+?)\s+jobs',
        ]
        
        found_companies = set()
        
        for pattern in company_patterns:
            matches = re.findall(pattern, html, re.MULTILINE)
            for match in matches:
                company_name = match.strip()
                
                # Filter out common false positives
                if (len(company_name) > 2 and 
                    len(company_name) < 50 and
                    company_name not in ['Seattle', 'Washington', 'United States', 'LinkedIn'] and
                    not company_name.endswith('...') and
                    company_name not in found_companies):
                    
                    found_companies.add(company_name)
                    companies.append({
                        'name': company_name,
                        'description': 'Discovered from LinkedIn job posting',
                        'location': 'Seattle, WA',
                        'source': 'linkedin_jobs_text',
                        'hiring_for_ml': True,
                        'discovered_date': datetime.now().isoformat()
                    })
        
        return companies
    
    def _deduplicate_companies(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate companies and merge data"""
        seen_companies = {}
        
        for company in companies:
            company_name = company['name'].lower().strip()
            
            if company_name in seen_companies:
                # Merge ML job titles
                existing = seen_companies[company_name]
                if 'ml_job_titles' in company:
                    existing_titles = existing.get('ml_job_titles', [])
                    new_titles = company['ml_job_titles']
                    existing['ml_job_titles'] = list(set(existing_titles + new_titles))
            else:
                seen_companies[company_name] = company
        
        return list(seen_companies.values())

# Alternative approach: Use public job boards that aggregate LinkedIn data
class JobBoardAggregator:
    """Alternative scraper using public job aggregation sites"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = None
        
        # Job board sources that often include LinkedIn data
        self.job_boards = [
            {
                'name': 'Indeed',
                'search_url': 'https://www.indeed.com/jobs',
                'params': {
                    'q': 'Machine Learning Engineer',
                    'l': 'Seattle, WA',
                    'fromage': '7',  # Last 7 days
                    'sort': 'date'
                }
            },
            {
                'name': 'Glassdoor',
                'search_url': 'https://www.glassdoor.com/Job/jobs.htm',
                'params': {
                    'sc.keyword': 'ML Engineer',
                    'locT': 'C',
                    'locId': '1150505',  # Seattle
                    'fromAge': '7'
                }
            }
        ]
    
    async def search_job_boards(self) -> List[Dict[str, Any]]:
        """Search multiple job boards for ML positions"""
        all_companies = []
        
        for board in self.job_boards:
            try:
                logger.info(f"Searching {board['name']} for ML jobs...")
                companies = await self._search_job_board(board)
                all_companies.extend(companies)
                
                # Rate limiting
                await asyncio.sleep(self.config.scraping.request_delay)
                
            except Exception as e:
                logger.error(f"Failed to search {board['name']}: {str(e)}")
        
        return all_companies
    
    async def _search_job_board(self, board: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search individual job board"""
        # Placeholder implementation
        # In reality, each job board would need custom parsing logic
        return []

# Mock data for testing when LinkedIn is not accessible
MOCK_LINKEDIN_COMPANIES = [
    {
        'name': 'Convoy',
        'description': 'Hiring for: Senior Machine Learning Engineer',
        'location': 'Seattle, WA',
        'source': 'linkedin_jobs_mock',
        'hiring_for_ml': True,
        'ml_job_titles': ['Senior Machine Learning Engineer'],
        'discovered_date': datetime.now().isoformat()
    },
    {
        'name': 'Redfin',
        'description': 'Hiring for: Data Scientist - Machine Learning',
        'location': 'Seattle, WA', 
        'source': 'linkedin_jobs_mock',
        'hiring_for_ml': True,
        'ml_job_titles': ['Data Scientist - Machine Learning'],
        'discovered_date': datetime.now().isoformat()
    },
    {
        'name': 'Zillow',
        'description': 'Hiring for: AI/ML Engineer',
        'location': 'Seattle, WA',
        'source': 'linkedin_jobs_mock',
        'hiring_for_ml': True,
        'ml_job_titles': ['AI/ML Engineer'],
        'discovered_date': datetime.now().isoformat()
    }
]

async def test_linkedin_scraper():
    """Test function for LinkedIn scraper"""
    from config.settings import Config
    
    config = Config()
    scraper = LinkedInScraper(config)
    
    # Use mock data for testing
    logger.info("Using mock LinkedIn data for testing...")
    companies = MOCK_LINKEDIN_COMPANIES
    
    print(f"Found {len(companies)} companies hiring ML talent:")
    for company in companies:
        print(f"  - {company['name']}: {company['description']}")
        if company.get('ml_job_titles'):
            print(f"    ML roles: {', '.join(company['ml_job_titles'])}")

if __name__ == "__main__":
    asyncio.run(test_linkedin_scraper())
