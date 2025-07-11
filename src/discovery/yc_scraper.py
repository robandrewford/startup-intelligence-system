"""
Y Combinator Company Scraper
Discovers companies from YC batches W22, S22, W23 with Seattle focus
"""
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from config.settings import Config

logger = logging.getLogger(__name__)

class YCombinatorScraper:
    """Scraper for Y Combinator company data"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = "https://www.ycombinator.com"
        self.session = None
        
        # Target batches based on Nate's recommendation (18-24 months post-YC)
        self.target_batches = ['W22', 'S22', 'W23']
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.scraping.timeout),
            headers={'User-Agent': self.config.scraping.user_agents[0]}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_seattle_companies(self) -> List[Dict[str, Any]]:
        """Get all Seattle-area companies from target YC batches"""
        all_companies = []
        
        async with self:
            for batch in self.target_batches:
                try:
                    logger.info(f"Scraping YC batch {batch}")
                    batch_companies = await self._scrape_batch(batch)
                    seattle_companies = self._filter_seattle_companies(batch_companies)
                    
                    logger.info(f"Found {len(seattle_companies)} Seattle companies in {batch}")
                    all_companies.extend(seattle_companies)
                    
                    # Rate limiting
                    await asyncio.sleep(self.config.scraping.request_delay)
                    
                except Exception as e:
                    logger.error(f"Failed to scrape batch {batch}: {str(e)}")
        
        return all_companies
    
    async def _scrape_batch(self, batch: str) -> List[Dict[str, Any]]:
        """Scrape a specific YC batch"""
        # YC companies are listed at /companies with batch filter
        url = f"{self.base_url}/companies"
        params = {'batch': batch}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_companies_html(html, batch)
                else:
                    logger.error(f"HTTP {response.status} for batch {batch}")
                    return []
        except Exception as e:
            logger.error(f"Request failed for batch {batch}: {str(e)}")
            return []
    
    def _parse_companies_html(self, html: str, batch: str) -> List[Dict[str, Any]]:
        """Parse YC companies from HTML"""
        companies = []
        
        # YC company pages have a specific structure
        # This is a simplified parser - in reality, you'd need more robust parsing
        # or use the YC API if available
        
        # Look for company data patterns in HTML
        company_pattern = r'<div[^>]*class="[^"]*company[^"]*"[^>]*>(.*?)</div>'
        matches = re.findall(company_pattern, html, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            company_data = self._extract_company_data(match, batch)
            if company_data:
                companies.append(company_data)
        
        return companies
    
    def _extract_company_data(self, html_block: str, batch: str) -> Optional[Dict[str, Any]]:
        """Extract company data from HTML block"""
        try:
            # Extract company name
            name_match = re.search(r'<h3[^>]*>(.*?)</h3>', html_block, re.IGNORECASE)
            name = name_match.group(1).strip() if name_match else None
            
            # Extract description
            desc_match = re.search(r'<p[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</p>', 
                                 html_block, re.IGNORECASE)
            description = desc_match.group(1).strip() if desc_match else None
            
            # Extract website
            website_match = re.search(r'href="(https?://[^"]+)"', html_block)
            website = website_match.group(1) if website_match else None
            
            # Extract location from description or other indicators
            location = self._extract_location(html_block)
            
            # Extract industry tags
            tags = self._extract_tags(html_block)
            
            if name:
                return {
                    'name': name,
                    'description': description or '',
                    'website': website,
                    'location': location,
                    'batch': batch,
                    'founded_year': self._batch_to_year(batch),
                    'source': 'y_combinator',
                    'tags': tags,
                    'discovered_date': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Failed to extract company data: {str(e)}")
        
        return None
    
    def _extract_location(self, html_block: str) -> str:
        """Extract location information from HTML"""
        # Look for location patterns
        location_patterns = [
            r'<span[^>]*class="[^"]*location[^"]*"[^>]*>(.*?)</span>',
            r'>\s*(Seattle|Bellevue|Redmond|Kirkland|San Francisco|New York)[^<]*<',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, html_block, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_tags(self, html_block: str) -> List[str]:
        """Extract industry/technology tags"""
        tag_pattern = r'<span[^>]*class="[^"]*tag[^"]*"[^>]*>(.*?)</span>'
        matches = re.findall(tag_pattern, html_block, re.IGNORECASE)
        
        return [tag.strip() for tag in matches if tag.strip()]
    
    def _batch_to_year(self, batch: str) -> int:
        """Convert YC batch to founding year"""
        # Extract year from batch (e.g., W22 -> 2022, S23 -> 2023)
        year_match = re.search(r'(\d{2})$', batch)
        if year_match:
            year_suffix = int(year_match.group(1))
            # Assume 20xx for recent batches
            return 2000 + year_suffix
        
        return datetime.now().year
    
    def _filter_seattle_companies(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter companies for Seattle area"""
        seattle_companies = []
        
        seattle_indicators = [
            'seattle', 'bellevue', 'redmond', 'kirkland', 'tacoma',
            'washington state', 'wa,', 'wa ', 'pacific northwest'
        ]
        
        for company in companies:
            location = company.get('location', '').lower()
            description = company.get('description', '').lower()
            
            # Check location field
            if any(indicator in location for indicator in seattle_indicators):
                seattle_companies.append(company)
                continue
            
            # Check description for Seattle mentions
            if any(indicator in description for indicator in seattle_indicators):
                seattle_companies.append(company)
                continue
        
        return seattle_companies

# Alternative approach using YC's public API if available
class YCombinatorAPIClient:
    """Alternative YC API client if public API becomes available"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.ycombinator.com/v1"
    
    async def get_companies(self, batch: str = None, location: str = None) -> List[Dict[str, Any]]:
        """Get companies via API"""
        # Placeholder for future YC API implementation
        # Currently YC doesn't have a public API for company data
        raise NotImplementedError("YC public API not yet available")

# Fallback: Manual YC company list for immediate testing
KNOWN_YC_SEATTLE_COMPANIES = [
    {
        'name': 'Convoy',
        'description': 'Digital freight network',
        'website': 'https://convoy.com',
        'location': 'Seattle, WA',
        'batch': 'W15',
        'founded_year': 2015,
        'source': 'y_combinator_manual',
        'tags': ['B2B', 'Logistics', 'Transportation']
    },
    {
        'name': 'Luma Health',
        'description': 'Patient engagement platform',
        'website': 'https://lumahealth.io',
        'location': 'Seattle, WA',
        'batch': 'W14',
        'founded_year': 2014,
        'source': 'y_combinator_manual',
        'tags': ['Healthcare', 'B2B', 'SaaS']
    }
    # Add more known Seattle YC companies as needed
]

async def test_yc_scraper():
    """Test function for YC scraper"""
    from config.settings import Config
    
    config = Config()
    scraper = YCombinatorScraper(config)
    
    companies = await scraper.get_seattle_companies()
    
    print(f"Found {len(companies)} Seattle YC companies:")
    for company in companies[:5]:  # Show first 5
        print(f"  - {company['name']}: {company['description'][:100]}...")

if __name__ == "__main__":
    asyncio.run(test_yc_scraper())
