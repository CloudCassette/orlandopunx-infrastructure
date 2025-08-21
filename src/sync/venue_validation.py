#!/usr/bin/env python3
"""
Venue Assignment Verification and Fixer
- Detects events missing venue/place data
- Fixes missing venue assignments
- Ensures robust venue assignment in sync process
- Provides intelligent venue detection based on event content
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests


class VenueAssignmentFixer:
    def __init__(self, gancio_base_url="http://localhost:13120"):
        self.gancio_base_url = gancio_base_url
        self.session = requests.Session()

        # Enhanced venue mappings with intelligent detection
        self.venue_mappings = {
            # Primary venue names (exact match)
            "will's pub": {
                "id": 1,
                "name": "Will's Pub",
                "address": "1042 N. Mills Ave. Orlando, FL 32803",
            },
            "wills pub": {
                "id": 1,
                "name": "Will's Pub",
                "address": "1042 N. Mills Ave. Orlando, FL 32803",
            },
            "conduit": {
                "id": 5,
                "name": "Conduit",
                "address": "22 S Magnolia Ave, Orlando, FL 32801",
            },
            "stardust": {
                "id": 4,
                "name": "Stardust Video & Coffee",
                "address": "1842 Winter Park Rd",
            },
            "stardust video & coffee": {
                "id": 4,
                "name": "Stardust Video & Coffee",
                "address": "1842 Winter Park Rd",
            },
            "sly fox": {"id": 6, "name": "Sly Fox", "address": "Not Available"},
            # Address-based detection
            "22 s magnolia": {
                "id": 5,
                "name": "Conduit",
                "address": "22 S Magnolia Ave, Orlando, FL 32801",
            },
            "1042 n mills": {
                "id": 1,
                "name": "Will's Pub",
                "address": "1042 N. Mills Ave. Orlando, FL 32803",
            },
            "1842 winter park": {
                "id": 4,
                "name": "Stardust Video & Coffee",
                "address": "1842 Winter Park Rd",
            },
            # Alternative names/variations
            "the conduit": {
                "id": 5,
                "name": "Conduit",
                "address": "22 S Magnolia Ave, Orlando, FL 32801",
            },
            "conduit bar": {
                "id": 5,
                "name": "Conduit",
                "address": "22 S Magnolia Ave, Orlando, FL 32801",
            },
        }

        self.default_venue = {
            "id": 1,
            "name": "Will's Pub",
            "address": "1042 N. Mills Ave. Orlando, FL 32803",
        }

        # Venue detection patterns for intelligent assignment
        self.venue_patterns = {
            5: [  # Conduit
                r"\bconduit\b",
                r"22.*magnolia",
                r"downtown.*orlando",
                r"conduit.*bar",
            ],
            1: [r"will\'?s\s*pub", r"1042.*mills", r"mills.*ave"],  # Will's Pub
            4: [r"stardust", r"video.*coffee", r"1842.*winter"],  # Stardust
            6: [r"sly.*fox"],  # Sly Fox
        }

    def authenticate(self):
        """Authenticate with Gancio"""
        print("🔑 Authenticating with Gancio...")

        email = os.getenv("GANCIO_EMAIL", "godlessamericarecords@gmail.com")
        password = os.getenv("GANCIO_PASSWORD")

        if not password:
            print("❌ GANCIO_PASSWORD environment variable required")
            return False

        try:
            self.session.get(f"{self.gancio_base_url}/login")

            login_url = f"{self.gancio_base_url}/auth/login"
            response = self.session.post(
                login_url,
                data={"email": email, "password": password},
                allow_redirects=True,
            )

            if "admin" in response.url or response.status_code == 200:
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def get_all_events(self) -> List[Dict]:
        """Get all events from Gancio"""
        try:
            response = requests.get(f"{self.gancio_base_url}/api/events")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to fetch events: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching events: {e}")
            return []

    def normalize_venue_name(self, venue_name: str) -> str:
        """Normalize venue name for lookup"""
        if not venue_name:
            return ""
        return re.sub(r"[^\w\s]", "", venue_name.strip().lower())

    def detect_venue_from_content(self, event: Dict) -> Optional[Dict]:
        """Intelligently detect venue from event content"""
        # Combine title, description, and any other text fields
        text_content = " ".join(
            [
                event.get("title", ""),
                event.get("description", ""),
                str(event.get("venue", "")),
                str(event.get("location", "")),
            ]
        ).lower()

        # Check patterns for each venue
        for venue_id, patterns in self.venue_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_content, re.IGNORECASE):
                    # Find the venue info by ID
                    for venue_info in self.venue_mappings.values():
                        if venue_info["id"] == venue_id:
                            return venue_info

        return None

    def get_venue_info(self, venue_name: str, event: Dict = None) -> Dict:
        """Get venue info with intelligent detection"""
        if venue_name:
            normalized = self.normalize_venue_name(venue_name)
            if normalized in self.venue_mappings:
                return self.venue_mappings[normalized]

        # Try intelligent detection from event content
        if event:
            detected_venue = self.detect_venue_from_content(event)
            if detected_venue:
                print(
                    f"🎯 Intelligently detected venue: {detected_venue['name']} for event: {event.get('title', 'Unknown')[:40]}..."
                )
                return detected_venue

        # Fallback to default
        return self.default_venue

    def analyze_venue_assignments(self) -> Dict:
        """Analyze all events for venue assignment issues"""
        print("🔍 Analyzing venue assignments...")

        events = self.get_all_events()
        if not events:
            return {}

        analysis = {
            "total_events": len(events),
            "events_missing_place": [],
            "events_missing_place_id": [],
            "events_with_null_place": [],
            "events_with_empty_place_name": [],
            "events_needing_intelligent_assignment": [],
            "venue_distribution": {},
            "problematic_events": [],
        }

        for event in events:
            event_id = event.get("id")
            title = event.get("title", "No title")
            place = event.get("place")
            place_id = event.get("placeId")

            # Check for missing place object
            if place is None:
                analysis["events_with_null_place"].append(event)
                analysis["problematic_events"].append(
                    {
                        "id": event_id,
                        "title": title,
                        "issue": "null_place",
                        "suggested_fix": self.get_venue_info("", event),
                    }
                )
                continue

            # Check for missing place name
            place_name = place.get("name") if isinstance(place, dict) else None
            if not place_name:
                analysis["events_with_empty_place_name"].append(event)
                analysis["problematic_events"].append(
                    {
                        "id": event_id,
                        "title": title,
                        "issue": "empty_place_name",
                        "suggested_fix": self.get_venue_info("", event),
                    }
                )
                continue

            # Check for missing or invalid place ID
            if place_id is None or place_id == 0:
                analysis["events_missing_place_id"].append(event)
                analysis["problematic_events"].append(
                    {
                        "id": event_id,
                        "title": title,
                        "issue": "invalid_place_id",
                        "current_place": place,
                        "suggested_fix": self.get_venue_info(place_name, event),
                    }
                )

            # Count venue distribution
            if place_name:
                if place_name not in analysis["venue_distribution"]:
                    analysis["venue_distribution"][place_name] = 0
                analysis["venue_distribution"][place_name] += 1

        return analysis

    def fix_event_venue(self, event_id: int, venue_info: Dict) -> bool:
        """Fix venue assignment for a specific event"""
        if not self.authenticate():
            return False

        try:
            # Use the correct API endpoint for updating events
            update_url = f"{self.gancio_base_url}/api/event/{event_id}"
            update_data = {"place_id": venue_info["id"]}

            response = self.session.put(update_url, json=update_data)

            if response.status_code in [200, 204]:
                print(f"✅ Fixed venue for event {event_id} → {venue_info['name']}")
                return True
            else:
                print(
                    f"❌ Failed to fix venue for event {event_id}: {response.status_code} - {response.text[:100]}"
                )
                return False

        except Exception as e:
            print(f"❌ Error fixing venue for event {event_id}: {e}")
            return False

    def generate_fix_commands(self, analysis: Dict) -> List[str]:
        """Generate curl commands to fix venue issues"""
        commands = []

        if not analysis.get("problematic_events"):
            return commands

        print("🔧 Generating fix commands...")

        for problem in analysis["problematic_events"]:
            event_id = problem["id"]
            suggested_fix = problem["suggested_fix"]
            venue_id = suggested_fix["id"]
            venue_name = suggested_fix["name"]

            # Generate curl command for manual execution
            command = (
                f'curl -X PUT "{self.gancio_base_url}/api/event/{event_id}" '
                f'-H "Content-Type: application/json" '
                f'-H "Authorization: Bearer YOUR_TOKEN" '
                f"-d '{{\"place_id\": {venue_id}}}' "
                f"# Fix event {event_id} → {venue_name}"
            )
            commands.append(command)

        return commands

    def run_automated_fixes(self, analysis: Dict, dry_run=True) -> Dict:
        """Run automated fixes for venue issues"""
        problematic_events = analysis.get("problematic_events", [])

        if not problematic_events:
            print("✅ No venue issues found to fix!")
            return {"fixed": 0, "failed": 0, "skipped": 0}

        print(
            f"🔧 {'DRY RUN - Would fix' if dry_run else 'Fixing'} {len(problematic_events)} venue issues..."
        )

        results = {"fixed": 0, "failed": 0, "skipped": 0}

        for problem in problematic_events:
            event_id = problem["id"]
            title = problem["title"]
            suggested_fix = problem["suggested_fix"]

            print(
                f"{'[DRY RUN] Would fix' if dry_run else 'Fixing'} event {event_id}: {title[:40]}... → {suggested_fix['name']}"
            )

            if dry_run:
                results["skipped"] += 1
            else:
                if self.fix_event_venue(event_id, suggested_fix):
                    results["fixed"] += 1
                else:
                    results["failed"] += 1

        return results

    def create_venue_assignment_report(self, analysis: Dict) -> str:
        """Create detailed venue assignment report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"venue_assignment_report_{timestamp}.json"

        # Add fix commands to the analysis
        analysis["fix_commands"] = self.generate_fix_commands(analysis)

        with open(report_file, "w") as f:
            json.dump(analysis, f, indent=2, default=str)

        print(f"📄 Venue assignment report saved to: {report_file}")
        return report_file

    def print_analysis_summary(self, analysis: Dict):
        """Print venue assignment analysis summary"""
        total = analysis["total_events"]
        problems = len(analysis.get("problematic_events", []))

        print(f"\n📊 Venue Assignment Analysis:")
        print(f"   📋 Total events: {total}")
        print(f"   🚨 Events with venue issues: {problems}")
        print(f"   ✅ Events with correct venues: {total - problems}")

        if analysis.get("venue_distribution"):
            print(f"\n🏢 Current Venue Distribution:")
            for venue, count in sorted(analysis["venue_distribution"].items()):
                print(f"   {venue}: {count} events")

        if problems > 0:
            print(f"\n⚠️ Issues Found:")
            issue_types = {}
            for problem in analysis.get("problematic_events", []):
                issue_type = problem["issue"]
                if issue_type not in issue_types:
                    issue_types[issue_type] = 0
                issue_types[issue_type] += 1

            for issue_type, count in issue_types.items():
                print(f"   {issue_type.replace('_', ' ').title()}: {count} events")
        else:
            print(f"\n✅ All events have proper venue assignments!")


def create_venue_enforced_sync_template():
    """Create a template showing proper venue enforcement in sync scripts"""
    template = '''
# Enhanced Venue Assignment Template for Sync Scripts

def ensure_venue_assignment(event_data: Dict) -> Dict:
    """Ensure every event has a valid venue assignment"""

    # 1. Extract venue information from multiple sources
    venue_sources = [
        event_data.get('venue'),
        event_data.get('location'),
        event_data.get('place', {}).get('name') if isinstance(event_data.get('place'), dict) else None,
        extract_venue_from_title(event_data.get('title', '')),
        extract_venue_from_description(event_data.get('description', ''))
    ]

    # 2. Find the first valid venue
    venue_name = None
    for source in venue_sources:
        if source and source.strip():
            venue_name = source.strip()
            break

    # 3. Map venue name to venue info
    venue_validator = VenueValidator()
    venue_info = venue_validator.get_venue_info(venue_name, event_data)

    # 4. Ensure all venue fields are set
    event_data['venue'] = venue_info['name']
    event_data['place_id'] = venue_info['id']
    event_data['place'] = {
        'id': venue_info['id'],
        'name': venue_info['name'],
        'address': venue_info.get('address', '')
    }

    # 5. Validation check
    if not event_data.get('place_id') or event_data.get('place_id') == 0:
        print(f"⚠️ WARNING: Event still missing venue after assignment: {event_data.get('title', 'Unknown')}")
        # Force default venue as last resort
        event_data['place_id'] = 1  # Will's Pub

    return event_data

def extract_venue_from_title(title: str) -> Optional[str]:
    """Extract venue from event title"""
    venue_patterns = {
        r'@\s*([^,\n]+)': 1,  # "Event @ Venue"
        r'at\s+([^,\n]+)': 1,  # "Event at Venue"
        r'\b(conduit)\b': 1,   # Conduit mentions
        r'\b(will\'?s\s*pub)\b': 1,  # Will's Pub mentions
    }

    for pattern, _ in venue_patterns.items():
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None

# Example usage in sync script:
def create_event_in_gancio(raw_event_data):
    # 1. Process and clean event data
    processed_event = process_event_data(raw_event_data)

    # 2. CRITICAL: Ensure venue assignment
    processed_event = ensure_venue_assignment(processed_event)

    # 3. Validate before sending to API
    if not processed_event.get('place_id'):
        raise ValueError(f"Event missing venue assignment: {processed_event.get('title')}")

    # 4. Create in Gancio
    gancio_payload = {
        'title': processed_event['title'],
        'description': processed_event.get('description', ''),
        'start_datetime': processed_event['start_datetime'],
        'place_id': processed_event['place_id'],  # MUST be present
        # ... other fields
    }

    response = session.post(f"{gancio_url}/api/event", json=gancio_payload)
    return response
'''

    with open("venue_enforcement_template.py", "w") as f:
        f.write(template)

    print("📝 Created venue enforcement template: venue_enforcement_template.py")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Venue Assignment Verification and Fixer"
    )
    parser.add_argument(
        "--analyze", action="store_true", help="Analyze venue assignments"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Fix venue issues automatically"
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=True, help="Dry run mode (default)"
    )
    parser.add_argument("--force", action="store_true", help="Actually perform fixes")
    parser.add_argument(
        "--generate-commands", action="store_true", help="Generate manual fix commands"
    )
    parser.add_argument(
        "--create-template",
        action="store_true",
        help="Create venue enforcement template",
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate detailed report"
    )

    args = parser.parse_args()

    if args.create_template:
        create_venue_enforced_sync_template()
        return

    fixer = VenueAssignmentFixer()

    # Always run analysis first
    analysis = fixer.analyze_venue_assignments()
    fixer.print_analysis_summary(analysis)

    if args.report:
        fixer.create_venue_assignment_report(analysis)

    if args.generate_commands:
        commands = fixer.generate_fix_commands(analysis)
        if commands:
            print(f"\n🔧 Manual Fix Commands:")
            for cmd in commands:
                print(f"   {cmd}")
        else:
            print(f"\n✅ No fix commands needed!")

    if args.fix:
        dry_run = not args.force
        results = fixer.run_automated_fixes(analysis, dry_run=dry_run)

        print(f"\n📊 Fix Results:")
        print(f"   ✅ Fixed: {results['fixed']}")
        print(f"   ❌ Failed: {results['failed']}")
        print(f"   ⏭️ Skipped (dry run): {results['skipped']}")


if __name__ == "__main__":
    main()
