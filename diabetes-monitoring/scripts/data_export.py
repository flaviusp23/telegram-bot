"""Data export script for diabetes monitoring system"""
import os
import sys
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal, get_user_by_telegram_id, get_user_responses
from database.models import User, Response
from sqlalchemy import func, and_

# For graphs, we'll add matplotlib when needed
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    GRAPHS_AVAILABLE = True
except ImportError:
    GRAPHS_AVAILABLE = False
    print("Warning: matplotlib not installed. Graphs will not be generated.")
    print("Install with: pip install matplotlib")

class DataExporter:
    """Export user data to various formats"""
    
    def __init__(self, db_session):
        self.db = db_session
        
    def get_user_statistics(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate statistics for a user"""
        responses = self.db.query(Response).filter(
            and_(
                Response.user_id == user_id,
                Response.response_timestamp >= start_date,
                Response.response_timestamp <= end_date
            )
        ).all()
        
        # Separate distress checks and severity ratings
        distress_checks = [r for r in responses if r.question_type == 'distress_check']
        severity_ratings = [r for r in responses if r.question_type == 'severity_rating']
        
        # Calculate statistics
        total_checks = len(distress_checks)
        distress_count = sum(1 for r in distress_checks if r.response_value == 'yes')
        no_distress_count = total_checks - distress_count
        
        # Severity statistics
        severities = [int(r.response_value) for r in severity_ratings]
        avg_severity = sum(severities) / len(severities) if severities else 0
        max_severity = max(severities) if severities else 0
        min_severity = min(severities) if severities else 0
        
        # Response rate (assuming 3 alerts per day)
        days = (end_date - start_date).days + 1
        expected_responses = days * 3
        response_rate = (total_checks / expected_responses * 100) if expected_responses > 0 else 0
        
        return {
            'total_responses': total_checks,
            'distress_count': distress_count,
            'no_distress_count': no_distress_count,
            'distress_percentage': (distress_count / total_checks * 100) if total_checks > 0 else 0,
            'average_severity': round(avg_severity, 2),
            'max_severity': max_severity,
            'min_severity': min_severity,
            'response_rate': round(response_rate, 2),
            'severity_distribution': self._get_severity_distribution(severities)
        }
    
    def _get_severity_distribution(self, severities: List[int]) -> Dict[int, int]:
        """Get distribution of severity ratings"""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for severity in severities:
            if severity in distribution:
                distribution[severity] += 1
        return distribution
    
    def export_to_xml(self, user_id: int, start_date: datetime, end_date: datetime, output_file: str):
        """Export user data to XML format"""
        # Get user info
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Create root element
        root = ET.Element("DiabetesMonitoringExport")
        root.set("generated", datetime.now().isoformat())
        root.set("version", "1.0")
        
        # User information
        user_elem = ET.SubElement(root, "User")
        ET.SubElement(user_elem, "ID").text = str(user.id)
        ET.SubElement(user_elem, "FirstName").text = user.first_name
        ET.SubElement(user_elem, "FamilyName").text = user.family_name
        ET.SubElement(user_elem, "TelegramID").text = user.telegram_id
        ET.SubElement(user_elem, "Status").text = user.status.value
        ET.SubElement(user_elem, "RegistrationDate").text = user.registration_date.isoformat()
        
        # Export period
        period_elem = ET.SubElement(root, "ExportPeriod")
        ET.SubElement(period_elem, "StartDate").text = start_date.isoformat()
        ET.SubElement(period_elem, "EndDate").text = end_date.isoformat()
        
        # Statistics
        stats = self.get_user_statistics(user_id, start_date, end_date)
        stats_elem = ET.SubElement(root, "Statistics")
        ET.SubElement(stats_elem, "TotalResponses").text = str(stats['total_responses'])
        ET.SubElement(stats_elem, "DistressCount").text = str(stats['distress_count'])
        ET.SubElement(stats_elem, "NoDistressCount").text = str(stats['no_distress_count'])
        ET.SubElement(stats_elem, "DistressPercentage").text = f"{stats['distress_percentage']:.2f}"
        ET.SubElement(stats_elem, "AverageSeverity").text = str(stats['average_severity'])
        ET.SubElement(stats_elem, "MaxSeverity").text = str(stats['max_severity'])
        ET.SubElement(stats_elem, "MinSeverity").text = str(stats['min_severity'])
        ET.SubElement(stats_elem, "ResponseRate").text = f"{stats['response_rate']:.2f}"
        
        # Severity distribution
        dist_elem = ET.SubElement(stats_elem, "SeverityDistribution")
        for level, count in stats['severity_distribution'].items():
            level_elem = ET.SubElement(dist_elem, "Level")
            level_elem.set("value", str(level))
            level_elem.text = str(count)
        
        # Responses
        responses_elem = ET.SubElement(root, "Responses")
        responses = self.db.query(Response).filter(
            and_(
                Response.user_id == user_id,
                Response.response_timestamp >= start_date,
                Response.response_timestamp <= end_date
            )
        ).order_by(Response.response_timestamp).all()
        
        for response in responses:
            resp_elem = ET.SubElement(responses_elem, "Response")
            ET.SubElement(resp_elem, "ID").text = str(response.id)
            ET.SubElement(resp_elem, "Timestamp").text = response.response_timestamp.isoformat()
            ET.SubElement(resp_elem, "QuestionType").text = response.question_type
            ET.SubElement(resp_elem, "ResponseValue").text = response.response_value
        
        # Pretty print and save
        self._indent_xml(root)
        tree = ET.ElementTree(root)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
        return stats
    
    def _indent_xml(self, elem, level=0):
        """Add pretty-printing to XML"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self._indent_xml(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def generate_graphs(self, user_id: int, start_date: datetime, end_date: datetime, output_dir: str):
        """Generate graphs for user data"""
        if not GRAPHS_AVAILABLE:
            print("Error: matplotlib not installed. Cannot generate graphs.")
            return
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Get user and responses
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        responses = self.db.query(Response).filter(
            and_(
                Response.user_id == user_id,
                Response.response_timestamp >= start_date,
                Response.response_timestamp <= end_date
            )
        ).order_by(Response.response_timestamp).all()
        
        # 1. Distress over time graph
        self._generate_distress_timeline(responses, user, output_dir)
        
        # 2. Severity distribution pie chart
        self._generate_severity_distribution(responses, user, output_dir)
        
        # 3. Daily response rate
        self._generate_response_rate(responses, user, start_date, end_date, output_dir)
        
        # 4. Severity trend line
        self._generate_severity_trend(responses, user, output_dir)
        
        print(f"Graphs generated in: {output_dir}")
    
    def _generate_distress_timeline(self, responses: List[Response], user: User, output_dir: str):
        """Generate distress timeline graph"""
        distress_data = [(r.response_timestamp, 1 if r.response_value == 'yes' else 0) 
                        for r in responses if r.question_type == 'distress_check']
        
        if not distress_data:
            return
        
        dates, values = zip(*distress_data)
        
        plt.figure(figsize=(12, 6))
        plt.scatter(dates, values, alpha=0.6, s=100)
        plt.plot(dates, values, alpha=0.3)
        
        plt.title(f'Distress Check Timeline - {user.first_name} {user.family_name}')
        plt.xlabel('Date')
        plt.ylabel('Distress (0=No, 1=Yes)')
        plt.ylim(-0.1, 1.1)
        plt.yticks([0, 1], ['No', 'Yes'])
        
        # Format x-axis
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'distress_timeline.png'))
        plt.close()
    
    def _generate_severity_distribution(self, responses: List[Response], user: User, output_dir: str):
        """Generate severity distribution pie chart"""
        severities = [int(r.response_value) for r in responses if r.question_type == 'severity_rating']
        
        if not severities:
            return
        
        distribution = self._get_severity_distribution(severities)
        
        # Filter out zero counts
        labels = []
        sizes = []
        colors = ['#2ecc71', '#f1c40f', '#e67e22', '#e74c3c', '#c0392b']
        
        for level, count in distribution.items():
            if count > 0:
                labels.append(f'Level {level}')
                sizes.append(count)
        
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, colors=colors[:len(labels)], autopct='%1.1f%%', startangle=90)
        plt.title(f'Severity Distribution - {user.first_name} {user.family_name}')
        plt.axis('equal')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'severity_distribution.png'))
        plt.close()
    
    def _generate_response_rate(self, responses: List[Response], user: User, start_date: datetime, end_date: datetime, output_dir: str):
        """Generate daily response rate graph"""
        # Group responses by date
        response_counts = {}
        for r in responses:
            if r.question_type == 'distress_check':
                date = r.response_timestamp.date()
                response_counts[date] = response_counts.get(date, 0) + 1
        
        # Generate all dates in range
        current_date = start_date.date()
        end = end_date.date()
        dates = []
        rates = []
        
        while current_date <= end:
            dates.append(current_date)
            count = response_counts.get(current_date, 0)
            rate = (count / 3) * 100  # 3 expected per day
            rates.append(min(rate, 100))  # Cap at 100%
            current_date += timedelta(days=1)
        
        plt.figure(figsize=(12, 6))
        plt.bar(dates, rates, alpha=0.7, color='#3498db')
        plt.axhline(y=100, color='r', linestyle='--', alpha=0.5, label='Expected (100%)')
        
        plt.title(f'Daily Response Rate - {user.first_name} {user.family_name}')
        plt.xlabel('Date')
        plt.ylabel('Response Rate (%)')
        plt.ylim(0, 120)
        
        # Format x-axis
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        plt.xticks(rotation=45)
        
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'response_rate.png'))
        plt.close()
    
    def _generate_severity_trend(self, responses: List[Response], user: User, output_dir: str):
        """Generate severity trend line graph"""
        severity_data = [(r.response_timestamp, int(r.response_value)) 
                        for r in responses if r.question_type == 'severity_rating']
        
        if not severity_data:
            return
        
        dates, severities = zip(*severity_data)
        
        # Calculate moving average
        window = 7  # 7-point moving average
        moving_avg = []
        for i in range(len(severities)):
            start = max(0, i - window // 2)
            end = min(len(severities), i + window // 2 + 1)
            avg = sum(severities[start:end]) / (end - start)
            moving_avg.append(avg)
        
        plt.figure(figsize=(12, 6))
        plt.scatter(dates, severities, alpha=0.5, label='Individual Ratings')
        plt.plot(dates, moving_avg, color='red', linewidth=2, label='7-Point Moving Average')
        
        plt.title(f'Severity Trend - {user.first_name} {user.family_name}')
        plt.xlabel('Date')
        plt.ylabel('Severity Level')
        plt.ylim(0.5, 5.5)
        plt.yticks(range(1, 6))
        
        # Add horizontal lines for severity levels
        for level in range(1, 6):
            plt.axhline(y=level, color='gray', linestyle=':', alpha=0.3)
        
        # Format x-axis
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        plt.xticks(rotation=45)
        
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'severity_trend.png'))
        plt.close()

def main():
    """Main function for command-line interface"""
    parser = argparse.ArgumentParser(description='Export diabetes monitoring data')
    
    # User identification
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--telegram-id', type=str, help='Telegram ID of the user')
    group.add_argument('--user-id', type=int, help='Database user ID')
    
    # Date range
    parser.add_argument('--start-date', type=str, 
                       help='Start date (YYYY-MM-DD). Default: 30 days ago')
    parser.add_argument('--end-date', type=str,
                       help='End date (YYYY-MM-DD). Default: today')
    
    # Export options
    parser.add_argument('--format', choices=['xml', 'both'], default='both',
                       help='Export format (default: both)')
    parser.add_argument('--output-dir', type=str, default='exports',
                       help='Output directory (default: exports)')
    parser.add_argument('--no-graphs', action='store_true',
                       help='Skip graph generation')
    
    args = parser.parse_args()
    
    # Parse dates
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    else:
        start_date = datetime.now() - timedelta(days=30)
    
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    else:
        end_date = datetime.now()
    
    # Validate dates
    if start_date > end_date:
        print("Error: Start date must be before end date")
        sys.exit(1)
    
    # Create database session
    db = SessionLocal()
    try:
        # Get user
        if args.telegram_id:
            user = get_user_by_telegram_id(db, args.telegram_id)
            if not user:
                print(f"Error: User with Telegram ID {args.telegram_id} not found")
                sys.exit(1)
            user_id = user.id
        else:
            user_id = args.user_id
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                print(f"Error: User with ID {user_id} not found")
                sys.exit(1)
        
        # Create exporter
        exporter = DataExporter(db)
        
        # Create output directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        user_dir = os.path.join(args.output_dir, f"user_{user.telegram_id}_{timestamp}")
        os.makedirs(user_dir, exist_ok=True)
        
        print(f"Exporting data for: {user.first_name} {user.family_name}")
        print(f"Period: {start_date.date()} to {end_date.date()}")
        print(f"Output directory: {user_dir}")
        print("-" * 50)
        
        # Export XML
        if args.format in ['xml', 'both']:
            xml_file = os.path.join(user_dir, 'data_export.xml')
            stats = exporter.export_to_xml(user_id, start_date, end_date, xml_file)
            print(f"✓ XML exported to: {xml_file}")
            
            # Print statistics
            print("\nStatistics:")
            print(f"  Total responses: {stats['total_responses']}")
            print(f"  Distress occurrences: {stats['distress_count']} ({stats['distress_percentage']:.1f}%)")
            print(f"  Average severity: {stats['average_severity']}")
            print(f"  Response rate: {stats['response_rate']:.1f}%")
        
        # Generate graphs
        if not args.no_graphs and args.format in ['both']:
            print("\nGenerating graphs...")
            exporter.generate_graphs(user_id, start_date, end_date, user_dir)
            print("✓ Graphs generated")
        
        print(f"\n✓ Export completed successfully!")
        print(f"Files saved in: {user_dir}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()