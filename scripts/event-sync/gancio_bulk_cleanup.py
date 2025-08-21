#!/usr/bin/env python3
"""
🧹 Gancio Bulk Cleanup Tool - Clean Hidden Event Duplicates
===========================================================
Removes duplicate hidden events and approves unique ones
"""

import sqlite3
import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

class GancioBulkCleanup:
    def __init__(self):
        self.db_path = "/var/lib/gancio/gancio.sqlite"
        
    def analyze_duplicates(self):
        """Analyze duplicate events in the database"""
        print("🔍 ANALYZING DUPLICATE EVENTS")
        print("="*50)
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        try:
            # Get all hidden events
            cursor.execute("""
                SELECT id, title, start_datetime, placeId, description, createdAt
                FROM events 
                WHERE is_visible = 0
                ORDER BY title, start_datetime
            """)
            
            hidden_events = cursor.fetchall()
            print(f"📊 Hidden events: {len(hidden_events)}")
            
            # Group by title and analyze
            title_groups = defaultdict(list)
            for event in hidden_events:
                title_groups[event['title']].append(event)
            
            duplicates = {title: events for title, events in title_groups.items() if len(events) > 1}
            unique_titles = {title: events[0] for title, events in title_groups.items() if len(events) == 1}
            
            print(f"🔄 Duplicate titles: {len(duplicates)}")
            print(f"✨ Unique titles: {len(unique_titles)}")
            
            # Show top duplicates
            sorted_duplicates = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
            print(f"\n🔥 TOP DUPLICATES:")
            for title, events in sorted_duplicates[:10]:
                print(f"   • {title}: {len(events)} copies")
            
            return duplicates, unique_titles, hidden_events
            
        finally:
            conn.close()
    
    def create_cleanup_plan(self, duplicates, unique_titles):
        """Create a plan for cleanup"""
        print(f"\n📋 CREATING CLEANUP PLAN")
        print("="*50)
        
        events_to_delete = []
        events_to_approve = []
        
        # For duplicates: keep the first one, delete the rest
        for title, events in duplicates.items():
            # Sort by creation date, keep the earliest
            sorted_events = sorted(events, key=lambda x: x['createdAt'])
            keep_event = sorted_events[0]
            delete_events = sorted_events[1:]
            
            events_to_approve.append(keep_event['id'])
            events_to_delete.extend([e['id'] for e in delete_events])
            
            print(f"📅 {title}:")
            print(f"   ✅ Keep: ID {keep_event['id']} (created {keep_event['createdAt']})")
            print(f"   ❌ Delete: {len(delete_events)} duplicates")
        
        # For unique titles: approve them
        for title, event in unique_titles.items():
            events_to_approve.append(event['id'])
        
        print(f"\n📊 CLEANUP SUMMARY:")
        print(f"   ✅ Events to approve (make visible): {len(events_to_approve)}")
        print(f"   ❌ Events to delete: {len(events_to_delete)}")
        print(f"   🧮 Total processed: {len(events_to_approve) + len(events_to_delete)}")
        
        return events_to_approve, events_to_delete
    
    def execute_cleanup(self, events_to_approve, events_to_delete, dry_run=True):
        """Execute the cleanup plan"""
        print(f"\n🚀 EXECUTING CLEANUP ({'DRY RUN' if dry_run else 'LIVE RUN'})")
        print("="*50)
        
        if dry_run:
            print("⚠️ DRY RUN MODE - No changes will be made")
            print(f"Would approve {len(events_to_approve)} events")
            print(f"Would delete {len(events_to_delete)} events")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Approve events (make them visible)
            if events_to_approve:
                print(f"✅ Approving {len(events_to_approve)} events...")
                placeholders = ','.join(['?' for _ in events_to_approve])
                cursor.execute(f"""
                    UPDATE events 
                    SET is_visible = 1, updatedAt = ? 
                    WHERE id IN ({placeholders})
                """, [datetime.now().isoformat()] + events_to_approve)
                
                print(f"   ✅ Approved {cursor.rowcount} events")
            
            # Delete duplicate events
            if events_to_delete:
                print(f"❌ Deleting {len(events_to_delete)} duplicate events...")
                placeholders = ','.join(['?' for _ in events_to_delete])
                cursor.execute(f"DELETE FROM events WHERE id IN ({placeholders})", events_to_delete)
                
                print(f"   ❌ Deleted {cursor.rowcount} events")
            
            conn.commit()
            print("✅ Database changes committed!")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def verify_cleanup(self):
        """Verify the cleanup results"""
        print(f"\n🔍 VERIFYING CLEANUP RESULTS")
        print("="*50)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT is_visible, COUNT(*) FROM events GROUP BY is_visible")
            results = cursor.fetchall()
            
            for is_visible, count in results:
                status = "Visible" if is_visible else "Hidden"
                print(f"   {status}: {count} events")
            
            # Check for remaining duplicates
            cursor.execute("""
                SELECT title, COUNT(*) as count 
                FROM events 
                GROUP BY title 
                HAVING count > 1 
                ORDER BY count DESC 
                LIMIT 5
            """)
            
            remaining_dupes = cursor.fetchall()
            if remaining_dupes:
                print(f"\n⚠️ Remaining duplicates (may be legitimate recurring events):")
                for title, count in remaining_dupes:
                    print(f"   • {title}: {count} copies")
            else:
                print(f"\n✅ No title-based duplicates remain!")
                
        finally:
            conn.close()
    
    def run_cleanup(self, dry_run=True):
        """Run the complete cleanup process"""
        print("🧹 GANCIO BULK CLEANUP TOOL")
        print("="*60)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Analyze
        duplicates, unique_titles, hidden_events = self.analyze_duplicates()
        
        # Step 2: Plan
        events_to_approve, events_to_delete = self.create_cleanup_plan(duplicates, unique_titles)
        
        # Step 3: Execute
        self.execute_cleanup(events_to_approve, events_to_delete, dry_run=dry_run)
        
        # Step 4: Verify
        if not dry_run:
            self.verify_cleanup()
        
        print(f"\n✨ Cleanup {'simulation' if dry_run else 'execution'} complete!")
        
        if dry_run:
            print("\n💡 To execute the cleanup for real, run:")
            print("   python3 gancio_bulk_cleanup.py --execute")

def main():
    import sys
    
    cleanup = GancioBulkCleanup()
    
    # Check for execute flag
    dry_run = '--execute' not in sys.argv
    
    if not dry_run:
        print("⚠️ LIVE EXECUTION MODE - Changes will be permanent!")
        response = input("Are you sure you want to proceed? (type 'yes' to continue): ")
        if response.lower() != 'yes':
            print("❌ Cleanup cancelled")
            return
    
    cleanup.run_cleanup(dry_run=dry_run)

if __name__ == "__main__":
    main()
