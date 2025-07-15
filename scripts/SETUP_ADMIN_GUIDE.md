# Admin Panel Setup Guide

## Overview

The `setup_admin.sh` script provides a comprehensive setup process for the admin panel of the Diabetes Monitoring System. It automates the configuration and initialization steps required to get the admin panel up and running.

## What the Script Does

1. **Prerequisites Check**
   - Verifies Python 3 installation
   - Checks for virtual environment
   - Installs required dependencies

2. **Environment Configuration**
   - Generates a secure `SECRET_KEY` if not present
   - Creates/updates `.env` file with required variables
   - Validates environment settings

3. **Database Setup**
   - Tests MySQL connection
   - Runs Alembic migrations for admin tables
   - Creates database schema if needed

4. **Admin User Creation**
   - Detects existing admin users
   - Offers to create the first superadmin
   - Validates user input and password strength

5. **Next Steps Guidance**
   - Provides clear instructions for running the admin panel
   - Shows relevant commands and URLs
   - Warns about production-specific settings

## Prerequisites

Before running the setup script, ensure you have:

1. **Python 3.8+** installed
2. **MySQL Server** running and accessible
3. **Virtual environment** created:
   ```bash
   python3 -m venv venv
   ```

## Running the Setup Script

```bash
# Navigate to the scripts directory
cd /path/to/erasmus/scripts

# Run the setup script
./setup_admin.sh
```

## Environment Variables

The script will check for and create these variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key (auto-generated) | Generated |
| `DB_HOST` | MySQL host | localhost |
| `DB_USER` | MySQL username | root |
| `DB_PASSWORD` | MySQL password | (empty) |
| `DB_NAME` | Database name | diabetes_monitoring |
| `ENVIRONMENT` | DEV or PROD | DEV |

## Manual Setup Steps

If you prefer to set up manually or the script encounters issues:

### 1. Environment Setup
```bash
# Create .env file
cp .env.example .env  # if example exists

# Generate SECRET_KEY
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'

# Add to .env
echo "SECRET_KEY=your-generated-key" >> .env
```

### 2. Database Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head
```

### 3. Create Admin User
```bash
python scripts/create_admin_user.py
```

### 4. Run Admin Panel
```bash
python run_admin.py
```

## Troubleshooting

### MySQL Connection Issues
- Verify MySQL is running: `mysql.server status`
- Check credentials in `.env`
- Ensure database exists or user has CREATE privileges

### Migration Errors
- Check current migration status: `alembic current`
- View migration history: `alembic history`
- Downgrade if needed: `alembic downgrade -1`

### Virtual Environment Issues
- Recreate venv: `rm -rf venv && python3 -m venv venv`
- Reinstall dependencies: `pip install -r requirements.txt`

### Permission Errors
- Make script executable: `chmod +x setup_admin.sh`
- Run with proper permissions for MySQL access

## Security Considerations

### Development Environment
- Default settings are suitable for local development
- `SESSION_COOKIE_SECURE=False` allows HTTP access

### Production Environment
- Set `ENVIRONMENT=PROD` in `.env`
- Use strong `DB_PASSWORD`
- Enable `SESSION_COOKIE_SECURE=True` for HTTPS
- Configure proper `CORS_ORIGINS`
- Use production server (Gunicorn/Nginx)
- Set up SSL/TLS certificates

## Post-Setup Tasks

1. **Test Admin Access**
   - Navigate to http://localhost:8000/admin
   - Login with created credentials

2. **Configure Additional Settings**
   - Review `admin/core/config.py`
   - Adjust pagination, upload limits, etc.

3. **Set Up Monitoring**
   - Check audit logs regularly
   - Monitor failed login attempts
   - Review user activities

## Related Scripts

- `create_admin_user.py` - Create additional admin users
- `setup_database.py` - Database initialization only
- `data_export.py` - Export system data

## Support

For issues or questions:
1. Check error messages in terminal
2. Review logs in application
3. Verify all prerequisites are met
4. Ensure environment variables are correct