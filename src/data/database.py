"""
Database Manager for Startup Intelligence System
Handles PostgreSQL operations for company data storage and retrieval
"""
import asyncio
import asyncpg
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from config.settings import DatabaseConfig

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool and create tables"""
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.name,
                user=self.config.user,
                password=self.config.password,
                min_size=2,
                max_size=10
            )
            
            # Create tables if they don't exist
            await self._create_tables()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connections closed")
    
    async def _create_tables(self):
        """Create database tables"""
        async with self.pool.acquire() as conn:
            # Companies table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS companies (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    website VARCHAR(255),
                    description TEXT,
                    location VARCHAR(100),
                    stage VARCHAR(50),
                    employees_count INTEGER,
                    founded_year INTEGER,
                    batch VARCHAR(20),
                    source VARCHAR(50),
                    source_article VARCHAR(500),
                    tags TEXT[],
                    ai_washing_score INTEGER,
                    strategic_fit_score INTEGER,
                    healthcare_relevance BOOLEAN,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(name, website)
                )
            ''')
            
            # Funding rounds table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS funding_rounds (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
                    round_type VARCHAR(50),
                    amount_usd BIGINT,
                    amount_text VARCHAR(100),
                    announced_date DATE,
                    lead_investor VARCHAR(255),
                    investors TEXT[],
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Company intelligence table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS company_intelligence (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
                    github_analysis JSONB,
                    technical_depth_score INTEGER,
                    team_quality_score INTEGER,
                    market_position TEXT,
                    recent_news TEXT[],
                    competitive_analysis TEXT,
                    swot_analysis JSONB,
                    analysis_notes TEXT,
                    last_analyzed TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Discovery runs table for tracking automation performance
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS discovery_runs (
                    id SERIAL PRIMARY KEY,
                    run_date DATE DEFAULT CURRENT_DATE,
                    companies_discovered INTEGER,
                    companies_analyzed INTEGER,
                    high_potential_targets INTEGER,
                    ai_washing_filtered INTEGER,
                    runtime_seconds FLOAT,
                    success BOOLEAN,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Create indexes for better performance
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_companies_ai_score 
                ON companies(ai_washing_score DESC)
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_companies_strategic_fit 
                ON companies(strategic_fit_score DESC)
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_companies_healthcare 
                ON companies(healthcare_relevance)
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_companies_location 
                ON companies(location)
            ''')
    
    async def upsert_company(self, company_data: Dict[str, Any]) -> int:
        """Insert or update company data"""
        async with self.pool.acquire() as conn:
            # Check if company exists
            existing_id = await conn.fetchval('''
                SELECT id FROM companies 
                WHERE name = $1 OR website = $2
            ''', company_data.get('name'), company_data.get('website'))
            
            if existing_id:
                # Update existing company
                company_id = await self._update_company(conn, existing_id, company_data)
            else:
                # Insert new company
                company_id = await self._insert_company(conn, company_data)
            
            # Handle funding information if present
            if company_data.get('funding_info'):
                await self._upsert_funding(conn, company_id, company_data['funding_info'])
            
            # Handle GitHub analysis if present
            if company_data.get('github_analysis'):
                await self._upsert_intelligence(conn, company_id, company_data)
            
            return company_id
    
    async def _insert_company(self, conn, company_data: Dict[str, Any]) -> int:
        """Insert new company"""
        company_id = await conn.fetchval('''
            INSERT INTO companies (
                name, website, description, location, stage, employees_count,
                founded_year, batch, source, source_article, tags,
                ai_washing_score, strategic_fit_score, healthcare_relevance
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            RETURNING id
        ''',
            company_data.get('name'),
            company_data.get('website'),
            company_data.get('description'),
            company_data.get('location'),
            company_data.get('stage'),
            company_data.get('employees_count'),
            company_data.get('founded_year'),
            company_data.get('batch'),
            company_data.get('source'),
            company_data.get('source_article'),
            company_data.get('tags', []),
            company_data.get('ai_washing_score'),
            company_data.get('strategic_fit_score'),
            company_data.get('healthcare_relevance', False)
        )
        
        logger.info(f"Inserted new company: {company_data.get('name')} (ID: {company_id})")
        return company_id
    
    async def _update_company(self, conn, company_id: int, company_data: Dict[str, Any]) -> int:
        """Update existing company"""
        await conn.execute('''
            UPDATE companies SET
                description = COALESCE($2, description),
                location = COALESCE($3, location),
                stage = COALESCE($4, stage),
                employees_count = COALESCE($5, employees_count),
                ai_washing_score = COALESCE($6, ai_washing_score),
                strategic_fit_score = COALESCE($7, strategic_fit_score),
                healthcare_relevance = COALESCE($8, healthcare_relevance),
                updated_at = NOW()
            WHERE id = $1
        ''',
            company_id,
            company_data.get('description'),
            company_data.get('location'),
            company_data.get('stage'),
            company_data.get('employees_count'),
            company_data.get('ai_washing_score'),
            company_data.get('strategic_fit_score'),
            company_data.get('healthcare_relevance')
        )
        
        logger.info(f"Updated company ID: {company_id}")
        return company_id
    
    async def _upsert_funding(self, conn, company_id: int, funding_info: Dict[str, Any]):
        """Insert or update funding information"""
        # Check if funding round already exists
        existing_round = await conn.fetchval('''
            SELECT id FROM funding_rounds 
            WHERE company_id = $1 AND round_type = $2
        ''', company_id, funding_info.get('round_type'))
        
        if existing_round:
            # Update existing round
            await conn.execute('''
                UPDATE funding_rounds SET
                    amount_text = $2,
                    lead_investor = $3
                WHERE id = $1
            ''',
                existing_round,
                funding_info.get('amount'),
                funding_info.get('lead_investor')
            )
        else:
            # Insert new round
            await conn.execute('''
                INSERT INTO funding_rounds (
                    company_id, round_type, amount_text, lead_investor
                ) VALUES ($1, $2, $3, $4)
            ''',
                company_id,
                funding_info.get('round_type'),
                funding_info.get('amount'),
                funding_info.get('lead_investor')
            )
    
    async def _upsert_intelligence(self, conn, company_id: int, company_data: Dict[str, Any]):
        """Insert or update company intelligence"""
        # Check if intelligence record exists
        existing_intel = await conn.fetchval('''
            SELECT id FROM company_intelligence WHERE company_id = $1
        ''', company_id)
        
        github_analysis = json.dumps(company_data.get('github_analysis', {}))
        
        if existing_intel:
            # Update existing intelligence
            await conn.execute('''
                UPDATE company_intelligence SET
                    github_analysis = $2,
                    last_analyzed = NOW()
                WHERE id = $1
            ''', existing_intel, github_analysis)
        else:
            # Insert new intelligence
            await conn.execute('''
                INSERT INTO company_intelligence (
                    company_id, github_analysis
                ) VALUES ($1, $2)
            ''', company_id, github_analysis)
    
    async def get_top_companies(self, limit: int = 20, healthcare_only: bool = False) -> List[Dict[str, Any]]:
        """Get top companies by strategic fit and AI authenticity"""
        async with self.pool.acquire() as conn:
            where_clause = ""
            if healthcare_only:
                where_clause = "WHERE healthcare_relevance = true"
            
            rows = await conn.fetch(f'''
                SELECT c.*, 
                       f.round_type, f.amount_text, f.lead_investor,
                       ci.github_analysis
                FROM companies c
                LEFT JOIN funding_rounds f ON c.id = f.company_id
                LEFT JOIN company_intelligence ci ON c.id = ci.company_id
                {where_clause}
                ORDER BY 
                    c.strategic_fit_score DESC NULLS LAST,
                    c.ai_washing_score DESC NULLS LAST,
                    c.updated_at DESC
                LIMIT $1
            ''', limit)
            
            return [dict(row) for row in rows]
    
    async def get_companies_by_criteria(self, 
                                      min_ai_score: int = 6,
                                      min_fit_score: int = 6,
                                      location_filter: str = None,
                                      healthcare_only: bool = False) -> List[Dict[str, Any]]:
        """Get companies matching specific criteria"""
        async with self.pool.acquire() as conn:
            conditions = [
                "ai_washing_score >= $1",
                "strategic_fit_score >= $2"
            ]
            params = [min_ai_score, min_fit_score]
            param_count = 2
            
            if location_filter:
                param_count += 1
                conditions.append(f"location ILIKE ${param_count}")
                params.append(f"%{location_filter}%")
            
            if healthcare_only:
                conditions.append("healthcare_relevance = true")
            
            where_clause = " AND ".join(conditions)
            
            rows = await conn.fetch(f'''
                SELECT c.*, 
                       f.round_type, f.amount_text, f.lead_investor
                FROM companies c
                LEFT JOIN funding_rounds f ON c.id = f.company_id
                WHERE {where_clause}
                ORDER BY 
                    c.strategic_fit_score DESC,
                    c.ai_washing_score DESC,
                    c.updated_at DESC
            ''', *params)
            
            return [dict(row) for row in rows]
    
    async def record_discovery_run(self, stats: Dict[str, Any], success: bool = True, error: str = None):
        """Record discovery run statistics"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO discovery_runs (
                    companies_discovered, companies_analyzed, high_potential_targets,
                    ai_washing_filtered, runtime_seconds, success, error_message
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''',
                stats.get('companies_discovered', 0),
                stats.get('companies_analyzed', 0),
                stats.get('high_potential_targets', 0),
                stats.get('ai_washing_filtered', 0),
                stats.get('runtime_seconds', 0),
                success,
                error
            )
    
    async def get_discovery_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get discovery run statistics for the last N days"""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_runs,
                    AVG(companies_discovered) as avg_discovered,
                    AVG(companies_analyzed) as avg_analyzed,
                    AVG(high_potential_targets) as avg_targets,
                    AVG(runtime_seconds) as avg_runtime,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_runs
                FROM discovery_runs
                WHERE run_date >= CURRENT_DATE - INTERVAL '%s days'
            ''' % days)
            
            return dict(stats) if stats else {}
    
    async def search_companies(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search companies by name or description"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT c.*, f.round_type, f.amount_text
                FROM companies c
                LEFT JOIN funding_rounds f ON c.id = f.company_id
                WHERE c.name ILIKE $1 OR c.description ILIKE $1
                ORDER BY c.strategic_fit_score DESC NULLS LAST
                LIMIT $2
            ''', f"%{query}%", limit)
            
            return [dict(row) for row in rows]

# Database management utilities
async def init_database(config: DatabaseConfig):
    """Initialize database with tables"""
    db = DatabaseManager(config)
    await db.initialize()
    await db.close()
    logger.info("Database initialization complete")

async def test_database():
    """Test database operations"""
    from config.settings import Config
    
    config = Config()
    db = DatabaseManager(config.database)
    
    try:
        await db.initialize()
        
        # Test company insertion
        test_company = {
            'name': 'Test AI Company',
            'description': 'A test company for ML development',
            'website': 'https://test-ai.com',
            'location': 'Seattle, WA',
            'ai_washing_score': 8,
            'strategic_fit_score': 7,
            'healthcare_relevance': True,
            'source': 'test'
        }
        
        company_id = await db.upsert_company(test_company)
        print(f"Inserted test company with ID: {company_id}")
        
        # Test retrieval
        top_companies = await db.get_top_companies(limit=5)
        print(f"Found {len(top_companies)} companies")
        
        for company in top_companies:
            print(f"  - {company['name']}: AI={company['ai_washing_score']}, Fit={company['strategic_fit_score']}")
        
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(test_database())
