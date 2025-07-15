#!/bin/bash

# ==============================================================================
# Admin Panel Setup Script
# ==============================================================================
# This script sets up the admin panel for the Diabetes Monitoring System.
# It performs the following tasks:
# 1. Checks prerequisites (Python, MySQL, venv)
# 2. Generates a secure ADMIN_SECRET_KEY if not set
# 3. Runs database migrations for admin tables
# 4. Prompts to create the first admin user
# 5. Shows next steps for running the admin panel
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo
    echo "=============================================================="
    echo "$1"
    echo "=============================================================="
    echo
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to generate a secure secret key
generate_secret_key() {
    python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
}

# Function to check MySQL connection
check_mysql_connection() {
    print_info "Checking MySQL connection..."
    
    # Load environment variables
    if [ -f "$PROJECT_ROOT/.env" ]; then
        source "$PROJECT_ROOT/.env"
    fi
    
    # Set defaults if not in env
    DB_HOST="${DB_HOST:-localhost}"
    DB_USER="${DB_USER:-root}"
    DB_PASSWORD="${DB_PASSWORD:-}"
    DB_NAME="${DB_NAME:-diabetes_monitoring}"
    
    # Test connection using Python
    python3 -c "
import os
import sys
sys.path.append('$PROJECT_ROOT')
try:
    from database.database import test_connection
    if test_connection():
        print('MySQL connection successful')
        sys.exit(0)
    else:
        print('MySQL connection failed')
        sys.exit(1)
except Exception as e:
    print(f'MySQL connection error: {e}')
    sys.exit(1)
" 2>&1
    
    return $?
}

# Function to check and update .env file
update_env_file() {
    local env_file="$PROJECT_ROOT/.env"
    local env_updated=false
    
    # Create .env if it doesn't exist
    if [ ! -f "$env_file" ]; then
        print_info "Creating .env file..."
        touch "$env_file"
    fi
    
    # Check if SECRET_KEY exists
    if ! grep -q "^SECRET_KEY=" "$env_file"; then
        print_info "Generating secure SECRET_KEY..."
        local secret_key=$(generate_secret_key)
        echo "SECRET_KEY=$secret_key" >> "$env_file"
        env_updated=true
        print_success "SECRET_KEY generated and added to .env"
    else
        print_info "SECRET_KEY already exists in .env"
    fi
    
    # Check for required environment variables
    local required_vars=(
        "DB_HOST"
        "DB_USER"
        "DB_NAME"
        "ENVIRONMENT"
    )
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" "$env_file"; then
            case $var in
                "DB_HOST")
                    echo "DB_HOST=localhost" >> "$env_file"
                    print_warning "Added default DB_HOST=localhost to .env"
                    ;;
                "DB_USER")
                    echo "DB_USER=root" >> "$env_file"
                    print_warning "Added default DB_USER=root to .env"
                    ;;
                "DB_NAME")
                    echo "DB_NAME=diabetes_monitoring" >> "$env_file"
                    print_warning "Added default DB_NAME=diabetes_monitoring to .env"
                    ;;
                "ENVIRONMENT")
                    echo "ENVIRONMENT=DEV" >> "$env_file"
                    print_warning "Added default ENVIRONMENT=DEV to .env"
                    ;;
            esac
            env_updated=true
        fi
    done
    
    if [ "$env_updated" = true ]; then
        echo
        print_warning "Please review and update the .env file with your actual values!"
        print_info "Edit: $env_file"
        echo
    fi
}

# Main setup process
main() {
    print_header "ADMIN PANEL SETUP SCRIPT"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Step 1: Check prerequisites
    print_header "Step 1: Checking Prerequisites"
    
    # Check Python
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python $python_version found"
    
    # Check if venv exists
    if [ ! -d "$PROJECT_ROOT/venv" ]; then
        print_error "Virtual environment not found!"
        print_info "Please run the following command first:"
        echo "  python3 -m venv venv"
        exit 1
    fi
    print_success "Virtual environment found"
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source "$PROJECT_ROOT/venv/bin/activate"
    print_success "Virtual environment activated"
    
    # Check if requirements are installed
    if ! python3 -c "import sqlalchemy" 2>/dev/null; then
        print_warning "Dependencies not installed. Installing requirements..."
        pip install -r "$PROJECT_ROOT/requirements.txt"
        print_success "Dependencies installed"
    else
        print_success "Dependencies already installed"
    fi
    
    # Step 2: Generate/Check SECRET_KEY
    print_header "Step 2: Checking Environment Configuration"
    update_env_file
    
    # Step 3: Check MySQL connection
    print_header "Step 3: Database Connection"
    if ! check_mysql_connection; then
        print_error "Failed to connect to MySQL database!"
        print_info "Please ensure MySQL is running and check your database credentials in .env"
        print_info "Required variables: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME"
        exit 1
    fi
    print_success "MySQL connection successful"
    
    # Step 4: Run database migrations
    print_header "Step 4: Database Migrations"
    
    # Check if alembic is configured
    if [ ! -f "$PROJECT_ROOT/alembic.ini" ]; then
        print_error "Alembic configuration not found!"
        exit 1
    fi
    
    # Check if admin tables migration exists
    if ls "$PROJECT_ROOT/alembic/versions/"*add_admin_tables*.py 1> /dev/null 2>&1; then
        print_info "Running database migrations..."
        
        # Run migrations
        if alembic upgrade head; then
            print_success "Database migrations completed successfully"
        else
            print_error "Database migration failed!"
            print_info "You may need to check your database connection or migration files"
            exit 1
        fi
    else
        print_warning "Admin tables migration not found!"
        print_info "Creating admin tables migration..."
        
        # Generate migration
        alembic revision --autogenerate -m "add_admin_tables"
        
        print_info "Migration created. Running upgrade..."
        alembic upgrade head
        print_success "Admin tables created successfully"
    fi
    
    # Step 5: Create first admin user
    print_header "Step 5: Admin User Creation"
    
    # Check if admin users exist
    admin_exists=$(python3 -c "
import sys
sys.path.append('$PROJECT_ROOT')
from sqlalchemy.orm import Session
from database.database import SessionLocal
from admin.models.admin import AdminUser
try:
    db = SessionLocal()
    count = db.query(AdminUser).count()
    db.close()
    print(count)
except:
    print(0)
")
    
    if [ "$admin_exists" -eq 0 ]; then
        print_info "No admin users found in the database."
        echo
        read -p "Would you like to create the first superadmin user now? (yes/no): " create_admin
        
        if [ "$create_admin" = "yes" ]; then
            python3 "$PROJECT_ROOT/scripts/create_admin_user.py"
        else
            print_warning "Skipping admin user creation."
            print_info "You can create an admin user later by running:"
            echo "  python scripts/create_admin_user.py"
        fi
    else
        print_info "Found $admin_exists existing admin user(s)"
        echo
        read -p "Would you like to create another admin user? (yes/no): " create_another
        
        if [ "$create_another" = "yes" ]; then
            python3 "$PROJECT_ROOT/scripts/create_admin_user.py"
        fi
    fi
    
    # Step 6: Show next steps
    print_header "Setup Complete!"
    
    print_success "Admin panel setup completed successfully!"
    echo
    print_info "Next steps to run the admin panel:"
    echo
    echo "  1. Activate the virtual environment:"
    echo "     source venv/bin/activate"
    echo
    echo "  2. Run the admin panel:"
    echo "     python run_admin.py"
    echo
    echo "  3. Access the admin panel:"
    echo "     http://localhost:8000"
    echo "     http://localhost:8000/admin"
    echo
    echo "  4. Login with the admin credentials you created"
    echo
    print_info "Additional commands:"
    echo "  - Create another admin user: python scripts/create_admin_user.py"
    echo "  - Run database migrations: alembic upgrade head"
    echo "  - Check migration status: alembic current"
    echo
    
    # Check if running in production
    if grep -q "ENVIRONMENT=PROD" "$PROJECT_ROOT/.env" 2>/dev/null; then
        print_warning "Production mode detected!"
        echo "  - Ensure SESSION_COOKIE_SECURE=True for HTTPS"
        echo "  - Configure proper CORS_ORIGINS"
        echo "  - Use a production-grade server (e.g., Gunicorn with Nginx)"
        echo "  - Set up SSL/TLS certificates"
    fi
}

# Run main function
main