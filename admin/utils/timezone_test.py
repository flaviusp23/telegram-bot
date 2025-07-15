"""
Timezone debugging utility for admin panel
"""
from datetime import datetime, timezone
import pytz

def test_timezone_handling():
    """Test and display timezone information"""
    
    # Current times in different formats
    naive_now = datetime.now()
    utc_now = datetime.now(timezone.utc)
    
    print("=== Timezone Test Results ===")
    print(f"Naive datetime.now(): {naive_now}")
    print(f"UTC datetime.now(timezone.utc): {utc_now}")
    print(f"Naive as ISO: {naive_now.isoformat()}")
    print(f"UTC as ISO: {utc_now.isoformat()}")
    
    # Test MySQL-style timestamp
    mysql_timestamp = "2025-01-15 14:30:00"
    
    # Parse as naive (what was happening before)
    naive_parsed = datetime.fromisoformat(mysql_timestamp)
    print(f"\nMySQL timestamp '{mysql_timestamp}' parsed as naive: {naive_parsed}")
    
    # Parse as UTC (what should happen)
    utc_parsed = datetime.fromisoformat(mysql_timestamp + "+00:00")
    print(f"MySQL timestamp '{mysql_timestamp}' parsed as UTC: {utc_parsed}")
    
    # Show the difference
    print(f"Difference: {naive_parsed - utc_parsed.replace(tzinfo=None)}")
    
    # Test JavaScript compatibility
    js_compatible = utc_now.isoformat().replace('+00:00', 'Z')
    print(f"\nJavaScript compatible UTC format: {js_compatible}")
    
    return {
        "naive_now": naive_now.isoformat(),
        "utc_now": utc_now.isoformat(),
        "js_compatible": js_compatible
    }

if __name__ == "__main__":
    test_timezone_handling()