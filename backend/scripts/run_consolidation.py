#!/usr/bin/env python3
"""
Weekly consolidation job - learns user preferences from feedback.

Run this script via cron:
    0 2 * * 0  cd /path/to/backend && python scripts/run_consolidation.py

This runs every Sunday at 2 AM.
"""
import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from packages.database.connection import get_db
from packages.memory.consolidator import MemoryConsolidator


def main():
    """Run weekly consolidation for all users"""
    print(f"Starting consolidation at {datetime.now(timezone.utc).isoformat()}")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create consolidator
        consolidator = MemoryConsolidator(db)
        
        # Run for last 7 days
        since_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        # Consolidate all users
        results = consolidator.consolidate_all_users(
            since_date=since_date,
            min_events=5,  # Minimum 5 events to learn
        )
        
        # Print summary
        print(f"\nConsolidation complete:")
        print(f"  Users processed: {len(results)}")
        
        if results:
            total_events = sum(r.events_processed for r in results.values())
            total_topics = sum(r.topics_added for r in results.values())
            total_vips = sum(r.vips_added for r in results.values())
            
            print(f"  Total events analyzed: {total_events}")
            print(f"  New topics learned: {total_topics}")
            print(f"  New VIPs promoted: {total_vips}")
            
            # Show per-user details
            print("\nPer-user details:")
            for user_id, result in results.items():
                print(f"  {user_id}:")
                print(f"    Events: {result.events_processed}")
                print(f"    Topics: {result.topics_updated} (+{result.topics_added})")
                print(f"    VIPs: {len(result.preferences_after.get('vip_people', []))} (+{result.vips_added})")
                print(f"    Sources: {result.sources_updated}")
        else:
            print("  No users had sufficient data for consolidation")
        
    except Exception as e:
        print(f"Error during consolidation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
    
    print(f"\nCompleted at {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
