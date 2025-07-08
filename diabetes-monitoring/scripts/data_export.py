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

from database import SessionLocal, get_user_by_telegram_id, get_user_responses, db_session_context
from database.models import User, Response
from database.constants import QuestionTypes, ResponseValues
from bot_config.bot_constants import (
    AlertSettings, ExportSettings, XMLConstants, GraphSettings, BotSettings
)
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
        distress_checks = [r for r in responses if r.question_type == QuestionTypes.DISTRESS_CHECK]
        severity_ratings = [r for r in responses if r.question_type == QuestionTypes.SEVERITY_RATING]
        
        # Calculate statistics
        total_checks = len(distress_checks)
        distress_count = sum(1 for r in distress_checks if r.response_value == ResponseValues.YES)
        no_distress_count = total_checks - distress_count
        
        # Severity statistics
        severities = [int(r.response_value) for r in severity_ratings]
        avg_severity = sum(severities) / len(severities) if severities else 0
        max_severity = max(severities) if severities else 0
        min_severity = min(severities) if severities else 0
        
        # Response rate
        days = (end_date - start_date).days + 1
        expected_responses = days * AlertSettings.EXPECTED_RESPONSES_PER_DAY
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
        distribution = {level: 0 for level in ResponseValues.get_numeric_ratings()}
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
        root = ET.Element(XMLConstants.ROOT_ELEMENT)
        root.set(XMLConstants.GENERATED_ATTR, datetime.now().isoformat())
        root.set(XMLConstants.VERSION_ATTR, XMLConstants.VERSION)
        
        # User information
        user_elem = ET.SubElement(root, XMLConstants.USER_ELEMENT)
        ET.SubElement(user_elem, XMLConstants.ID_FIELD).text = str(user.id)
        ET.SubElement(user_elem, XMLConstants.FIRST_NAME_FIELD).text = user.first_name
        ET.SubElement(user_elem, XMLConstants.FAMILY_NAME_FIELD).text = user.family_name
        ET.SubElement(user_elem, XMLConstants.TELEGRAM_ID_FIELD).text = user.telegram_id
        ET.SubElement(user_elem, XMLConstants.STATUS_FIELD).text = user.status.value
        ET.SubElement(user_elem, XMLConstants.REGISTRATION_DATE_FIELD).text = user.registration_date.isoformat()
        
        # Export period
        period_elem = ET.SubElement(root, XMLConstants.EXPORT_PERIOD_ELEMENT)
        ET.SubElement(period_elem, XMLConstants.START_DATE_FIELD).text = start_date.isoformat()
        ET.SubElement(period_elem, XMLConstants.END_DATE_FIELD).text = end_date.isoformat()
        
        # Statistics
        stats = self.get_user_statistics(user_id, start_date, end_date)
        stats_elem = ET.SubElement(root, XMLConstants.STATISTICS_ELEMENT)
        ET.SubElement(stats_elem, XMLConstants.TOTAL_RESPONSES_FIELD).text = str(stats['total_responses'])
        ET.SubElement(stats_elem, XMLConstants.DISTRESS_COUNT_FIELD).text = str(stats['distress_count'])
        ET.SubElement(stats_elem, XMLConstants.NO_DISTRESS_COUNT_FIELD).text = str(stats['no_distress_count'])
        ET.SubElement(stats_elem, XMLConstants.DISTRESS_PERCENTAGE_FIELD).text = XMLConstants.PERCENTAGE_FORMAT.format(stats['distress_percentage'])
        ET.SubElement(stats_elem, XMLConstants.AVERAGE_SEVERITY_FIELD).text = str(stats['average_severity'])
        ET.SubElement(stats_elem, XMLConstants.MAX_SEVERITY_FIELD).text = str(stats['max_severity'])
        ET.SubElement(stats_elem, XMLConstants.MIN_SEVERITY_FIELD).text = str(stats['min_severity'])
        ET.SubElement(stats_elem, XMLConstants.RESPONSE_RATE_FIELD).text = XMLConstants.PERCENTAGE_FORMAT.format(stats['response_rate'])
        
        # Severity distribution
        dist_elem = ET.SubElement(stats_elem, XMLConstants.SEVERITY_DISTRIBUTION_ELEMENT)
        for level, count in stats['severity_distribution'].items():
            level_elem = ET.SubElement(dist_elem, XMLConstants.LEVEL_ELEMENT)
            level_elem.set(XMLConstants.VALUE_ATTR, str(level))
            level_elem.text = str(count)
        
        # Responses
        responses_elem = ET.SubElement(root, XMLConstants.RESPONSES_ELEMENT)
        responses = self.db.query(Response).filter(
            and_(
                Response.user_id == user_id,
                Response.response_timestamp >= start_date,
                Response.response_timestamp <= end_date
            )
        ).order_by(Response.response_timestamp).all()
        
        for response in responses:
            resp_elem = ET.SubElement(responses_elem, XMLConstants.RESPONSE_ELEMENT)
            ET.SubElement(resp_elem, XMLConstants.ID_FIELD).text = str(response.id)
            ET.SubElement(resp_elem, XMLConstants.TIMESTAMP_FIELD).text = response.response_timestamp.isoformat()
            ET.SubElement(resp_elem, XMLConstants.QUESTION_TYPE_FIELD).text = response.question_type
            ET.SubElement(resp_elem, XMLConstants.RESPONSE_VALUE_FIELD).text = response.response_value
        
        # Pretty print and save
        self._indent_xml(root)
        tree = ET.ElementTree(root)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
        return stats
    
    def _indent_xml(self, elem, level=0):
        """Add pretty-printing to XML"""
        i = "\n" + level * XMLConstants.INDENT_SPACES
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + XMLConstants.INDENT_SPACES
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
        distress_data = [(r.response_timestamp, 1 if r.response_value == ResponseValues.YES else 0) 
                        for r in responses if r.question_type == QuestionTypes.DISTRESS_CHECK]
        
        if not distress_data:
            return
        
        dates, values = zip(*distress_data)
        
        plt.figure(figsize=GraphSettings.TIMELINE_FIGURE_SIZE)
        plt.scatter(dates, values, alpha=GraphSettings.SCATTER_ALPHA, s=GraphSettings.SCATTER_SIZE)
        plt.plot(dates, values, alpha=GraphSettings.LINE_ALPHA)
        
        plt.title(GraphSettings.DISTRESS_TIMELINE_TITLE.format(first_name=user.first_name, family_name=user.family_name))
        plt.xlabel(GraphSettings.DATE_LABEL)
        plt.ylabel(GraphSettings.DISTRESS_LABEL)
        plt.ylim(GraphSettings.DISTRESS_Y_MIN, GraphSettings.DISTRESS_Y_MAX)
        plt.yticks(*GraphSettings.DISTRESS_Y_TICKS)
        
        # Format x-axis
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter(BotSettings.DATE_FORMAT))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=GraphSettings.DATE_INTERVAL_DAYS))
        plt.xticks(rotation=GraphSettings.DATE_ROTATION)
        
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
        colors = ExportSettings.SEVERITY_COLORS
        
        for level, count in distribution.items():
            if count > 0:
                labels.append(f'Level {level}')
                sizes.append(count)
        
        plt.figure(figsize=GraphSettings.PIE_FIGURE_SIZE)
        plt.pie(sizes, labels=labels, colors=colors[:len(labels)], autopct=GraphSettings.AUTOPCT_FORMAT, startangle=GraphSettings.PIE_START_ANGLE)
        plt.title(GraphSettings.SEVERITY_DISTRIBUTION_TITLE.format(first_name=user.first_name, family_name=user.family_name))
        plt.axis('equal')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, ExportSettings.GRAPHS[1][0]))
        plt.close()
    
    def _generate_response_rate(self, responses: List[Response], user: User, start_date: datetime, end_date: datetime, output_dir: str):
        """Generate daily response rate graph"""
        # Group responses by date
        response_counts = {}
        for r in responses:
            if r.question_type == QuestionTypes.DISTRESS_CHECK:
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
            rate = (count / AlertSettings.EXPECTED_RESPONSES_PER_DAY) * 100
            rates.append(min(rate, BotSettings.MAX_RESPONSE_RATE_PERCENT))  # Cap at 100%
            current_date += timedelta(days=1)
        
        plt.figure(figsize=GraphSettings.BAR_FIGURE_SIZE)
        plt.bar(dates, rates, alpha=GraphSettings.BAR_ALPHA, color=ExportSettings.RESPONSE_RATE_COLOR)
        plt.axhline(y=100, color='r', linestyle='--', alpha=GraphSettings.EXPECTED_LINE_ALPHA, label=GraphSettings.EXPECTED_RATE_LABEL)
        
        plt.title(GraphSettings.RESPONSE_RATE_TITLE.format(first_name=user.first_name, family_name=user.family_name))
        plt.xlabel(GraphSettings.DATE_LABEL)
        plt.ylabel(GraphSettings.RESPONSE_RATE_LABEL)
        plt.ylim(0, GraphSettings.RESPONSE_RATE_Y_MAX)
        
        # Format x-axis
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter(BotSettings.DATE_FORMAT))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=GraphSettings.DATE_INTERVAL_DAYS))
        plt.xticks(rotation=GraphSettings.DATE_ROTATION)
        
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, ExportSettings.GRAPHS[2][0]))
        plt.close()
    
    def _generate_severity_trend(self, responses: List[Response], user: User, output_dir: str):
        """Generate severity trend line graph"""
        severity_data = [(r.response_timestamp, int(r.response_value)) 
                        for r in responses if r.question_type == QuestionTypes.SEVERITY_RATING]
        
        if not severity_data:
            return
        
        dates, severities = zip(*severity_data)
        
        # Calculate moving average
        window = ExportSettings.SEVERITY_TREND_WINDOW
        moving_avg = []
        for i in range(len(severities)):
            start = max(0, i - window // 2)
            end = min(len(severities), i + window // 2 + 1)
            avg = sum(severities[start:end]) / (end - start)
            moving_avg.append(avg)
        
        plt.figure(figsize=GraphSettings.TREND_FIGURE_SIZE)
        plt.scatter(dates, severities, alpha=GraphSettings.SCATTER_ALPHA, label=GraphSettings.INDIVIDUAL_RATINGS_LABEL)
        plt.plot(dates, moving_avg, color='red', linewidth=2, label=GraphSettings.MOVING_AVERAGE_LABEL)
        
        plt.title(GraphSettings.SEVERITY_TREND_TITLE.format(first_name=user.first_name, family_name=user.family_name))
        plt.xlabel(GraphSettings.DATE_LABEL)
        plt.ylabel(GraphSettings.SEVERITY_LEVEL_LABEL)
        plt.ylim(GraphSettings.SEVERITY_Y_MIN, GraphSettings.SEVERITY_Y_MAX)
        plt.yticks(GraphSettings.SEVERITY_Y_TICKS)
        
        # Add horizontal lines for severity levels
        for level in ResponseValues.get_numeric_ratings():
            plt.axhline(y=level, color='gray', linestyle=':', alpha=GraphSettings.GRID_ALPHA)
        
        # Format x-axis
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter(BotSettings.DATE_FORMAT))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=GraphSettings.DATE_INTERVAL_DAYS))
        plt.xticks(rotation=GraphSettings.DATE_ROTATION)
        
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, ExportSettings.GRAPHS[3][0]))
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
                       help=f'Start date (YYYY-MM-DD). Default: {ExportSettings.DEFAULT_EXPORT_DAYS} days ago')
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
        start_date = datetime.now() - timedelta(days=ExportSettings.DEFAULT_EXPORT_DAYS)
    
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    else:
        end_date = datetime.now()
    
    # Validate dates
    if start_date > end_date:
        print("Error: Start date must be before end date")
        sys.exit(1)
    
    # Use database session context
    try:
        with db_session_context(commit=False) as db:
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
            timestamp = datetime.now().strftime(BotSettings.TIMESTAMP_FORMAT)
            user_dir = os.path.join(args.output_dir, f"user_{user.telegram_id}_{timestamp}")
            os.makedirs(user_dir, exist_ok=True)
            
            print(f"Exporting data for: {user.first_name} {user.family_name}")
            print(f"Period: {start_date.date()} to {end_date.date()}")
            print(f"Output directory: {user_dir}")
            print("-" * 50)
            
            # Export XML
            if args.format in ['xml', 'both']:
                xml_file = os.path.join(user_dir, ExportSettings.XML_FILENAME)
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

if __name__ == "__main__":
    main()