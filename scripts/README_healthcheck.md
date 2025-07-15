# Admin Panel Health Check Script

This script performs comprehensive health checks on the admin panel to ensure all components are functioning correctly.

## Features

The health check script tests the following:

1. **API Health**: Verifies the admin API is running and responsive
2. **Database Connectivity**: Ensures the API can connect to the database
3. **Authentication Endpoints**: Tests all auth endpoints are accessible
4. **Rate Limiting**: Verifies rate limiting is active and working
5. **Static Files**: Checks that CSS and JS files are served correctly
6. **User Listing**: Tests that the user listing endpoint requires authentication

## Usage

### Basic Usage

```bash
# Check health of local admin panel (default: http://localhost:8000)
python scripts/check_admin_health.py

# Check health of remote admin panel
python scripts/check_admin_health.py --url https://admin.example.com

# Enable verbose output
python scripts/check_admin_health.py --verbose

# Output results as JSON
python scripts/check_admin_health.py --json

# Save report to file
python scripts/check_admin_health.py --output health_report.json
```

### Exit Codes

- `0`: All checks passed (HEALTHY)
- `1`: Some checks failed but service is operational (DEGRADED)
- `2`: Critical checks failed (UNHEALTHY)

### Example Output

```
Starting Admin Panel Health Checks...

[SUCCESS] API Health: Admin API is running and responsive
[SUCCESS] Database Connectivity: Database is accessible (authentication check completed)
[SUCCESS] Auth - Login Endpoint: Login endpoint is accessible and validating input
[SUCCESS] Auth - Refresh Endpoint: Refresh endpoint is accessible and validating tokens
[SUCCESS] Auth - Me Endpoint: Me endpoint is accessible and requires authentication
[SUCCESS] Rate Limiting: Rate limiting is active (triggered after 6 requests)
[SUCCESS] Static Files - CSS: CSS files are being served correctly
[SUCCESS] Static Files - JS: JavaScript files are being served correctly
[SUCCESS] User Listing - Authentication Required: User listing endpoint properly requires authentication
[SUCCESS] User Listing - Token Validation: User listing endpoint properly validates authentication tokens

============================================================
ADMIN PANEL HEALTH CHECK REPORT
============================================================
Timestamp: 2025-01-15T10:30:45.123456
Base URL: http://localhost:8000
Overall Status: HEALTHY
Health Score: 100.0%

Checks: 10 passed, 0 failed
============================================================
```

## Integration with CI/CD

You can integrate this health check into your deployment pipeline:

```bash
#!/bin/bash
# deployment_check.sh

# Run health check after deployment
python scripts/check_admin_health.py --url $ADMIN_URL --output health_report.json

# Check exit code
if [ $? -eq 0 ]; then
    echo "Deployment health check passed"
else
    echo "Deployment health check failed"
    cat health_report.json
    exit 1
fi
```

## Integration with Monitoring

The script can be used with monitoring tools:

```bash
# Run periodically via cron
*/5 * * * * /path/to/python /path/to/scripts/check_admin_health.py --url https://admin.example.com --json >> /var/log/admin_health.log 2>&1
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure the admin panel is running
   - Check the URL and port are correct
   - Verify firewall settings

2. **Database Connection Errors**
   - Check database credentials in configuration
   - Ensure database service is running
   - Verify network connectivity to database

3. **Rate Limiting Not Working**
   - Check rate limiting is enabled in configuration
   - Verify Redis is running (if using Redis backend)
   - Check rate limit settings are appropriate

4. **Static Files Not Found**
   - Verify static files directory exists
   - Check file permissions
   - Ensure static files are mounted correctly in the app

## Requirements

- Python 3.8+
- `requests` library (included in requirements.txt)

## Configuration

The script uses sensible defaults but can be customized via command-line arguments. No configuration file is needed.

## Development

To add new health checks:

1. Add a new method to the `HealthCheck` class
2. Call it from `run_all_checks()`
3. Update the documentation

Example:
```python
def check_custom_feature(self) -> bool:
    """Check if custom feature is working"""
    try:
        response = requests.get(f"{self.base_url}/api/custom", timeout=5)
        if response.status_code == 200:
            self.add_result("Custom Feature", True, "Feature is working")
            return True
        else:
            self.add_result("Custom Feature", False, f"Feature returned {response.status_code}")
            return False
    except Exception as e:
        self.add_result("Custom Feature", False, f"Error: {str(e)}")
        return False
```