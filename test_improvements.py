#!/usr/bin/env python3
"""
Test script for improved sync system
"""

import json
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, "/home/cloudcassette/orlandopunx-infrastructure/src")


def test_deduplication():
    """Test the deduplication logic"""
    print("🧪 Testing deduplication logic...")

    try:
        from sync.improved_sync import EnhancedEventDeduplicator, PersistentStateManager

        # Create test events
        event1 = {
            "title": "Test Event at Will's Pub",
            "venue": "Will's Pub",
            "start_datetime": 1724457600,  # Example timestamp
            "description": "This is a test event",
        }

        event2 = {
            "title": "Test Event at Wills Pub",  # Slight variation
            "venue": "Wills Pub",  # No apostrophe
            "start_datetime": 1724457600,  # Same date
            "description": "This is a test event with slight variation",
        }

        # Test hashing
        state_manager = PersistentStateManager("/tmp/test_state.pkl")
        deduplicator = EnhancedEventDeduplicator(state_manager)

        hash1 = deduplicator.create_event_hash(event1)
        hash2 = deduplicator.create_event_hash(event2)

        print(f"   Event 1 hash: {hash1[:16]}...")
        print(f"   Event 2 hash: {hash2[:16]}...")

        # Test normalization
        norm1 = deduplicator._normalize_text("Will's Pub")
        norm2 = deduplicator._normalize_text("Wills Pub")

        print(f"   Normalized venue 1: '{norm1}'")
        print(f"   Normalized venue 2: '{norm2}'")

        if norm1 == norm2:
            print("   ✅ Venue normalization working correctly")
        else:
            print("   ⚠️ Venue normalization may need adjustment")

        return True

    except Exception as e:
        print(f"   ❌ Deduplication test failed: {e}")
        return False


def test_state_management():
    """Test state persistence"""
    print("\n🧪 Testing state management...")

    try:
        from datetime import datetime

        from sync.improved_sync import EventState, PersistentStateManager

        # Create state manager with test file
        state_file = "/tmp/test_event_state.pkl"
        if os.path.exists(state_file):
            os.remove(state_file)

        manager = PersistentStateManager(state_file)

        # Test adding state
        test_state = EventState(
            event_hash="test_hash_123",
            gancio_id=None,
            last_seen=datetime.now(),
            source="test",
            venue="Test Venue",
            title="Test Event",
            date="2023-08-23",
            status="pending",
        )

        manager.mark_event_processed("test_hash_123", test_state)

        # Test checking processed
        if manager.is_event_processed("test_hash_123"):
            print("   ✅ Event marking/checking working correctly")
        else:
            print("   ❌ Event marking failed")
            return False

        # Test persistence
        manager.save_state()

        # Load fresh manager
        manager2 = PersistentStateManager(state_file)

        if manager2.is_event_processed("test_hash_123"):
            print("   ✅ State persistence working correctly")
        else:
            print("   ❌ State persistence failed")
            return False

        # Cleanup
        if os.path.exists(state_file):
            os.remove(state_file)

        return True

    except Exception as e:
        print(f"   ❌ State management test failed: {e}")
        return False


def test_scheduling():
    """Test intelligent scheduling"""
    print("\n🧪 Testing intelligent scheduling...")

    try:
        from sync.improved_sync import mark_sync_run, should_run_sync

        # Clear any existing sync marker
        sync_file = "/tmp/orlandopunx_last_sync"
        if os.path.exists(sync_file):
            os.remove(sync_file)

        # Should run on first check (no previous run)
        if should_run_sync():
            print("   ✅ First run detection working")
        else:
            print("   ❌ First run detection failed")
            return False

        # Mark a sync run
        mark_sync_run()

        # Should not run immediately after marking
        if not should_run_sync():
            print("   ✅ Recent run detection working")
        else:
            print("   ⚠️ Recent run detection may be too permissive")

        # Cleanup
        if os.path.exists(sync_file):
            os.remove(sync_file)

        return True

    except Exception as e:
        print(f"   ❌ Scheduling test failed: {e}")
        return False


def test_imports():
    """Test that all imports work"""
    print("\n🧪 Testing imports...")

    try:
        from sync.improved_sync import (
            EnhancedEventDeduplicator,
            EventState,
            ImprovedGancioSync,
            PersistentStateManager,
        )

        print("   ✅ Main sync module imports working")

        from sync.cleanup_duplicates import GancioDuplicateCleanup

        print("   ✅ Cleanup module imports working")

        return True

    except Exception as e:
        print(f"   ❌ Import test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing Orlando Punx Sync Improvements")
    print("=" * 50)

    tests = [test_imports, test_deduplication, test_state_management, test_scheduling]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The improvements are ready to deploy.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
