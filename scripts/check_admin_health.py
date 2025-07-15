#!/usr/bin/env python3
"""
Admin Panel Health Check Script

This script performs comprehensive health checks on the admin panel to ensure:
1. Admin API is running and responsive
2. Database connectivity is working
3. Authentication endpoints are functional
4. Rate limiting is active and working
5. Static files are being served correctly
6. User listing endpoint is accessible

Usage:
    python scripts/check_admin_health.py [--url http://localhost:8000] [--verbose]
"""

import sys
import time
import json
import argparse
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException
from urllib.parse import urljoin

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class HealthCheck:
    """Admin Panel Health Check"""
    
    def __init__(self, base_url: str, verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        self.results = []
        self.errors = []
        self.warnings = []
        self.access_token = None
        self.refresh_token = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with appropriate formatting"""
        if level == "ERROR":
            print(f"{Colors.RED}[ERROR]{Colors.ENDC} {message}")
        elif level == "WARNING":
            print(f"{Colors.YELLOW}[WARNING]{Colors.ENDC} {message}")
        elif level == "SUCCESS":
            print(f"{Colors.GREEN}[SUCCESS]{Colors.ENDC} {message}")
        elif level == "INFO":
            print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {message}")
        else:
            print(f"[{level}] {message}")
    
    def add_result(self, check_name: str, status: bool, message: str, details: Optional[Dict] = None):
        """Add a check result"""
        result = {
            "check": check_name,
            "status": "PASS" if status else "FAIL",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        if details:
            result["details"] = details
        
        self.results.append(result)
        
        if status:
            self.log(f"{check_name}: {message}", "SUCCESS")
        else:
            self.log(f"{check_name}: {message}", "ERROR")
            self.errors.append(f"{check_name}: {message}")
        
        if self.verbose and details:
            print(f"  Details: {json.dumps(details, indent=2)}")
    
    def check_api_health(self) -> bool:
        """Check if the admin API is running"""
        try:
            response = requests.get(
                f"{self.base_url}/api/health",
                timeout=5
            )
            
            if response.status_code == 200:
                self.add_result(
                    "API Health",
                    True,
                    "Admin API is running and responsive",
                    {"status_code": response.status_code, "response_time_ms": int(response.elapsed.total_seconds() * 1000)}
                )
                return True
            elif response.status_code == 404:
                # Health endpoint might not exist, try home page
                home_response = requests.get(f"{self.base_url}/", timeout=5)
                if home_response.status_code == 200:
                    self.add_result(
                        "API Health",
                        True,
                        "Admin API is running (health endpoint not found, but home page responsive)",
                        {"status_code": home_response.status_code}
                    )
                    return True
            
            self.add_result(
                "API Health",
                False,
                f"Admin API returned unexpected status code: {response.status_code}",
                {"status_code": response.status_code}
            )
            return False
            
        except ConnectionError:
            self.add_result(
                "API Health",
                False,
                f"Cannot connect to admin API at {self.base_url}",
                {"error": "Connection refused or host unreachable"}
            )
            return False
        except Timeout:
            self.add_result(
                "API Health",
                False,
                "Admin API request timed out",
                {"error": "Request timeout after 5 seconds"}
            )
            return False
        except Exception as e:
            self.add_result(
                "API Health",
                False,
                f"Unexpected error checking API health: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def check_database_connectivity(self) -> bool:
        """Check database connectivity via the API"""
        # Most APIs expose database health through endpoints
        # We'll try to access an endpoint that requires database
        try:
            # Try to access login endpoint with invalid credentials
            # This will test database connectivity without needing valid credentials
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": "health_check_test", "password": "invalid"},
                timeout=5
            )
            
            # We expect 401 (unauthorized) which means the API could check the database
            if response.status_code == 401:
                self.add_result(
                    "Database Connectivity",
                    True,
                    "Database is accessible (authentication check completed)",
                    {"status_code": response.status_code}
                )
                return True
            elif response.status_code == 500:
                self.add_result(
                    "Database Connectivity",
                    False,
                    "Database connection error (500 Internal Server Error)",
                    {"status_code": response.status_code}
                )
                return False
            else:
                self.add_result(
                    "Database Connectivity",
                    True,
                    f"Database appears accessible (status: {response.status_code})",
                    {"status_code": response.status_code}
                )
                return True
                
        except Exception as e:
            self.add_result(
                "Database Connectivity",
                False,
                f"Error checking database connectivity: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def check_authentication_endpoints(self) -> bool:
        """Test authentication endpoints"""
        all_good = True
        
        # Check login endpoint exists
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": "", "password": ""},
                timeout=5
            )
            
            if response.status_code in [400, 401, 422]:  # Expected for invalid input
                self.add_result(
                    "Auth - Login Endpoint",
                    True,
                    "Login endpoint is accessible and validating input",
                    {"status_code": response.status_code}
                )
            else:
                self.add_result(
                    "Auth - Login Endpoint",
                    False,
                    f"Login endpoint returned unexpected status: {response.status_code}",
                    {"status_code": response.status_code}
                )
                all_good = False
                
        except Exception as e:
            self.add_result(
                "Auth - Login Endpoint",
                False,
                f"Error accessing login endpoint: {str(e)}",
                {"error": str(e)}
            )
            all_good = False
        
        # Check refresh endpoint exists
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/refresh",
                json={"refresh_token": "invalid_token"},
                timeout=5
            )
            
            if response.status_code in [401, 422]:  # Expected for invalid token
                self.add_result(
                    "Auth - Refresh Endpoint",
                    True,
                    "Refresh endpoint is accessible and validating tokens",
                    {"status_code": response.status_code}
                )
            else:
                self.add_result(
                    "Auth - Refresh Endpoint",
                    False,
                    f"Refresh endpoint returned unexpected status: {response.status_code}",
                    {"status_code": response.status_code}
                )
                all_good = False
                
        except Exception as e:
            self.add_result(
                "Auth - Refresh Endpoint",
                False,
                f"Error accessing refresh endpoint: {str(e)}",
                {"error": str(e)}
            )
            all_good = False
        
        # Check me endpoint exists (requires auth)
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/auth/me",
                headers={"Authorization": "Bearer invalid_token"},
                timeout=5
            )
            
            if response.status_code == 401:  # Expected for invalid token
                self.add_result(
                    "Auth - Me Endpoint",
                    True,
                    "Me endpoint is accessible and requires authentication",
                    {"status_code": response.status_code}
                )
            else:
                self.add_result(
                    "Auth - Me Endpoint",
                    False,
                    f"Me endpoint returned unexpected status: {response.status_code}",
                    {"status_code": response.status_code}
                )
                all_good = False
                
        except Exception as e:
            self.add_result(
                "Auth - Me Endpoint",
                False,
                f"Error accessing me endpoint: {str(e)}",
                {"error": str(e)}
            )
            all_good = False
        
        return all_good
    
    def check_rate_limiting(self) -> bool:
        """Check if rate limiting is working"""
        # Try to trigger rate limiting on login endpoint
        login_url = f"{self.base_url}/api/v1/auth/login"
        
        # Make multiple rapid requests
        request_count = 0
        rate_limited = False
        
        try:
            # According to config, login limit is 5 per minute
            for i in range(10):
                response = requests.post(
                    login_url,
                    json={"username": "rate_limit_test", "password": "test"},
                    timeout=2
                )
                request_count += 1
                
                if response.status_code == 429:
                    rate_limited = True
                    retry_after = response.headers.get('Retry-After', 'Not specified')
                    self.add_result(
                        "Rate Limiting",
                        True,
                        f"Rate limiting is active (triggered after {request_count} requests)",
                        {
                            "requests_before_limit": request_count,
                            "retry_after": retry_after,
                            "status_code": 429
                        }
                    )
                    break
                
                # Small delay to ensure we don't DOS the server
                time.sleep(0.1)
            
            if not rate_limited:
                self.warnings.append("Rate limiting might not be properly configured")
                self.add_result(
                    "Rate Limiting",
                    False,
                    f"Rate limiting not triggered after {request_count} rapid requests",
                    {"requests_made": request_count}
                )
                return False
            
            return True
            
        except Exception as e:
            self.add_result(
                "Rate Limiting",
                False,
                f"Error testing rate limiting: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def check_static_files(self) -> bool:
        """Check if static files are being served"""
        all_good = True
        
        # Check CSS file
        try:
            response = requests.get(
                f"{self.base_url}/static/css/style.css",
                timeout=5
            )
            
            if response.status_code == 200:
                self.add_result(
                    "Static Files - CSS",
                    True,
                    "CSS files are being served correctly",
                    {"status_code": 200, "content_type": response.headers.get('Content-Type', 'Not specified')}
                )
            else:
                self.add_result(
                    "Static Files - CSS",
                    False,
                    f"CSS file not accessible (status: {response.status_code})",
                    {"status_code": response.status_code}
                )
                all_good = False
                
        except Exception as e:
            self.add_result(
                "Static Files - CSS",
                False,
                f"Error accessing CSS file: {str(e)}",
                {"error": str(e)}
            )
            all_good = False
        
        # Check JS file
        try:
            response = requests.get(
                f"{self.base_url}/static/js/main.js",
                timeout=5
            )
            
            if response.status_code == 200:
                self.add_result(
                    "Static Files - JS",
                    True,
                    "JavaScript files are being served correctly",
                    {"status_code": 200, "content_type": response.headers.get('Content-Type', 'Not specified')}
                )
            else:
                self.add_result(
                    "Static Files - JS",
                    False,
                    f"JS file not accessible (status: {response.status_code})",
                    {"status_code": response.status_code}
                )
                all_good = False
                
        except Exception as e:
            self.add_result(
                "Static Files - JS",
                False,
                f"Error accessing JS file: {str(e)}",
                {"error": str(e)}
            )
            all_good = False
        
        return all_good
    
    def check_user_listing_endpoint(self) -> bool:
        """Test user listing endpoint (requires authentication)"""
        try:
            # First, try without authentication to ensure it's protected
            response = requests.get(
                f"{self.base_url}/api/v1/users/",
                timeout=5
            )
            
            if response.status_code == 401:
                self.add_result(
                    "User Listing - Authentication Required",
                    True,
                    "User listing endpoint properly requires authentication",
                    {"status_code": 401}
                )
                
                # Try with invalid token to test auth validation
                response = requests.get(
                    f"{self.base_url}/api/v1/users/",
                    headers={"Authorization": "Bearer invalid_token"},
                    timeout=5
                )
                
                if response.status_code == 401:
                    self.add_result(
                        "User Listing - Token Validation",
                        True,
                        "User listing endpoint properly validates authentication tokens",
                        {"status_code": 401}
                    )
                    return True
                else:
                    self.add_result(
                        "User Listing - Token Validation",
                        False,
                        f"Unexpected response with invalid token: {response.status_code}",
                        {"status_code": response.status_code}
                    )
                    return False
            else:
                self.add_result(
                    "User Listing - Authentication Required",
                    False,
                    f"User listing endpoint accessible without authentication (status: {response.status_code})",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.add_result(
                "User Listing Endpoint",
                False,
                f"Error accessing user listing endpoint: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def generate_report(self) -> Dict:
        """Generate a comprehensive health report"""
        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results if r["status"] == "PASS")
        failed_checks = total_checks - passed_checks
        
        health_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        if health_score == 100:
            overall_status = "HEALTHY"
        elif health_score >= 80:
            overall_status = "DEGRADED"
        else:
            overall_status = "UNHEALTHY"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "overall_status": overall_status,
            "health_score": round(health_score, 2),
            "summary": {
                "total_checks": total_checks,
                "passed": passed_checks,
                "failed": failed_checks
            },
            "results": self.results,
            "errors": self.errors,
            "warnings": self.warnings
        }
        
        return report
    
    def print_summary(self, report: Dict):
        """Print a formatted summary of the health check"""
        print("\n" + "="*60)
        print(f"{Colors.BOLD}ADMIN PANEL HEALTH CHECK REPORT{Colors.ENDC}")
        print("="*60)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Base URL: {report['base_url']}")
        print(f"Overall Status: ", end="")
        
        if report['overall_status'] == 'HEALTHY':
            print(f"{Colors.GREEN}{report['overall_status']}{Colors.ENDC}")
        elif report['overall_status'] == 'DEGRADED':
            print(f"{Colors.YELLOW}{report['overall_status']}{Colors.ENDC}")
        else:
            print(f"{Colors.RED}{report['overall_status']}{Colors.ENDC}")
        
        print(f"Health Score: {report['health_score']}%")
        print(f"\nChecks: {report['summary']['passed']} passed, {report['summary']['failed']} failed")
        
        if report['errors']:
            print(f"\n{Colors.RED}Errors:{Colors.ENDC}")
            for error in report['errors']:
                print(f"  - {error}")
        
        if report['warnings']:
            print(f"\n{Colors.YELLOW}Warnings:{Colors.ENDC}")
            for warning in report['warnings']:
                print(f"  - {warning}")
        
        print("\n" + "="*60)
        
        # Recommendations
        if report['overall_status'] != 'HEALTHY':
            print(f"\n{Colors.BOLD}RECOMMENDATIONS:{Colors.ENDC}")
            
            if any("API Health" in error for error in report['errors']):
                print("- Ensure the admin panel is running and accessible")
                print(f"- Check if the service is running on {report['base_url']}")
                print("- Verify firewall settings if running remotely")
            
            if any("Database" in error for error in report['errors']):
                print("- Check database connection settings in configuration")
                print("- Ensure database service is running")
                print("- Verify database credentials")
            
            if any("Rate Limiting" in error for error in report['errors']):
                print("- Check rate limiting configuration")
                print("- Ensure rate limiting middleware is properly initialized")
            
            if any("Static Files" in error for error in report['errors']):
                print("- Verify static files directory exists and has correct permissions")
                print("- Check static files mounting in the application")
        
        print("")
    
    def run_all_checks(self) -> Dict:
        """Run all health checks"""
        print(f"\n{Colors.BOLD}Starting Admin Panel Health Checks...{Colors.ENDC}\n")
        
        # Check if API is running first
        if not self.check_api_health():
            self.log("API is not accessible. Skipping remaining checks.", "WARNING")
            report = self.generate_report()
            self.print_summary(report)
            return report
        
        # Run remaining checks
        self.check_database_connectivity()
        self.check_authentication_endpoints()
        self.check_rate_limiting()
        self.check_static_files()
        self.check_user_listing_endpoint()
        
        # Generate and display report
        report = self.generate_report()
        self.print_summary(report)
        
        return report


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Admin Panel Health Check")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the admin panel (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--output",
        help="Save report to file"
    )
    
    args = parser.parse_args()
    
    # Run health checks
    checker = HealthCheck(args.url, args.verbose)
    report = checker.run_all_checks()
    
    # Save report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {args.output}")
    
    # Output JSON if requested
    if args.json:
        print("\nJSON Report:")
        print(json.dumps(report, indent=2))
    
    # Exit with appropriate code
    if report['overall_status'] == 'HEALTHY':
        sys.exit(0)
    elif report['overall_status'] == 'DEGRADED':
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()