#!/bin/bash
# Local Debug Runner Script
# Simulates GitHub Actions environment locally for debugging

set -e

echo "🏠 LOCAL GITHUB ACTIONS DEBUG RUNNER"
echo "====================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f ".github/workflows/simple-diagnostic.yml" ]; then
    log_error "This script must be run from the repository root directory"
    log_info "Navigate to your repository directory first"
    exit 1
fi

# Load environment variables if .env file exists
if [ -f ".env" ]; then
    log_info "Loading environment variables from .env file"
    source .env
elif [ -f ".env.local" ]; then
    log_info "Loading environment variables from .env.local file"
    source .env.local
else
    log_warning "No .env file found. Set GANCIO_* variables manually or create .env file"
fi

# Check required environment variables
log_info "Checking environment variables..."
MISSING_VARS=()

if [ -z "$GANCIO_BASE_URL" ]; then
    MISSING_VARS+=("GANCIO_BASE_URL")
fi

if [ -z "$GANCIO_EMAIL" ]; then
    MISSING_VARS+=("GANCIO_EMAIL")
fi

if [ -z "$GANCIO_PASSWORD" ]; then
    MISSING_VARS+=("GANCIO_PASSWORD")
fi

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    log_error "Missing required environment variables: ${MISSING_VARS[*]}"
    echo ""
    log_info "Create a .env file with:"
    echo "GANCIO_BASE_URL=http://your-server:13120"
    echo "GANCIO_EMAIL=admin@domain.com"
    echo "GANCIO_PASSWORD=your-password"
    echo ""
    log_info "Or export them manually:"
    echo "export GANCIO_BASE_URL='http://your-server:13120'"
    echo "export GANCIO_EMAIL='admin@domain.com'"
    echo "export GANCIO_PASSWORD='your-password'"
    exit 1
fi

log_success "All environment variables are set"

# Set up simulation environment
export GITHUB_WORKSPACE=$(pwd)
export GITHUB_REPOSITORY="local-debug/simulation"
export GITHUB_REF="refs/heads/main"
export GITHUB_SHA="local-debug-sha"
export RUNNER_OS="Linux"
export RUNNER_TEMP="/tmp"
export ACTIONS_STEP_DEBUG="true"
export ACTIONS_RUNNER_DEBUG="true"

# Menu for what to test
echo ""
log_info "What would you like to debug?"
echo "1. Environment setup"
echo "2. Network connectivity" 
echo "3. Secrets and authentication"
echo "4. Script execution"
echo "5. Full diagnostic suite"
echo "6. Run specific Python script"
echo "7. Install act (GitHub Actions runner)"
echo "8. Exit"

read -p "Enter your choice (1-8): " choice

case $choice in
    1)
        log_info "Testing environment setup..."
        
        # Python check
        if command -v python3 >/dev/null 2>&1; then
            log_success "Python3: $(python3 --version)"
        else
            log_error "Python3 not found"
        fi
        
        # Virtual environment test
        log_info "Creating virtual environment..."
        python3 -m venv test_venv
        source test_venv/bin/activate
        
        log_info "Installing dependencies..."
        pip install --upgrade pip
        pip install requests beautifulsoup4 lxml
        
        log_success "Environment setup complete"
        
        # Cleanup
        deactivate
        rm -rf test_venv
        ;;
        
    2)
        log_info "Testing network connectivity to: $GANCIO_BASE_URL"
        
        # Extract host and port
        HOST=$(echo "$GANCIO_BASE_URL" | sed -E 's|https?://([^/:]+).*|\1|')
        PORT=$(echo "$GANCIO_BASE_URL" | sed -E 's|.*:([0-9]+).*|\1|' | head -1)
        
        log_info "Host: $HOST, Port: $PORT"
        
        # Test ping
        if ping -c 2 -W 3 "$HOST" >/dev/null 2>&1; then
            log_success "Ping to $HOST successful"
        else
            log_warning "Ping to $HOST failed (may be blocked)"
        fi
        
        # Test port connectivity
        if timeout 5 bash -c "</dev/tcp/$HOST/$PORT" 2>/dev/null; then
            log_success "Port $PORT is accessible"
        else
            log_error "Port $PORT is not accessible"
        fi
        
        # Test HTTP
        if curl -I -s --max-time 10 "$GANCIO_BASE_URL" >/dev/null; then
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$GANCIO_BASE_URL")
            log_success "HTTP connection successful (Status: $HTTP_CODE)"
        else
            log_error "HTTP connection failed"
        fi
        
        # Test API
        if curl -I -s --max-time 10 "$GANCIO_BASE_URL/api/events" >/dev/null; then
            API_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$GANCIO_BASE_URL/api/events")
            log_success "API endpoint accessible (Status: $API_CODE)"
        else
            log_error "API endpoint not accessible"
        fi
        ;;
        
    3)
        log_info "Testing secrets and authentication..."
        
        # Run the validation script
        if [ -f "scripts/event-sync/validate_github_secrets.py" ]; then
            python3 scripts/event-sync/validate_github_secrets.py
        else
            log_error "validate_github_secrets.py not found"
        fi
        ;;
        
    4)
        log_info "Testing script execution..."
        
        # List available scripts
        log_info "Available scripts in scripts/event-sync/:"
        if [ -d "scripts/event-sync" ]; then
            ls -la scripts/event-sync/*.py
        else
            log_error "scripts/event-sync directory not found"
            exit 1
        fi
        
        # Check permissions
        log_info "Checking script permissions..."
        for script in scripts/event-sync/*.py; do
            if [ -x "$script" ]; then
                log_success "$(basename "$script") is executable"
            else
                log_warning "$(basename "$script") is not executable"
            fi
        done
        
        # Test syntax
        log_info "Testing Python syntax..."
        for script in scripts/event-sync/*.py; do
            if python3 -m py_compile "$script" 2>/dev/null; then
                log_success "$(basename "$script") syntax OK"
            else
                log_error "$(basename "$script") has syntax errors"
            fi
        done
        ;;
        
    5)
        log_info "Running full diagnostic suite..."
        
        if [ -f "scripts/event-sync/advanced_github_actions_debug.py" ]; then
            python3 scripts/event-sync/advanced_github_actions_debug.py
        else
            log_error "advanced_github_actions_debug.py not found"
        fi
        ;;
        
    6)
        log_info "Available Python scripts:"
        select script in scripts/event-sync/*.py; do
            if [ -n "$script" ]; then
                log_info "Running: $script"
                python3 "$script"
                break
            fi
        done
        ;;
        
    7)
        log_info "Installing act (GitHub Actions runner)..."
        
        if command -v act >/dev/null 2>&1; then
            log_success "act is already installed: $(act --version)"
        else
            log_info "Downloading and installing act..."
            if command -v curl >/dev/null 2>&1; then
                curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
                log_success "act installation complete"
                
                log_info "You can now run workflows locally with:"
                echo "  act workflow_dispatch -W .github/workflows/simple-diagnostic.yml"
            else
                log_error "curl not found - cannot install act"
            fi
        fi
        ;;
        
    8)
        log_info "Exiting local debug runner"
        exit 0
        ;;
        
    *)
        log_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
log_success "Local debugging session complete!"
log_info "Next steps:"
echo "- If issues were found, fix them and run again"
echo "- Test the actual GitHub Actions workflow"
echo "- Use the Emergency Debug workflow for live troubleshooting"
