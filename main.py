"""
Main entry point for Startup Intelligence System
Run daily discovery and analysis
"""
import asyncio
import logging
import sys
import argparse
from datetime import datetime
import json

from config.settings import Config
from src.discovery.discovery_engine import StartupDiscoveryEngine
from src.data.database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'data/outputs/discovery_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def run_discovery(args):
    """Run discovery engine"""
    logger.info("Starting startup discovery run")
    
    config = Config.load_from_env()
    
    # Validate configuration
    issues = config.validate()
    if issues:
        logger.error("Configuration issues found:")
        for issue in issues:
            logger.error(f"  - {issue}")
        return False
    
    db = DatabaseManager(config.database)
    engine = StartupDiscoveryEngine(config)
    
    try:
        await db.initialize()
        
        # Run discovery
        report = await engine.run_daily_discovery()
        
        # Save report
        report_file = f'data/outputs/discovery_report_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Discovery report saved to {report_file}")
        
        # Record run in database
        await db.record_discovery_run(report['statistics'], success=True)
        
        return True
        
    except Exception as e:
        logger.error(f"Discovery run failed: {str(e)}")
        if db.pool:
            await db.record_discovery_run({}, success=False, error=str(e))
        return False
        
    finally:
        await db.close()

async def analyze_company(args):
    """Analyze specific company"""
    config = Config.load_from_env()
    db = DatabaseManager(config.database)
    
    try:
        await db.initialize()
        
        if args.search:
            companies = await db.search_companies(args.search, limit=5)
            print(f"\nFound {len(companies)} companies matching '{args.search}':")
            for company in companies:
                print(f"  - {company['name']}: AI={company['ai_washing_score']}, Fit={company['strategic_fit_score']}")
        
        if args.top:
            companies = await db.get_top_companies(limit=args.top, healthcare_only=args.healthcare)
            print(f"\nTop {args.top} companies:")
            for i, company in enumerate(companies, 1):
                print(f"{i}. {company['name']}")
                print(f"   AI Score: {company['ai_washing_score']}, Fit Score: {company['strategic_fit_score']}")
                print(f"   Location: {company['location']}")
                print(f"   Healthcare: {company['healthcare_relevance']}")
                print(f"   Description: {company['description'][:100]}...")
                print()
        
    finally:
        await db.close()

async def show_stats(args):
    """Show discovery statistics"""
    config = Config.load_from_env()
    db = DatabaseManager(config.database)
    
    try:
        await db.initialize()
        
        stats = await db.get_discovery_stats(days=args.days)
        
        print(f"\nDiscovery Statistics (Last {args.days} days)")
        print("=" * 50)
        print(f"Total runs: {stats.get('total_runs', 0)}")
        print(f"Successful runs: {stats.get('successful_runs', 0)}")
        print(f"Avg companies discovered: {stats.get('avg_discovered', 0):.1f}")
        print(f"Avg companies analyzed: {stats.get('avg_analyzed', 0):.1f}")
        print(f"Avg high-potential targets: {stats.get('avg_targets', 0):.1f}")
        print(f"Avg runtime: {stats.get('avg_runtime', 0):.1f} seconds")
        
    finally:
        await db.close()

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Startup Intelligence System')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Discovery command
    discovery_parser = subparsers.add_parser('discover', help='Run discovery engine')
    discovery_parser.set_defaults(func=run_discovery)
    
    # Analysis command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze companies')
    analyze_parser.add_argument('--search', type=str, help='Search for companies')
    analyze_parser.add_argument('--top', type=int, default=10, help='Show top N companies')
    analyze_parser.add_argument('--healthcare', action='store_true', help='Healthcare companies only')
    analyze_parser.set_defaults(func=analyze_company)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.add_argument('--days', type=int, default=30, help='Days to analyze')
    stats_parser.set_defaults(func=show_stats)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # Run the selected command
    success = asyncio.run(args.func(args))
    
    if args.command == 'discover':
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
