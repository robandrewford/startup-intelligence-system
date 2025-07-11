"""
AI-Washing Detection Module
Identifies real AI companies vs. ChatGPT integration plays
Based on Nate's framework for authentic AI detection
"""
import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional
import re
from bs4 import BeautifulSoup
import json

from config.settings import Config, AI_DETECTION_CONFIG

logger = logging.getLogger(__name__)

class AIWashingDetector:
    """Detector for AI-washing vs. authentic AI companies"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = None
        self.detection_config = AI_DETECTION_CONFIG
    
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
    
    async def calculate_ai_washing_score(self, company: Dict[str, Any]) -> int:
        """Calculate AI-washing score (1-10, higher = more authentic AI)"""
        score = 0
        
        async with self:
            # 1. Engineering blog analysis (30% weight)
            blog_score = await self._analyze_engineering_blog(company)
            score += blog_score * 0.3
            
            # 2. Job postings analysis (25% weight)
            jobs_score = await self._analyze_job_postings(company)
            score += jobs_score * 0.25
            
            # 3. GitHub presence analysis (25% weight)
            github_score = await self._analyze_github_presence(company)
            score += github_score * 0.25
            
            # 4. Marketing content analysis (20% weight)
            marketing_score = await self._analyze_marketing_content(company)
            score += marketing_score * 0.2
        
        # Ensure score is between 1-10
        final_score = max(1, min(10, int(score)))
        
        logger.info(f"AI-washing score for {company.get('name', 'unknown')}: {final_score}")
        return final_score
    
    async def _analyze_engineering_blog(self, company: Dict[str, Any]) -> float:
        """Analyze engineering blog for technical depth (0-10)"""
        website = company.get('website')
        if not website:
            return 0
        
        try:
            # Look for engineering blog
            blog_urls = await self._find_engineering_blog(website)
            if not blog_urls:
                return 2  # No blog found
            
            total_score = 0
            blog_count = 0
            
            for blog_url in blog_urls[:3]:  # Analyze up to 3 blog posts
                try:
                    blog_content = await self._get_page_content(blog_url)
                    if blog_content:
                        post_score = self._score_blog_post_content(blog_content)
                        total_score += post_score
                        blog_count += 1
                        
                        # Rate limiting
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    logger.error(f"Failed to analyze blog post {blog_url}: {str(e)}")
            
            if blog_count > 0:
                avg_score = total_score / blog_count
                return min(10, avg_score)
            
        except Exception as e:
            logger.error(f"Blog analysis failed for {company.get('name')}: {str(e)}")
        
        return 2
    
    async def _find_engineering_blog(self, website: str) -> List[str]:
        """Find engineering blog URLs"""
        blog_paths = [
            '/blog', '/engineering', '/tech', '/blog/engineering',
            '/technical-blog', '/dev-blog', '/engineering-blog'
        ]
        
        blog_urls = []
        base_url = website.rstrip('/')
        
        # Check main website for blog links
        try:
            main_content = await self._get_page_content(website)
            if main_content:
                # Look for blog links in main content
                soup = BeautifulSoup(main_content, 'html.parser')
                
                # Find blog links
                blog_keywords = ['blog', 'engineering', 'technical', 'tech']
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '').lower()
                    text = link.get_text().lower()
                    
                    if any(keyword in href or keyword in text for keyword in blog_keywords):
                        if href.startswith('/'):
                            full_url = base_url + href
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            continue
                        
                        if full_url not in blog_urls:
                            blog_urls.append(full_url)
        
        except Exception as e:
            logger.error(f"Failed to find blog for {website}: {str(e)}")
        
        # Fallback: try common blog paths
        if not blog_urls:
            for path in blog_paths:
                blog_urls.append(base_url + path)
        
        return blog_urls[:5]  # Limit to 5 URLs
    
    def _score_blog_post_content(self, content: str) -> float:
        """Score individual blog post for technical depth (0-10)"""
        if not content:
            return 0
        
        content_lower = content.lower()
        score = 0
        
        # Positive indicators (real ML content)
        positive_keywords = self.detection_config['blog_keywords']['positive']
        positive_matches = sum(1 for keyword in positive_keywords if keyword in content_lower)
        score += min(6, positive_matches * 0.5)  # Max 6 points
        
        # Negative indicators (AI-washing)
        negative_keywords = self.detection_config['blog_keywords']['negative']
        negative_matches = sum(1 for keyword in negative_keywords if keyword in content_lower)
        score -= negative_matches * 1.0  # Penalty for AI-washing
        
        # Technical depth indicators
        technical_patterns = [
            r'model\s+accuracy',
            r'precision\s+and\s+recall',
            r'training\s+loss',
            r'hyperparameter',
            r'feature\s+engineering',
            r'data\s+preprocessing',
            r'model\s+deployment',
            r'inference\s+latency'
        ]
        
        technical_matches = sum(1 for pattern in technical_patterns 
                              if re.search(pattern, content_lower))
        score += min(3, technical_matches * 0.5)  # Max 3 points
        
        # Code examples or technical diagrams
        if '<code>' in content or '```' in content or 'github.com' in content_lower:
            score += 1
        
        return max(0, min(10, score))
    
    async def _analyze_job_postings(self, company: Dict[str, Any]) -> float:
        """Analyze job postings for ML engineer ratio (0-10)"""
        company_name = company.get('name')
        if not company_name:
            return 0
        
        try:
            # Search for job postings (simplified - in reality would use LinkedIn/AngelList APIs)
            job_data = await self._search_job_postings(company_name)
            
            if not job_data:
                return 3  # Default score if no job data found
            
            total_positions = len(job_data)
            ml_positions = 0
            
            # Calculate ML engineer ratio
            for job in job_data:
                job_title = job.get('title', '').lower()
                
                # Weight different job types
                for title_pattern, weight in self.detection_config['job_title_weights'].items():
                    if title_pattern.lower() in job_title:
                        ml_positions += weight
                        break
            
            if total_positions > 0:
                ml_ratio = ml_positions / total_positions
                
                # Score based on ML engineer ratio
                if ml_ratio >= 0.3:  # 30%+ ML engineers
                    return 10
                elif ml_ratio >= 0.2:  # 20%+ ML engineers
                    return 8
                elif ml_ratio >= 0.15:  # 15%+ ML engineers
                    return 6
                elif ml_ratio >= 0.1:  # 10%+ ML engineers
                    return 4
                else:
                    return 2
            
        except Exception as e:
            logger.error(f"Job analysis failed for {company_name}: {str(e)}")
        
        return 3  # Default score
    
    async def _search_job_postings(self, company_name: str) -> List[Dict[str, Any]]:
        """Search for company job postings (simplified implementation)"""
        # In a real implementation, this would use LinkedIn, AngelList, or Greenhouse APIs
        # For now, return mock data or scrape job board pages
        
        # Placeholder implementation
        mock_jobs = [
            {'title': 'Software Engineer', 'description': 'Build web applications'},
            {'title': 'Product Manager', 'description': 'Manage product roadmap'},
        ]
        
        # Add ML-related jobs based on company type
        description = company.get('description', '').lower()
        if any(keyword in description for keyword in ['ai', 'ml', 'machine learning', 'data science']):
            mock_jobs.extend([
                {'title': 'Machine Learning Engineer', 'description': 'Build ML models'},
                {'title': 'Data Scientist', 'description': 'Analyze data and build models'}
            ])
        
        return mock_jobs
    
    async def _analyze_github_presence(self, company: Dict[str, Any]) -> float:
        """Analyze GitHub presence for ML contributions (0-10)"""
        website = company.get('website')
        company_name = company.get('name')
        
        if not website and not company_name:
            return 0
        
        try:
            # Find GitHub organization
            github_org = await self._find_github_org(website, company_name)
            
            if not github_org:
                return 2  # No GitHub presence found
            
            # Analyze repositories
            repo_score = await self._analyze_github_repos(github_org)
            
            return min(10, repo_score)
            
        except Exception as e:
            logger.error(f"GitHub analysis failed for {company_name}: {str(e)}")
        
        return 2
    
    async def _find_github_org(self, website: str, company_name: str) -> Optional[str]:
        """Find GitHub organization for company"""
        # Try to find GitHub links on website
        if website:
            try:
                content = await self._get_page_content(website)
                if content:
                    github_pattern = r'github\.com/([a-zA-Z0-9\-_]+)'
                    matches = re.findall(github_pattern, content)
                    if matches:
                        return matches[0]
            except Exception:
                pass
        
        # Try common GitHub organization names
        if company_name:
            possible_orgs = [
                company_name.lower().replace(' ', '-'),
                company_name.lower().replace(' ', ''),
                company_name.lower().replace(' ', '_')
            ]
            
            for org in possible_orgs:
                if await self._github_org_exists(org):
                    return org
        
        return None
    
    async def _github_org_exists(self, org_name: str) -> bool:
        """Check if GitHub organization exists"""
        if not self.config.api.github_token:
            return False
        
        try:
            url = f"https://api.github.com/orgs/{org_name}"
            headers = {'Authorization': f'token {self.config.api.github_token}'}
            
            async with self.session.get(url, headers=headers) as response:
                return response.status == 200
                
        except Exception:
            return False
    
    async def _analyze_github_repos(self, github_org: str) -> float:
        """Analyze GitHub repositories for ML content"""
        if not self.config.api.github_token:
            return 5  # Default score if no GitHub token
        
        try:
            url = f"https://api.github.com/orgs/{github_org}/repos"
            headers = {'Authorization': f'token {self.config.api.github_token}'}
            
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    return 3
                
                repos = await response.json()
                
                ml_indicators = self.detection_config['github_ml_indicators']
                ml_repo_count = 0
                total_repos = len(repos)
                
                for repo in repos:
                    description = (repo.get('description') or '').lower()
                    name = repo.get('name', '').lower()
                    language = (repo.get('language') or '').lower()
                    
                    # Check for ML indicators
                    if any(indicator in description or indicator in name 
                          for indicator in ml_indicators):
                        ml_repo_count += 1
                    
                    # Python repos are often ML-related
                    if language == 'python':
                        ml_repo_count += 0.5
                
                if total_repos > 0:
                    ml_ratio = ml_repo_count / total_repos
                    return min(10, ml_ratio * 20)  # Scale to 0-10
                
        except Exception as e:
            logger.error(f"GitHub repo analysis failed: {str(e)}")
        
        return 3
    
    async def _analyze_marketing_content(self, company: Dict[str, Any]) -> float:
        """Analyze marketing content for AI-washing indicators (0-10)"""
        website = company.get('website')
        description = company.get('description', '')
        
        if not website and not description:
            return 5
        
        try:
            # Get website content
            content = ""
            if website:
                content = await self._get_page_content(website)
            
            combined_content = f"{description} {content}".lower()
            
            # Look for specific AI claims vs. vague buzzwords
            specific_claims = [
                'accuracy', 'precision', 'recall', 'f1 score',
                'training data', 'model performance', 'inference time',
                'custom model', 'proprietary algorithm'
            ]
            
            vague_claims = [
                'ai-powered', 'artificial intelligence', 'machine learning magic',
                'smart technology', 'intelligent system', 'ai revolution'
            ]
            
            specific_count = sum(1 for claim in specific_claims if claim in combined_content)
            vague_count = sum(1 for claim in vague_claims if claim in combined_content)
            
            # Score based on specificity
            score = 5  # Base score
            score += min(3, specific_count * 0.5)  # Bonus for specific claims
            score -= min(3, vague_count * 0.3)  # Penalty for vague claims
            
            # Check for ChatGPT integration mentions
            if 'chatgpt' in combined_content or 'openai api' in combined_content:
                if specific_count == 0:  # Only ChatGPT, no custom AI
                    score -= 3
            
            return max(1, min(10, score))
            
        except Exception as e:
            logger.error(f"Marketing analysis failed: {str(e)}")
        
        return 5
    
    async def _get_page_content(self, url: str) -> str:
        """Get webpage content"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    return soup.get_text(strip=True)
        except Exception as e:
            logger.error(f"Failed to get content from {url}: {str(e)}")
        
        return ""

async def test_ai_washing_detector():
    """Test function for AI-washing detector"""
    from config.settings import Config
    
    config = Config()
    detector = AIWashingDetector(config)
    
    # Test companies
    test_companies = [
        {
            'name': 'Real AI Company',
            'description': 'We build custom neural networks for computer vision',
            'website': 'https://example-ai.com'
        },
        {
            'name': 'AI Washing Company',
            'description': 'We use ChatGPT to revolutionize business with AI-powered solutions',
            'website': 'https://example-washing.com'
        }
    ]
    
    for company in test_companies:
        score = await detector.calculate_ai_washing_score(company)
        print(f"{company['name']}: AI-washing score = {score}")

if __name__ == "__main__":
    asyncio.run(test_ai_washing_detector())
