"""
Simple Web Dashboard for Startup Intelligence System
View discovered companies and analysis results
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Simple HTML template (no external dependencies)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Startup Intelligence Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #007bff;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        .company-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
        }
        .company-card {
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 20px;
            background: white;
        }
        .company-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 10px;
        }
        .company-name {
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
        }
        .company-scores {
            display: flex;
            gap: 10px;
        }
        .score {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .score-ai {
            background: #e3f2fd;
            color: #1976d2;
        }
        .score-fit {
            background: #f3e5f5;
            color: #7b1fa2;
        }
        .score-high { background: #e8f5e8; color: #2e7d32; }
        .score-medium { background: #fff3cd; color: #856404; }
        .score-low { background: #f8d7da; color: #721c24; }
        .company-description {
            color: #666;
            margin: 10px 0;
            font-size: 0.9em;
        }
        .company-meta {
            display: flex;
            justify-content: space-between;
            font-size: 0.8em;
            color: #888;
            margin-top: 10px;
        }
        .healthcare-badge {
            background: #d4edda;
            color: #155724;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.7em;
        }
        .filters {
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
        }
        .filter-group {
            display: inline-block;
            margin-right: 20px;
        }
        .filter-group label {
            font-weight: bold;
            margin-right: 5px;
        }
        select, input {
            padding: 5px;
            border: 1px solid #ddd;
            border-radius: 3px;
        }
        .refresh-info {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Startup Intelligence Dashboard</h1>
        
        <div class="refresh-info">
            Last updated: {last_updated}
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total_companies}</div>
                <div class="stat-label">Total Companies</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{high_potential}</div>
                <div class="stat-label">High Potential</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{healthcare_companies}</div>
                <div class="stat-label">Healthcare Focus</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{seattle_companies}</div>
                <div class="stat-label">Seattle Area</div>
            </div>
        </div>
        
        <div class="filters">
            <div class="filter-group">
                <label>Min AI Score:</label>
                <select id="ai-filter" onchange="filterCompanies()">
                    <option value="0">All</option>
                    <option value="6" selected>6+</option>
                    <option value="7">7+</option>
                    <option value="8">8+</option>
                </select>
            </div>
            <div class="filter-group">
                <label>Healthcare Only:</label>
                <input type="checkbox" id="healthcare-filter" onchange="filterCompanies()">
            </div>
            <div class="filter-group">
                <label>Location:</label>
                <select id="location-filter" onchange="filterCompanies()">
                    <option value="">All</option>
                    <option value="Seattle" selected>Seattle</option>
                    <option value="Bellevue">Bellevue</option>
                    <option value="Redmond">Redmond</option>
                </select>
            </div>
        </div>
        
        <div class="company-grid" id="company-grid">
            {company_cards}
        </div>
    </div>
    
    <script>
        const companies = {companies_json};
        
        function getScoreClass(score) {
            if (score >= 8) return 'score-high';
            if (score >= 6) return 'score-medium';
            return 'score-low';
        }
        
        function createCompanyCard(company) {
            const aiScoreClass = getScoreClass(company.ai_washing_score || 0);
            const fitScoreClass = getScoreClass(company.strategic_fit_score || 0);
            const healthcareBadge = company.healthcare_relevance ? 
                '<span class="healthcare-badge">Healthcare</span>' : '';
            
            return `
                <div class="company-card" data-company='${JSON.stringify(company)}'>
                    <div class="company-header">
                        <div class="company-name">${company.name}</div>
                        <div class="company-scores">
                            <span class="score score-ai ${aiScoreClass}">AI: ${company.ai_washing_score || 'N/A'}</span>
                            <span class="score score-fit ${fitScoreClass}">Fit: ${company.strategic_fit_score || 'N/A'}</span>
                        </div>
                    </div>
                    <div class="company-description">
                        ${(company.description || 'No description available').substring(0, 150)}${company.description && company.description.length > 150 ? '...' : ''}
                    </div>
                    <div class="company-meta">
                        <span>${company.location || 'Unknown'}</span>
                        <span>${company.source || 'Unknown source'}</span>
                        ${healthcareBadge}
                    </div>
                    ${company.website ? `<div style="margin-top: 10px;"><a href="${company.website}" target="_blank" style="color: #007bff; text-decoration: none;">🌐 Visit Website</a></div>` : ''}
                </div>
            `;
        }
        
        function filterCompanies() {
            const aiFilter = parseInt(document.getElementById('ai-filter').value);
            const healthcareFilter = document.getElementById('healthcare-filter').checked;
            const locationFilter = document.getElementById('location-filter').value;
            
            const filtered = companies.filter(company => {
                const aiScore = company.ai_washing_score || 0;
                const isHealthcare = company.healthcare_relevance;
                const location = company.location || '';
                
                if (aiScore < aiFilter) return false;
                if (healthcareFilter && !isHealthcare) return false;
                if (locationFilter && !location.toLowerCase().includes(locationFilter.toLowerCase())) return false;
                
                return true;
            });
            
            const grid = document.getElementById('company-grid');
            grid.innerHTML = filtered.map(createCompanyCard).join('');
        }
        
        // Initialize
        filterCompanies();
    </script>
</body>
</html>
"""

class DashboardGenerator:
    """Generate HTML dashboard from database data"""
    
    def __init__(self, config):
        self.config = config
    
    async def generate_dashboard(self, output_file: str = "data/outputs/dashboard.html"):
        """Generate and save dashboard HTML"""
        from src.data.database import DatabaseManager
        
        db = DatabaseManager(self.config.database)
        
        try:
            await db.initialize()
            
            # Get company data
            companies = await db.get_top_companies(limit=100)
            
            # Calculate stats
            stats = self._calculate_stats(companies)
            
            # Generate HTML
            html = self._generate_html(companies, stats)
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"Dashboard generated: {output_file}")
            print(f"Found {len(companies)} companies")
            
        finally:
            await db.close()
    
    def _calculate_stats(self, companies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate dashboard statistics"""
        total = len(companies)
        high_potential = len([c for c in companies 
                            if (c.get('ai_washing_score', 0) >= 7 and 
                                c.get('strategic_fit_score', 0) >= 7)])
        healthcare = len([c for c in companies if c.get('healthcare_relevance', False)])
        seattle = len([c for c in companies 
                      if c.get('location', '').lower().find('seattle') >= 0])
        
        return {
            'total_companies': total,
            'high_potential': high_potential,
            'healthcare_companies': healthcare,
            'seattle_companies': seattle
        }
    
    def _generate_html(self, companies: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
        """Generate HTML dashboard"""
        # Prepare company cards
        company_cards = ""
        for company in companies[:20]:  # Show top 20 in initial load
            company_cards += self._create_company_card(company)
        
        # Prepare companies JSON for JavaScript
        companies_json = json.dumps([dict(c) for c in companies], default=str)
        
        return HTML_TEMPLATE.format(
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_companies=stats['total_companies'],
            high_potential=stats['high_potential'],
            healthcare_companies=stats['healthcare_companies'],
            seattle_companies=stats['seattle_companies'],
            company_cards=company_cards,
            companies_json=companies_json
        )
    
    def _create_company_card(self, company: Dict[str, Any]) -> str:
        """Create HTML for a company card"""
        ai_score = company.get('ai_washing_score', 0)
        fit_score = company.get('strategic_fit_score', 0)
        
        ai_class = self._get_score_class(ai_score)
        fit_class = self._get_score_class(fit_score)
        
        healthcare_badge = ('<span class="healthcare-badge">Healthcare</span>' 
                          if company.get('healthcare_relevance', False) else '')
        
        description = company.get('description', 'No description available')
        if len(description) > 150:
            description = description[:150] + '...'
        
        website_link = (f'<div style="margin-top: 10px;"><a href="{company.get("website")}" target="_blank" style="color: #007bff; text-decoration: none;">🌐 Visit Website</a></div>' 
                       if company.get('website') else '')
        
        return f"""
        <div class="company-card">
            <div class="company-header">
                <div class="company-name">{company.get('name', 'Unknown')}</div>
                <div class="company-scores">
                    <span class="score score-ai {ai_class}">AI: {ai_score or 'N/A'}</span>
                    <span class="score score-fit {fit_class}">Fit: {fit_score or 'N/A'}</span>
                </div>
            </div>
            <div class="company-description">{description}</div>
            <div class="company-meta">
                <span>{company.get('location', 'Unknown')}</span>
                <span>{company.get('source', 'Unknown source')}</span>
                {healthcare_badge}
            </div>
            {website_link}
        </div>
        """
    
    def _get_score_class(self, score: int) -> str:
        """Get CSS class for score"""
        if score >= 8:
            return 'score-high'
        elif score >= 6:
            return 'score-medium'
        else:
            return 'score-low'

async def main():
    """Generate dashboard"""
    from config.settings import Config
    
    config = Config.load_from_env()
    generator = DashboardGenerator(config)
    await generator.generate_dashboard()

if __name__ == "__main__":
    asyncio.run(main())
