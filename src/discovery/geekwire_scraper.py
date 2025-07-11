"""
GeekWire Startup News Scraper
Discovers companies from funding announcements and startup news
"""
import asyncio
import aiohttp
import feedparser
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup

from config.settings import Config

logger = logging.getLogger(__name__)

class GeekWireScraper:
    """Scraper for GeekWire startup news and funding announcements"""
    
    def __init__(self, config: Config):
        self.config = config
        self.rss_urls = [
            'https://www.geekwire.com/feed/',
            'https://www.geekwire.com/startups/feed/',
            'https://www.geekwire.com/funding/feed/'
        ]
        self.session = None
    
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
    
    async def get_recent_startups(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get startups mentioned in recent GeekWire articles"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        all_companies = []
        
        async with self:
            for rss_url in self.rss_urls:
                try:
                    logger.info(f"Scraping GeekWire RSS: {rss_url}")
                    companies = await self._scrape_rss_feed(rss_url, cutoff_date)
                    all_companies.extend(companies)
                    
                    # Rate limiting
                    await asyncio.sleep(self.config.scraping.request_delay)
                    
                except Exception as e:
                    logger.error(f"Failed to scrape {rss_url}: {str(e)}")
        
        # Deduplicate by company name
        unique_companies = self._deduplicate_companies(all_companies)
        logger.info(f"Found {len(unique_companies)} unique companies from GeekWire")
        
        return unique_companies
    
    async def _scrape_rss_feed(self, rss_url: str, cutoff_date: datetime) -> List[Dict[str, Any]]:
        """Scrape companies from RSS feed"""
        try:
            async with self.session.get(rss_url) as response:
                if response.status != 200:
                    logger.error(f"HTTP {response.status} for {rss_url}")
                    return []
                
                rss_content = await response.text()
                
            # Parse RSS feed
            feed = feedparser.parse(rss_content)
            companies = []
            
            for entry in feed.entries:
                # Check if article is recent enough
                article_date = self._parse_article_date(entry)
                if article_date and article_date < cutoff_date:
                    continue
                
                # Extract companies from article
                article_companies = await self._extract_companies_from_article(entry)
                companies.extend(article_companies)
            
            return companies
            
        except Exception as e:
            logger.error(f"RSS scraping failed for {rss_url}: {str(e)}")
            return []
    
    def _parse_article_date(self, entry) -> Optional[datetime]:
        """Parse article publication date"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6])
        except Exception as e:
            logger.error(f"Failed to parse date: {str(e)}")
        
        return None
    
    async def _extract_companies_from_article(self, entry) -> List[Dict[str, Any]]:
        """Extract company information from article"""
        companies = []
        
        try:
            # Get full article content
            article_url = entry.link
            article_content = await self._get_article_content(article_url)
            
            if not article_content:
                return []
            
            # Look for funding/startup indicators
            if not self._is_startup_relevant(entry.title, entry.summary, article_content):
                return []
            
            # Extract company data
            company_data = self._parse_company_from_content(
                entry.title, 
                entry.summary, 
                article_content,
                article_url
            )
            
            if company_data:
                companies.append(company_data)
                
        except Exception as e:
            logger.error(f"Failed to extract companies from {entry.link}: {str(e)}")
        
        return companies
    
    async def _get_article_content(self, url: str) -> str:
        """Get full article content"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract main article content
                    article_selectors = [
                        'article .entry-content',
                        '.post-content',
                        '.article-content',
                        'main article'
                    ]
                    
                    for selector in article_selectors:
                        content_elem = soup.select_one(selector)
                        if content_elem:
                            return content_elem.get_text(strip=True)
                    
                    return soup.get_text(strip=True)
                    
        except Exception as e:
            logger.error(f"Failed to get article content from {url}: {str(e)}")
        
        return ""
    
    def _is_startup_relevant(self, title: str, summary: str, content: str) -> bool:
        """Check if article is relevant to startup discovery"""
        combined_text = f"{title} {summary} {content}".lower()
        
        startup_indicators = [
            'raises', 'funding', 'series a', 'series b', 'seed round',
            'venture capital', 'investment', 'startup', 'founded',
            'launches', 'announces', 'million', 'valuation',
            'ai company', 'machine learning', 'artificial intelligence'
        ]
        
        seattle_indicators = [
            'seattle', 'bellevue', 'redmond', 'kirkland', 'washington'
        ]
        
        has_startup_content = any(indicator in combined_text for indicator in startup_indicators)
        has_seattle_connection = any(indicator in combined_text for indicator in seattle_indicators)
        
        return has_startup_content and has_seattle_connection
    
    def _parse_company_from_content(self, title: str, summary: str, content: str, url: str) -> Optional[Dict[str, Any]]:
        """Parse company information from article content"""
        try:
            # Extract company name from title
            company_name = self._extract_company_name(title, content)
            if not company_name:
                return None
            
            # Extract funding information
            funding_info = self._extract_funding_info(content)
            
            # Extract company description
            description = self._extract_company_description(content, company_name)
            
            # Extract website
            website = self._extract_website(content)
            
            # Extract location
            location = self._extract_location_from_content(content)
            
            return {
                'name': company_name,
                'description': description,
                'website': website,
                'location': location or 'Seattle, WA',  # Default to Seattle
                'funding_info': funding_info,
                'source': 'geekwire',
                'source_article': url,
                'discovered_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to parse company from content: {str(e)}")
            return None
    
    def _extract_company_name(self, title: str, content: str) -> Optional[str]:
        """Extract company name from title and content"""
        # Common patterns in GeekWire headlines
        patterns = [
            r'([A-Z][a-zA-Z0-9\s]+?)\s+raises',
            r'([A-Z][a-zA-Z0-9\s]+?)\s+lands',
            r'([A-Z][a-zA-Z0-9\s]+?)\s+secures',
            r'([A-Z][a-zA-Z0-9\s]+?)\s+announces',
            r'([A-Z][a-zA-Z0-9\s]+?)\s+launches',
            r'Meet\s+([A-Z][a-zA-Z0-9\s]+?)[\s,]',
            r'Seattle.*?startup\s+([A-Z][a-zA-Z0-9\s]+?)[\s,]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Filter out common false positives
                if len(name) > 1 and name.lower() not in ['seattle', 'the', 'a', 'an']:
                    return name
        
        return None
    
    def _extract_funding_info(self, content: str) -> Dict[str, Any]:
        """Extract funding round information"""
        funding_info = {}
        
        # Extract funding amount
        amount_patterns = [
            r'\$(\d+(?:\.\d+)?)\s*million',
            r'\$(\d+(?:\.\d+)?)\s*M',
            r'raised\s+\$(\d+(?:,\d{3})*(?:\.\d+)?)'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                funding_info['amount'] = match.group(1)
                break
        
        # Extract round type
        round_patterns = [
            r'(series [a-z])',
            r'(seed round)',
            r'(pre-seed)',
            r'(series seed)'
        ]
        
        for pattern in round_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                funding_info['round_type'] = match.group(1).title()
                break
        
        # Extract investors
        investor_pattern = r'led by\s+([^.]+)'
        match = re.search(investor_pattern, content, re.IGNORECASE)
        if match:
            funding_info['lead_investor'] = match.group(1).strip()
        
        return funding_info
    
    def _extract_company_description(self, content: str, company_name: str) -> str:
        """Extract company description"""
        # Look for sentences that describe what the company does
        sentences = content.split('.')
        
        for sentence in sentences:
            if company_name.lower() in sentence.lower():
                # Look for descriptive patterns
                desc_patterns = [
                    rf'{re.escape(company_name)}[^.]*?(?:is|builds|offers|provides|develops)[^.]*',
                    rf'(?:the|a)\s+[^.]*?company[^.]*?{re.escape(company_name)}[^.]*',
                ]
                
                for pattern in desc_patterns:
                    match = re.search(pattern, sentence, re.IGNORECASE)
                    if match:
                        return match.group(0).strip()
        
        # Fallback: return first paragraph
        paragraphs = content.split('\n')
        if paragraphs:
            return paragraphs[0][:200] + "..." if len(paragraphs[0]) > 200 else paragraphs[0]
        
        return ""
    
    def _extract_website(self, content: str) -> Optional[str]:
        """Extract company website"""
        # Look for website URLs
        url_patterns = [
            r'https?://(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})',
            r'visit\s+([a-zA-Z0-9-]+\.[a-zA-Z]{2,})',
            r'at\s+([a-zA-Z0-9-]+\.[a-zA-Z]{2,})'
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Filter out common non-company domains
                if not any(domain in match.lower() for domain in 
                          ['geekwire.com', 'twitter.com', 'linkedin.com', 'facebook.com']):
                    return f"https://{match}" if not match.startswith('http') else match
        
        return None
    
    def _extract_location_from_content(self, content: str) -> Optional[str]:
        """Extract location from content"""
        location_patterns = [
            r'based in\s+([^,.]+)',
            r'headquartered in\s+([^,.]+)',
            r'located in\s+([^,.]+)',
            r'(Seattle|Bellevue|Redmond|Kirkland)[^.]*?based',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _deduplicate_companies(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate companies"""
        seen_names = set()
        unique_companies = []
        
        for company in companies:
            name_key = company['name'].lower().strip()
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_companies.append(company)
        
        return unique_companies

async def test_geekwire_scraper():
    """Test function for GeekWire scraper"""
    from config.settings import Config
    
    config = Config()
    scraper = GeekWireScraper(config)
    
    companies = await scraper.get_recent_startups(days_back=7)
    
    print(f"Found {len(companies)} companies from GeekWire:")
    for company in companies[:3]:  # Show first 3
        print(f"  - {company['name']}: {company['description'][:100]}...")
        if company.get('funding_info'):
            print(f"    Funding: {company['funding_info']}")

if __name__ == "__main__":
    asyncio.run(test_geekwire_scraper())
