"""
GitHub Organization Analyzer
Analyzes GitHub presence for ML contributions and technical depth
"""
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re

from config.settings import Config, AI_DETECTION_CONFIG

logger = logging.getLogger(__name__)

class GitHubAnalyzer:
    """Analyzer for GitHub organization ML activity"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = None
        self.api_base = "https://api.github.com"
        self.ml_indicators = AI_DETECTION_CONFIG['github_ml_indicators']
    
    async def __aenter__(self):
        """Async context manager entry"""
        headers = {'User-Agent': self.config.scraping.user_agents[0]}
        
        if self.config.api.github_token:
            headers['Authorization'] = f'token {self.config.api.github_token}'
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.scraping.timeout),
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def analyze_company_github(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze company's GitHub presence for ML activity"""
        github_data = {
            'organization_found': False,
            'ml_repositories': [],
            'ml_contributions_score': 0,
            'total_repositories': 0,
            'python_repositories': 0,
            'ml_related_repos': 0,
            'recent_ml_activity': False,
            'open_source_ml_projects': [],
            'analysis_date': datetime.now().isoformat()
        }
        
        async with self:
            # Find GitHub organization
            github_org = await self._find_github_organization(company)
            
            if not github_org:
                logger.info(f"No GitHub organization found for {company.get('name', 'unknown')}")
                return github_data
            
            github_data['organization_found'] = True
            github_data['organization_name'] = github_org
            
            # Analyze repositories
            repos = await self._get_organization_repositories(github_org)
            if repos:
                github_data.update(await self._analyze_repositories(repos))
            
            # Analyze recent activity
            github_data['recent_ml_activity'] = await self._check_recent_ml_activity(github_org)
            
            # Calculate overall ML contribution score
            github_data['ml_contributions_score'] = self._calculate_ml_score(github_data)
        
        return github_data
    
    async def _find_github_organization(self, company: Dict[str, Any]) -> Optional[str]:
        """Find GitHub organization for company"""
        # Try multiple strategies to find GitHub org
        
        # 1. Check company website for GitHub links
        website = company.get('website')
        if website:
            github_org = await self._extract_github_from_website(website)
            if github_org:
                return github_org
        
        # 2. Try common naming patterns
        company_name = company.get('name', '')
        if company_name:
            potential_orgs = self._generate_potential_org_names(company_name)
            
            for org_name in potential_orgs:
                if await self._github_org_exists(org_name):
                    logger.info(f"Found GitHub org: {org_name}")
                    return org_name
        
        return None
    
    async def _extract_github_from_website(self, website: str) -> Optional[str]:
        """Extract GitHub organization from company website"""
        try:
            async with self.session.get(website) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Look for GitHub links
                    github_patterns = [
                        r'github\.com/([a-zA-Z0-9\-_]+)(?:/|$)',
                        r'href=["\']https://github\.com/([a-zA-Z0-9\-_]+)["\']'
                    ]
                    
                    for pattern in github_patterns:
                        matches = re.findall(pattern, html, re.IGNORECASE)
                        for match in matches:
                            # Filter out individual users and common false positives
                            if (match not in ['microsoft', 'google', 'facebook', 'apple', 'amazon'] and
                                not match.startswith('user-') and
                                len(match) > 2):
                                
                                # Verify it's an organization, not a user
                                if await self._is_github_organization(match):
                                    return match
        
        except Exception as e:
            logger.error(f"Failed to extract GitHub from {website}: {str(e)}")
        
        return None
    
    def _generate_potential_org_names(self, company_name: str) -> List[str]:
        """Generate potential GitHub organization names"""
        name = company_name.lower()
        
        # Remove common suffixes
        name = re.sub(r'\s+(inc|corp|corporation|llc|ltd|limited)\.?$', '', name)
        
        potential_names = [
            name.replace(' ', '-'),
            name.replace(' ', ''),
            name.replace(' ', '_'),
            name.replace(' ', '.'),
            name.split()[0] if ' ' in name else name,  # First word only
        ]
        
        # Add common variations
        if len(name.split()) > 1:
            words = name.split()
            potential_names.extend([
                ''.join(word[0] for word in words),  # Acronym
                words[0] + words[-1],  # First + last word
            ])
        
        # Remove duplicates and invalid names
        valid_names = []
        for name in potential_names:
            if (name and 
                len(name) >= 2 and 
                re.match(r'^[a-zA-Z0-9\-_.]+$', name) and
                name not in valid_names):
                valid_names.append(name)
        
        return valid_names[:10]  # Limit to 10 attempts
    
    async def _github_org_exists(self, org_name: str) -> bool:
        """Check if GitHub organization exists"""
        try:
            url = f"{self.api_base}/orgs/{org_name}"
            async with self.session.get(url) as response:
                return response.status == 200
        except Exception:
            return False
    
    async def _is_github_organization(self, name: str) -> bool:
        """Check if GitHub name is an organization (not a user)"""
        try:
            # Check organization endpoint
            org_url = f"{self.api_base}/orgs/{name}"
            async with self.session.get(org_url) as response:
                if response.status == 200:
                    return True
            
            # If not an org, check if it's a user with repos that look like org repos
            user_url = f"{self.api_base}/users/{name}"
            async with self.session.get(user_url) as response:
                if response.status == 200:
                    user_data = await response.json()
                    # Consider it an "org" if user has many public repos
                    return user_data.get('public_repos', 0) > 5
            
            return False
            
        except Exception:
            return False
    
    async def _get_organization_repositories(self, org_name: str) -> List[Dict[str, Any]]:
        """Get all repositories for an organization"""
        repos = []
        page = 1
        per_page = 100
        
        try:
            while len(repos) < 500:  # Limit to 500 repos max
                url = f"{self.api_base}/orgs/{org_name}/repos"
                params = {
                    'page': page,
                    'per_page': per_page,
                    'sort': 'updated',
                    'direction': 'desc'
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        page_repos = await response.json()
                        if not page_repos:
                            break
                        
                        repos.extend(page_repos)
                        page += 1
                        
                        # Rate limiting
                        await asyncio.sleep(0.1)
                    else:
                        logger.error(f"Failed to get repos for {org_name}: HTTP {response.status}")
                        break
        
        except Exception as e:
            logger.error(f"Error getting repositories for {org_name}: {str(e)}")
        
        return repos
    
    async def _analyze_repositories(self, repos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze repositories for ML content"""
        analysis = {
            'total_repositories': len(repos),
            'python_repositories': 0,
            'ml_related_repos': 0,
            'ml_repositories': [],
            'open_source_ml_projects': [],
            'languages_used': {},
            'ml_keywords_found': set()
        }
        
        for repo in repos:
            # Count Python repos
            if repo.get('language') == 'Python':
                analysis['python_repositories'] += 1
            
            # Track languages
            lang = repo.get('language')
            if lang:
                analysis['languages_used'][lang] = analysis['languages_used'].get(lang, 0) + 1
            
            # Check for ML indicators
            ml_score = self._score_repository_for_ml(repo)
            if ml_score > 0:
                analysis['ml_related_repos'] += 1
                
                repo_info = {
                    'name': repo['name'],
                    'description': repo.get('description', ''),
                    'language': repo.get('language'),
                    'stars': repo.get('stargazers_count', 0),
                    'forks': repo.get('forks_count', 0),
                    'updated_at': repo.get('updated_at'),
                    'ml_score': ml_score,
                    'url': repo.get('html_url')
                }
                
                analysis['ml_repositories'].append(repo_info)
                
                # Track significant open source ML projects
                if (repo.get('stargazers_count', 0) > 50 or 
                    repo.get('forks_count', 0) > 10):
                    analysis['open_source_ml_projects'].append(repo_info)
        
        # Sort ML repositories by score
        analysis['ml_repositories'].sort(key=lambda x: x['ml_score'], reverse=True)
        analysis['open_source_ml_projects'].sort(key=lambda x: x['stars'], reverse=True)
        
        # Convert set to list for JSON serialization
        analysis['ml_keywords_found'] = list(analysis['ml_keywords_found'])
        
        return analysis
    
    def _score_repository_for_ml(self, repo: Dict[str, Any]) -> float:
        """Score a repository for ML relevance (0-10)"""
        score = 0
        
        name = repo.get('name', '').lower()
        description = repo.get('description', '').lower() if repo.get('description') else ''
        language = repo.get('language', '').lower() if repo.get('language') else ''
        
        combined_text = f"{name} {description}"
        
        # Check for ML indicators
        for indicator in self.ml_indicators:
            if indicator in combined_text:
                score += 1
        
        # Language bonuses
        if language == 'python':
            score += 1
        elif language in ['r', 'julia', 'scala']:
            score += 0.5
        
        # Specific ML keywords with higher weights
        high_value_keywords = [
            'neural', 'deep learning', 'tensorflow', 'pytorch', 
            'machine learning', 'artificial intelligence', 'nlp',
            'computer vision', 'reinforcement learning'
        ]
        
        for keyword in high_value_keywords:
            if keyword in combined_text:
                score += 2
        
        # Repository activity and popularity
        stars = repo.get('stargazers_count', 0)
        if stars > 100:
            score += 1
        if stars > 1000:
            score += 1
        
        # Recent activity
        updated_at = repo.get('updated_at')
        if updated_at:
            try:
                updated_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                days_ago = (datetime.now(updated_date.tzinfo) - updated_date).days
                if days_ago < 30:
                    score += 0.5
            except Exception:
                pass
        
        return min(10, score)
    
    async def _check_recent_ml_activity(self, org_name: str) -> bool:
        """Check for recent ML-related activity"""
        try:
            # Check recent commits in ML repositories
            url = f"{self.api_base}/search/commits"
            params = {
                'q': f'org:{org_name} machine learning OR neural network OR deep learning',
                'sort': 'committer-date',
                'order': 'desc'
            }
            
            # Note: Search commits API requires special accept header
            headers = {'Accept': 'application/vnd.github.cloak-preview'}
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    commits = data.get('items', [])
                    
                    # Check if any commits in last 30 days
                    for commit in commits[:5]:  # Check first 5 commits
                        commit_date_str = commit.get('commit', {}).get('committer', {}).get('date')
                        if commit_date_str:
                            commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00'))
                            days_ago = (datetime.now(commit_date.tzinfo) - commit_date).days
                            if days_ago < 30:
                                return True
            
        except Exception as e:
            logger.error(f"Failed to check recent ML activity for {org_name}: {str(e)}")
        
        return False
    
    def _calculate_ml_score(self, github_data: Dict[str, Any]) -> int:
        """Calculate overall ML contribution score (1-10)"""
        if not github_data['organization_found']:
            return 0
        
        score = 0
        total_repos = github_data.get('total_repositories', 0)
        ml_repos = github_data.get('ml_related_repos', 0)
        python_repos = github_data.get('python_repositories', 0)
        
        # Base score for having a GitHub presence
        score += 2
        
        # ML repository ratio
        if total_repos > 0:
            ml_ratio = ml_repos / total_repos
            score += min(3, ml_ratio * 10)  # Max 3 points
        
        # Python usage (good indicator for ML)
        if total_repos > 0:
            python_ratio = python_repos / total_repos
            score += min(2, python_ratio * 4)  # Max 2 points
        
        # Open source ML projects
        ml_projects = github_data.get('open_source_ml_projects', [])
        if ml_projects:
            score += min(2, len(ml_projects) * 0.5)  # Max 2 points
        
        # Recent activity
        if github_data.get('recent_ml_activity', False):
            score += 1
        
        return min(10, max(0, int(score)))

async def test_github_analyzer():
    """Test function for GitHub analyzer"""
    from config.settings import Config
    
    config = Config()
    analyzer = GitHubAnalyzer(config)
    
    # Test companies
    test_companies = [
        {
            'name': 'OpenAI',
            'website': 'https://openai.com'
        },
        {
            'name': 'Hugging Face',
            'website': 'https://huggingface.co'
        },
        {
            'name': 'Anthropic',
            'website': 'https://anthropic.com'
        }
    ]
    
    for company in test_companies:
        print(f"\nAnalyzing GitHub presence for {company['name']}...")
        github_data = await analyzer.analyze_company_github(company)
        
        print(f"  Organization found: {github_data['organization_found']}")
        if github_data['organization_found']:
            print(f"  ML repositories: {github_data['ml_related_repos']}/{github_data['total_repositories']}")
            print(f"  ML score: {github_data['ml_contributions_score']}/10")
            print(f"  Recent ML activity: {github_data['recent_ml_activity']}")

if __name__ == "__main__":
    asyncio.run(test_github_analyzer())
