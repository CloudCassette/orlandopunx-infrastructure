#!/usr/bin/env python3
"""
Quick Workflow Fix Script
Identifies and fixes common GitHub Actions workflow issues
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def check_file_permissions():
    """Fix common file permission issues"""
    print("🔧 FIXING FILE PERMISSIONS")
    print("=" * 30)

    script_dir = Path("scripts/event-sync")
    if not script_dir.exists():
        print("❌ scripts/event-sync directory not found")
        return False

    fixed_files = []
    for script_file in script_dir.glob("*.py"):
        if not os.access(script_file, os.X_OK):
            print(f"🔨 Making {script_file} executable...")
            os.chmod(script_file, 0o755)
            fixed_files.append(str(script_file))

    for script_file in script_dir.glob("*.sh"):
        if not os.access(script_file, os.X_OK):
            print(f"🔨 Making {script_file} executable...")
            os.chmod(script_file, 0o755)
            fixed_files.append(str(script_file))

    if fixed_files:
        print(f"✅ Fixed permissions for {len(fixed_files)} files")
        for file in fixed_files:
            print(f"   → {file}")
    else:
        print("✅ All file permissions are correct")

    return True


def check_python_syntax():
    """Check Python syntax for all scripts"""
    print("\n🐍 CHECKING PYTHON SYNTAX")
    print("=" * 30)

    script_dir = Path("scripts/event-sync")
    if not script_dir.exists():
        print("❌ scripts/event-sync directory not found")
        return False

    syntax_errors = []
    for script_file in script_dir.glob("*.py"):
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(script_file)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"✅ {script_file.name} syntax OK")
            else:
                print(f"❌ {script_file.name} has syntax errors:")
                print(f"   {result.stderr.strip()}")
                syntax_errors.append(str(script_file))
        except Exception as e:
            print(f"❌ Could not check {script_file.name}: {e}")
            syntax_errors.append(str(script_file))

    if syntax_errors:
        print(f"\n⚠️ Found syntax errors in {len(syntax_errors)} files:")
        for file in syntax_errors:
            print(f"   → {file}")
        return False
    else:
        print("✅ All Python files have valid syntax")
        return True


def check_python_imports():
    """Check if required Python modules are available"""
    print("\n📦 CHECKING PYTHON IMPORTS")
    print("=" * 30)

    required_modules = ["requests", "json", "os", "sys", "urllib", "datetime"]

    optional_modules = ["beautifulsoup4", "lxml", "jq"]

    missing_required = []
    missing_optional = []

    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} (REQUIRED)")
            missing_required.append(module)

    for module in optional_modules:
        try:
            if module == "beautifulsoup4":
                __import__("bs4")
            else:
                __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"⚠️ {module} (optional)")
            missing_optional.append(module)

    if missing_required:
        print(f"\n❌ Missing required modules: {', '.join(missing_required)}")
        print("Run: pip install " + " ".join(missing_required))
        return False

    if missing_optional:
        print(f"\n⚠️ Missing optional modules: {', '.join(missing_optional)}")
        print("Consider running: pip install " + " ".join(missing_optional))

    return True


def check_workflow_files():
    """Check workflow file syntax and structure"""
    print("\n📄 CHECKING WORKFLOW FILES")
    print("=" * 30)

    workflow_dir = Path(".github/workflows")
    if not workflow_dir.exists():
        print("❌ .github/workflows directory not found")
        return False

    workflow_issues = []
    for workflow_file in workflow_dir.glob("*.yml"):
        try:
            # Basic YAML check (Python has yaml module typically)
            with open(workflow_file) as f:
                content = f.read()

            # Check for common issues
            if "runs-on: self-hosted" not in content:
                print(f"⚠️ {workflow_file.name}: Not using self-hosted runner")

            if "${{ secrets.GANCIO_" not in content:
                print(f"⚠️ {workflow_file.name}: No Gancio secrets referenced")

            if "uses: actions/checkout@" not in content:
                print(f"⚠️ {workflow_file.name}: No checkout action")
                workflow_issues.append(str(workflow_file))
            else:
                print(f"✅ {workflow_file.name} structure looks good")

        except Exception as e:
            print(f"❌ {workflow_file.name}: Error reading file - {e}")
            workflow_issues.append(str(workflow_file))

    return len(workflow_issues) == 0


def create_missing_scripts():
    """Create missing essential scripts if they don't exist"""
    print("\n🔨 CHECKING FOR MISSING SCRIPTS")
    print("=" * 30)

    script_dir = Path("scripts/event-sync")
    script_dir.mkdir(parents=True, exist_ok=True)

    essential_scripts = [
        ("github_actions_diagnostics.py", create_basic_diagnostic_script),
        ("validate_github_secrets.py", create_basic_validation_script),
    ]

    created_scripts = []
    for script_name, creator_func in essential_scripts:
        script_path = script_dir / script_name
        if not script_path.exists():
            print(f"🔨 Creating missing script: {script_name}")
            try:
                creator_func(script_path)
                created_scripts.append(script_name)
                os.chmod(script_path, 0o755)
            except Exception as e:
                print(f"❌ Failed to create {script_name}: {e}")
        else:
            print(f"✅ {script_name} exists")

    if created_scripts:
        print(f"✅ Created {len(created_scripts)} missing scripts")

    return True


def create_basic_diagnostic_script(path):
    """Create a basic diagnostic script"""
    content = '''#!/usr/bin/env python3
"""Basic diagnostic script for GitHub Actions"""

import os
import sys
import requests

def main():
    print("🔍 BASIC DIAGNOSTICS")
    print("=" * 20)

    # Check environment variables
    base_url = os.getenv('GANCIO_BASE_URL')
    email = os.getenv('GANCIO_EMAIL')
    password = os.getenv('GANCIO_PASSWORD')

    print(f"GANCIO_BASE_URL: {'SET' if base_url else 'NOT SET'}")
    print(f"GANCIO_EMAIL: {'SET' if email else 'NOT SET'}")
    print(f"GANCIO_PASSWORD: {'SET' if password else 'NOT SET'}")

    if not all([base_url, email, password]):
        print("❌ Missing required environment variables")
        return 1

    # Test connectivity
    try:
        response = requests.get(f"{base_url}/api/events", timeout=10)
        print(f"✅ API connectivity: {response.status_code}")
        return 0
    except Exception as e:
        print(f"❌ API connectivity failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    with open(path, "w") as f:
        f.write(content)


def create_basic_validation_script(path):
    """Create a basic validation script"""
    content = '''#!/usr/bin/env python3
"""Basic validation script for secrets"""

import os
import sys
import requests
from urllib.parse import urlparse

def main():
    print("🔐 SECRETS VALIDATION")
    print("=" * 20)

    base_url = os.getenv('GANCIO_BASE_URL')
    email = os.getenv('GANCIO_EMAIL')
    password = os.getenv('GANCIO_PASSWORD')

    if not base_url:
        print("❌ GANCIO_BASE_URL not set")
        return 1

    try:
        parsed = urlparse(base_url)
        if not parsed.scheme or not parsed.netloc:
            print("❌ Invalid GANCIO_BASE_URL format")
            return 1
        print(f"✅ GANCIO_BASE_URL format valid: {parsed.scheme}://{parsed.netloc}")
    except Exception as e:
        print(f"❌ URL validation error: {e}")
        return 1

    if email and '@' in email:
        print("✅ GANCIO_EMAIL format valid")
    else:
        print("❌ GANCIO_EMAIL invalid or not set")
        return 1

    if password and len(password) >= 8:
        print(f"✅ GANCIO_PASSWORD adequate length ({len(password)} chars)")
    else:
        print("❌ GANCIO_PASSWORD too short or not set")
        return 1

    print("✅ All secrets validation passed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
    with open(path, "w") as f:
        f.write(content)


def fix_common_issues():
    """Run all common issue fixes"""
    print("🔧 GITHUB ACTIONS WORKFLOW QUICK FIX")
    print("=" * 50)

    all_good = True

    # Check and fix file permissions
    if not check_file_permissions():
        all_good = False

    # Check Python syntax
    if not check_python_syntax():
        all_good = False

    # Check Python imports
    if not check_python_imports():
        all_good = False

    # Check workflow files
    if not check_workflow_files():
        all_good = False

    # Create missing scripts
    if not create_missing_scripts():
        all_good = False

    print("\n" + "=" * 50)
    if all_good:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ Your workflow should work correctly now")
    else:
        print("⚠️ SOME ISSUES FOUND")
        print("Review the output above and fix any remaining issues")

    print("\n💡 NEXT STEPS:")
    print("1. Run the Emergency Debug workflow to verify fixes")
    print("2. Test the Simple Gancio Diagnostic workflow")
    print("3. Check GitHub Actions secrets are properly configured")

    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(fix_common_issues())
