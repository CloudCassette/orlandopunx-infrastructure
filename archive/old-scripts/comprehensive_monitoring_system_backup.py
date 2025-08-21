#!/usr/bin/env python3
"""
Comprehensive Event Data Monitoring System
- Duplicate detection and alerts
- Venue data validation
- Data integrity checks
- Automated reporting
- CI/CD pipeline integration
"""

import hashlib
import json
import os
import re
import time
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

import requests


class ComprehensiveMonitor:
    def __init__(self, gancio_base_url="http://localhost:13120"):
        self.gancio_base_url = gancio_base_url
        self.alerts = []
        self.report_data = {}

    def get_events_from_gancio(self) -> List[Dict]:
        """Get all events from Gancio API"""
        try:
            response = requests.get(f"{self.gancio_base_url}/api/events")
            if response.status_code == 200:
                return response.json()
            else:
                self.add_alert(
                    "ERROR", f"Failed to fetch events: {response.status_code}"
                )
                return []
        except Exception as e:
            self.add_alert("ERROR", f"Error fetching events: {e}")
            return []

    def add_alert(self, level: str, message: str, event_id: Optional[int] = None):
        """Add alert to the alerts list"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": level,  # INFO, WARNING, ERROR, CRITICAL
            "message": message,
            "event_id": event_id,
        }
        self.alerts.append(alert)

        # Print immediately for real-time feedback
        if level in ["ERROR", "CRITICAL"]:
            print(f"🚨 {level}: {message}")
        elif level == "WARNING":
            print(f"⚠️ {level}: {message}")
        else:
            print(f"ℹ️ {level}: {message}")

    def normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        if not title:
            return ""
        normalized = re.sub(r"\s+", " ", title.strip().lower())
        normalized = re.sub(r"[^\w\s]", "", normalized)
        normalized = re.sub(r"\bwith\b|\band\b|\bfeat\b|\bfeaturing\b", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()

    def create_event_signature(self, event: Dict) -> str:
        """Create a signature for duplicate detection"""
        title = self.normalize_title(event.get("title", ""))
        venue = event.get("place", {}).get("name", "").strip().lower()

        start_time = event.get("start_datetime", 0)
        if isinstance(start_time, (int, float)):
            date = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d")
        else:
            date = str(start_time)[:10]

        return f"{title}|{venue}|{date}"

    def titles_are_similar(self, title1: str, title2: str, threshold=0.75) -> bool:
        """Check if two titles are similar"""
        norm1 = self.normalize_title(title1)
        norm2 = self.normalize_title(title2)

        if norm1 == norm2:
            return True

        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity >= threshold

    def detect_duplicates(self, events: List[Dict]) -> Dict:
        """Detect duplicate events with different strategies"""
        print("🔍 Detecting duplicates using multiple strategies...")

        duplicates = {
            "exact_duplicates": {},
            "fuzzy_duplicates": [],
            "suspicious_patterns": [],
        }

        # Strategy 1: Exact signature duplicates
        signatures = {}
        for event in events:
            signature = self.create_event_signature(event)
            if signature not in signatures:
                signatures[signature] = []
            signatures[signature].append(event)

        for signature, event_list in signatures.items():
            if len(event_list) > 1:
                duplicates["exact_duplicates"][signature] = event_list
                self.add_alert(
                    "WARNING", f"Found {len(event_list)} exact duplicates: {signature}"
                )

        # Strategy 2: Fuzzy title matching within same date/venue
        processed_pairs = set()
        for i, event1 in enumerate(events):
            for j, event2 in enumerate(events[i + 1 :], i + 1):
                pair = tuple(sorted([event1.get("id"), event2.get("id")]))
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)

                # Same date and venue
                if event1.get("start_datetime") == event2.get(
                    "start_datetime"
                ) and event1.get("place", {}).get("name") == event2.get(
                    "place", {}
                ).get(
                    "name"
                ):

                    if self.titles_are_similar(
                        event1.get("title", ""), event2.get("title", "")
                    ):
                        duplicates["fuzzy_duplicates"].append([event1, event2])
                        self.add_alert(
                            "WARNING",
                            f"Found fuzzy duplicates: {event1.get('title')[:30]}... vs {event2.get('title')[:30]}...",
                        )

        # Strategy 3: Suspicious patterns (same title different venues)
        title_groups = {}
        for event in events:
            normalized_title = self.normalize_title(event.get("title", ""))
            if normalized_title not in title_groups:
                title_groups[normalized_title] = []
            title_groups[normalized_title].append(event)

        for title, event_list in title_groups.items():
            if len(event_list) > 1:
                venues = set(
                    event.get("place", {}).get("name", "") for event in event_list
                )
                if len(venues) > 1:  # Same title, different venues
                    duplicates["suspicious_patterns"].append(
                        {"title": title, "events": event_list, "venues": list(venues)}
                    )
                    self.add_alert(
                        "INFO",
                        f"Same title across venues: {title[:30]}... ({len(venues)} venues)",
                    )

        return duplicates

    def validate_venue_data(self, events: List[Dict]) -> Dict:
        """Validate venue data integrity"""
        print("🏢 Validating venue data...")

        validation_results = {
            "total_events": len(events),
            "events_with_null_place": [],
            "events_with_null_place_name": [],
            "events_with_empty_place_name": [],
            "events_with_invalid_place_id": [],
            "venue_distribution": {},
            "orphaned_events": [],
        }

        for event in events:
            event_id = event.get("id")
            title = event.get("title", "No title")
            place = event.get("place")
            place_id = event.get("placeId")

            # Check for null place
            if place is None:
                validation_results["events_with_null_place"].append(event)
                self.add_alert(
                    "ERROR",
                    f"Event {event_id} has null place: {title[:40]}...",
                    event_id,
                )
                continue

            # Check for null place name
            place_name = place.get("name") if place else None
            if place_name is None:
                validation_results["events_with_null_place_name"].append(event)
                self.add_alert(
                    "ERROR",
                    f"Event {event_id} has null place name: {title[:40]}...",
                    event_id,
                )
                continue

            # Check for empty place name
            if place_name == "":
                validation_results["events_with_empty_place_name"].append(event)
                self.add_alert(
                    "ERROR",
                    f"Event {event_id} has empty place name: {title[:40]}...",
                    event_id,
                )
                continue

            # Check for invalid place ID
            if place_id is None or place_id == 0:
                validation_results["events_with_invalid_place_id"].append(event)
                self.add_alert(
                    "WARNING",
                    f"Event {event_id} has invalid place ID: {title[:40]}...",
                    event_id,
                )

            # Count venue distribution
            if place_name not in validation_results["venue_distribution"]:
                validation_results["venue_distribution"][place_name] = 0
            validation_results["venue_distribution"][place_name] += 1

        return validation_results

    def check_data_integrity(self, events: List[Dict]) -> Dict:
        """Check overall data integrity"""
        print("🔍 Checking data integrity...")

        integrity_results = {
            "events_missing_title": [],
            "events_missing_datetime": [],
            "events_with_invalid_datetime": [],
            "events_in_past": [],
            "events_far_future": [],
            "data_quality_score": 0,
        }

        now = datetime.now().timestamp()
        one_year_future = (datetime.now() + timedelta(days=365)).timestamp()

        for event in events:
            event_id = event.get("id")
            title = event.get("title")
            start_datetime = event.get("start_datetime")

            # Check for missing title
            if not title or title.strip() == "":
                integrity_results["events_missing_title"].append(event)
                self.add_alert("WARNING", f"Event {event_id} missing title", event_id)

            # Check for missing datetime
            if start_datetime is None:
                integrity_results["events_missing_datetime"].append(event)
                self.add_alert(
                    "ERROR",
                    f"Event {event_id} missing datetime: {title[:40] if title else 'No title'}...",
                    event_id,
                )
                continue

            # Check for invalid datetime
            if not isinstance(start_datetime, (int, float)) or start_datetime <= 0:
                integrity_results["events_with_invalid_datetime"].append(event)
                self.add_alert(
                    "ERROR",
                    f"Event {event_id} has invalid datetime: {start_datetime}",
                    event_id,
                )
                continue

            # Check for events in the far past (more than 1 year ago)
            one_year_ago = now - (365 * 24 * 60 * 60)
            if start_datetime < one_year_ago:
                integrity_results["events_in_past"].append(event)
                self.add_alert(
                    "INFO",
                    f"Event {event_id} is old: {datetime.fromtimestamp(start_datetime).strftime('%Y-%m-%d')}",
                )

            # Check for events too far in the future
            if start_datetime > one_year_future:
                integrity_results["events_far_future"].append(event)
                self.add_alert(
                    "WARNING",
                    f"Event {event_id} is far in future: {datetime.fromtimestamp(start_datetime).strftime('%Y-%m-%d')}",
                )

        # Calculate data quality score (0-100)
        total_checks = len(events) * 4  # 4 checks per event
        failed_checks = (
            len(integrity_results["events_missing_title"])
            + len(integrity_results["events_missing_datetime"])
            + len(integrity_results["events_with_invalid_datetime"])
            + len(integrity_results["events_far_future"])
        )

        if total_checks > 0:
            integrity_results["data_quality_score"] = max(
                0, int((total_checks - failed_checks) / total_checks * 100)
            )
        else:
            integrity_results["data_quality_score"] = 100

        return integrity_results

    def run_comprehensive_check(self) -> Dict:
        """Run all monitoring checks"""
        print(
            f"🚀 Starting comprehensive monitoring at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Clear previous alerts
        self.alerts = []

        # Get events
        events = self.get_events_from_gancio()
        if not events:
            self.add_alert("CRITICAL", "No events found or API error")
            return self.create_report({}, {}, {})

        print(f"📋 Analyzing {len(events)} events")

        # Run all checks
        duplicate_results = self.detect_duplicates(events)
        venue_results = self.validate_venue_data(events)
        integrity_results = self.check_data_integrity(events)

        # Create comprehensive report
        return self.create_report(duplicate_results, venue_results, integrity_results)

    def create_report(
        self, duplicate_results: Dict, venue_results: Dict, integrity_results: Dict
    ) -> Dict:
        """Create comprehensive monitoring report"""
        timestamp = datetime.now()

        report = {
            "timestamp": timestamp.isoformat(),
            "summary": {
                "total_events": venue_results.get("total_events", 0),
                "total_alerts": len(self.alerts),
                "critical_alerts": len(
                    [a for a in self.alerts if a["level"] == "CRITICAL"]
                ),
                "error_alerts": len([a for a in self.alerts if a["level"] == "ERROR"]),
                "warning_alerts": len(
                    [a for a in self.alerts if a["level"] == "WARNING"]
                ),
                "data_quality_score": integrity_results.get("data_quality_score", 0),
            },
            "duplicates": {
                "exact_duplicate_groups": len(
                    duplicate_results.get("exact_duplicates", {})
                ),
                "fuzzy_duplicate_pairs": len(
                    duplicate_results.get("fuzzy_duplicates", [])
                ),
                "suspicious_patterns": len(
                    duplicate_results.get("suspicious_patterns", [])
                ),
            },
            "venue_validation": {
                "null_place_events": len(
                    venue_results.get("events_with_null_place", [])
                ),
                "null_place_name_events": len(
                    venue_results.get("events_with_null_place_name", [])
                ),
                "empty_place_name_events": len(
                    venue_results.get("events_with_empty_place_name", [])
                ),
                "invalid_place_id_events": len(
                    venue_results.get("events_with_invalid_place_id", [])
                ),
                "venue_count": len(venue_results.get("venue_distribution", {})),
            },
            "data_integrity": {
                "missing_title_events": len(
                    integrity_results.get("events_missing_title", [])
                ),
                "missing_datetime_events": len(
                    integrity_results.get("events_missing_datetime", [])
                ),
                "invalid_datetime_events": len(
                    integrity_results.get("events_with_invalid_datetime", [])
                ),
                "old_events": len(integrity_results.get("events_in_past", [])),
                "future_events": len(integrity_results.get("events_far_future", [])),
            },
            "alerts": self.alerts,
            "detailed_results": {
                "duplicates": duplicate_results,
                "venue_validation": venue_results,
                "data_integrity": integrity_results,
            },
        }

        self.report_data = report
        return report

    def print_summary(self, report: Dict):
        """Print monitoring summary"""
        summary = report["summary"]
        duplicates = report["duplicates"]
        venue = report["venue_validation"]
        integrity = report["data_integrity"]

        print(f"\n📊 Monitoring Summary:")
        print(f"   📋 Total events: {summary['total_events']}")
        print(f"   🔍 Data quality score: {summary['data_quality_score']}/100")
        print(f"   🚨 Total alerts: {summary['total_alerts']}")
        print(f"      Critical: {summary['critical_alerts']}")
        print(f"      Errors: {summary['error_alerts']}")
        print(f"      Warnings: {summary['warning_alerts']}")

        print(f"\n🔄 Duplicate Detection:")
        print(f"   Exact duplicate groups: {duplicates['exact_duplicate_groups']}")
        print(f"   Fuzzy duplicate pairs: {duplicates['fuzzy_duplicate_pairs']}")
        print(f"   Suspicious patterns: {duplicates['suspicious_patterns']}")

        print(f"\n🏢 Venue Validation:")
        print(
            f"   Venue data issues: {venue['null_place_events'] + venue['null_place_name_events'] + venue['empty_place_name_events']}"
        )
        print(f"   Total venues: {venue['venue_count']}")

        print(f"\n📋 Data Integrity:")
        print(
            f"   Data issues: {integrity['missing_title_events'] + integrity['missing_datetime_events'] + integrity['invalid_datetime_events']}"
        )

        # Overall health assessment
        if summary["critical_alerts"] > 0:
            print(f"\n🚨 CRITICAL: System needs immediate attention!")
        elif summary["error_alerts"] > 0:
            print(f"\n❌ ERRORS: Issues found that need fixing")
        elif summary["warning_alerts"] > 0:
            print(f"\n⚠️ WARNINGS: Some issues detected")
        else:
            print(f"\n✅ ALL GOOD: No critical issues found")

    def save_report(self, report: Dict) -> str:
        """Save monitoring report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"monitoring_report_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"📄 Detailed report saved to: {report_file}")
        return report_file

    def should_alert(self, report: Dict) -> bool:
        """Determine if alerts should be sent"""
        summary = report["summary"]
        return (
            summary["critical_alerts"] > 0
            or summary["error_alerts"] > 0
            or summary["data_quality_score"] < 90
        )

    def get_ci_exit_code(self, report: Dict) -> int:
        """Get exit code for CI/CD pipeline"""
        summary = report["summary"]

        if summary["critical_alerts"] > 0:
            return 2  # Critical failure
        elif summary["error_alerts"] > 0:
            return 1  # Error
        else:
            return 0  # Success


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Comprehensive Event Monitoring System"
    )
    parser.add_argument(
        "--save-report", action="store_true", help="Save detailed report to file"
    )
    parser.add_argument(
        "--ci-mode", action="store_true", help="CI/CD mode (exit with error codes)"
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress output (for CI)")

    args = parser.parse_args()

    monitor = ComprehensiveMonitor()
    report = monitor.run_comprehensive_check()

    if not args.quiet:
        monitor.print_summary(report)

    if args.save_report:
        monitor.save_report(report)

    if args.ci_mode:
        exit_code = monitor.get_ci_exit_code(report)
        if exit_code > 0 and not args.quiet:
            print(f"\n🚨 CI/CD: Exiting with code {exit_code}")
        return exit_code

    return 0


if __name__ == "__main__":
    import sys

    exit_code = main()
    sys.exit(exit_code)
