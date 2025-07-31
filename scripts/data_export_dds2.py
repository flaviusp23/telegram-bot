"""Enhanced data export for DDS-2 questionnaire data.

This module handles exporting both legacy and DDS-2 questionnaire data.
"""
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    GRAPHS_AVAILABLE = True
except ImportError:
    GRAPHS_AVAILABLE = False

from database.models import User, Response
from database.constants import QuestionTypes, ResponseValues
from bot_config.bot_constants import (
    XMLConstants, ExportSettings, BotSettings, GraphSettings
)


class DDS2DataExporter:
    """Export handler that supports both legacy and DDS-2 data"""
    
    def export_user_data(self, user: User, responses: List[Response], start_date: datetime, 
                         end_date: datetime, output_dir: str) -> str:
        """Export user data to XML format with DDS-2 support"""
        # Create root element
        root = ET.Element(XMLConstants.ROOT_ELEMENT)
        root.set(XMLConstants.GENERATED_ATTR, datetime.now().strftime(BotSettings.DATETIME_FORMAT))
        root.set(XMLConstants.VERSION_ATTR, XMLConstants.VERSION)
        
        # Add user info
        user_elem = ET.SubElement(root, XMLConstants.USER_ELEMENT)
        user_elem.set(XMLConstants.ID_FIELD, str(user.id))
        ET.SubElement(user_elem, XMLConstants.FIRST_NAME_FIELD).text = user.first_name
        ET.SubElement(user_elem, XMLConstants.FAMILY_NAME_FIELD).text = user.family_name
        ET.SubElement(user_elem, XMLConstants.TELEGRAM_ID_FIELD).text = user.telegram_id
        ET.SubElement(user_elem, XMLConstants.STATUS_FIELD).text = user.status.value
        ET.SubElement(user_elem, XMLConstants.REGISTRATION_DATE_FIELD).text = user.registration_date.strftime(BotSettings.DATETIME_FORMAT)
        
        # Add export period
        period_elem = ET.SubElement(root, XMLConstants.EXPORT_PERIOD_ELEMENT)
        ET.SubElement(period_elem, XMLConstants.START_DATE_FIELD).text = start_date.strftime(BotSettings.DATE_FORMAT)
        ET.SubElement(period_elem, XMLConstants.END_DATE_FIELD).text = end_date.strftime(BotSettings.DATE_FORMAT)
        
        # Calculate statistics for both legacy and DDS-2
        stats = self._calculate_statistics(responses, start_date, end_date)
        
        # Add statistics
        stats_elem = ET.SubElement(root, XMLConstants.STATISTICS_ELEMENT)
        for key, value in stats.items():
            if isinstance(value, float):
                ET.SubElement(stats_elem, key).text = XMLConstants.PERCENTAGE_FORMAT.format(value)
            else:
                ET.SubElement(stats_elem, key).text = str(value)
        
        # Add responses
        responses_elem = ET.SubElement(root, XMLConstants.RESPONSES_ELEMENT)
        for response in responses:
            response_elem = ET.SubElement(responses_elem, XMLConstants.RESPONSE_ELEMENT)
            ET.SubElement(response_elem, XMLConstants.TIMESTAMP_FIELD).text = response.response_timestamp.strftime(BotSettings.DATETIME_FORMAT)
            ET.SubElement(response_elem, XMLConstants.QUESTION_TYPE_FIELD).text = response.question_type
            ET.SubElement(response_elem, XMLConstants.RESPONSE_VALUE_FIELD).text = response.response_value
        
        # Save XML
        xml_path = os.path.join(output_dir, XMLConstants.XML_FILENAME)
        self._save_pretty_xml(root, xml_path)
        
        return xml_path
    
    def _calculate_statistics(self, responses: List[Response], start_date: datetime, 
                             end_date: datetime) -> Dict[str, any]:
        """Calculate statistics including DDS-2 metrics"""
        stats = {
            XMLConstants.TOTAL_RESPONSES_FIELD: len(responses)
        }
        
        # Check if this is DDS-2 data or legacy data
        dds2_responses = [r for r in responses if r.question_type in QuestionTypes.get_dds2_types()]
        legacy_responses = [r for r in responses if r.question_type in [QuestionTypes.DISTRESS_CHECK, QuestionTypes.SEVERITY_RATING]]
        
        if dds2_responses:
            # Calculate DDS-2 statistics
            dds2_stats = self._calculate_dds2_statistics(dds2_responses, start_date, end_date)
            stats.update(dds2_stats)
        
        if legacy_responses:
            # Calculate legacy statistics
            legacy_stats = self._calculate_legacy_statistics(legacy_responses, start_date, end_date)
            stats.update(legacy_stats)
        
        return stats
    
    def _calculate_dds2_statistics(self, responses: List[Response], start_date: datetime, 
                                  end_date: datetime) -> Dict[str, any]:
        """Calculate DDS-2 specific statistics"""
        # Group responses by timestamp to calculate total scores
        sessions = {}
        for r in responses:
            session_key = r.response_timestamp.strftime("%Y-%m-%d %H")
            if session_key not in sessions:
                sessions[session_key] = {}
            
            if r.question_type == QuestionTypes.DDS2_Q1_OVERWHELMED:
                sessions[session_key]['q1'] = int(r.response_value)
            elif r.question_type == QuestionTypes.DDS2_Q2_FAILING:
                sessions[session_key]['q2'] = int(r.response_value)
        
        # Calculate total scores and distress levels
        total_scores = []
        distress_levels = {'low': 0, 'moderate': 0, 'high': 0}
        
        for session in sessions.values():
            if 'q1' in session and 'q2' in session:
                total_score = session['q1'] + session['q2']
                total_scores.append(total_score)
                
                level = ResponseValues.calculate_dds2_distress_level(total_score)
                distress_levels[level] += 1
        
        stats = {
            'dds2_sessions_completed': len(total_scores),
            'dds2_average_score': sum(total_scores) / len(total_scores) if total_scores else 0,
            'dds2_min_score': min(total_scores) if total_scores else 0,
            'dds2_max_score': max(total_scores) if total_scores else 0,
            'dds2_low_distress_count': distress_levels['low'],
            'dds2_moderate_distress_count': distress_levels['moderate'],
            'dds2_high_distress_count': distress_levels['high'],
            'dds2_high_distress_percentage': (distress_levels['high'] / len(total_scores) * 100) if total_scores else 0
        }
        
        # Calculate response rate
        days = (end_date - start_date).days + 1
        expected_responses = days * ExportSettings.EXPECTED_RESPONSES_PER_DAY
        stats['dds2_response_rate'] = (len(total_scores) / expected_responses * 100) if expected_responses > 0 else 0
        
        return stats
    
    def _calculate_legacy_statistics(self, responses: List[Response], start_date: datetime, 
                                    end_date: datetime) -> Dict[str, any]:
        """Calculate legacy questionnaire statistics"""
        distress_responses = [r for r in responses if r.question_type == QuestionTypes.DISTRESS_CHECK]
        severity_responses = [r for r in responses if r.question_type == QuestionTypes.SEVERITY_RATING]
        
        distress_count = sum(1 for r in distress_responses if r.response_value == ResponseValues.YES)
        no_distress_count = sum(1 for r in distress_responses if r.response_value == ResponseValues.NO)
        
        severities = [int(r.response_value) for r in severity_responses]
        
        stats = {
            XMLConstants.DISTRESS_COUNT_FIELD: distress_count,
            XMLConstants.NO_DISTRESS_COUNT_FIELD: no_distress_count,
            XMLConstants.DISTRESS_PERCENTAGE_FIELD: (distress_count / len(distress_responses) * 100) if distress_responses else 0,
            XMLConstants.AVERAGE_SEVERITY_FIELD: sum(severities) / len(severities) if severities else 0,
            XMLConstants.MAX_SEVERITY_FIELD: max(severities) if severities else 0,
            XMLConstants.MIN_SEVERITY_FIELD: min(severities) if severities else 0
        }
        
        # Calculate response rate
        days = (end_date - start_date).days + 1
        expected_responses = days * ExportSettings.EXPECTED_RESPONSES_PER_DAY
        stats[XMLConstants.RESPONSE_RATE_FIELD] = (len(distress_responses) / expected_responses * 100) if expected_responses > 0 else 0
        
        return stats
    
    def generate_graphs(self, responses: List[Response], user: User, start_date: datetime, 
                       end_date: datetime, output_dir: str):
        """Generate graphs supporting both legacy and DDS-2 data"""
        if not GRAPHS_AVAILABLE:
            print("Graphs not available. Install pandas and matplotlib.")
            return
        
        # Check data type
        has_dds2 = any(r.question_type in QuestionTypes.get_dds2_types() for r in responses)
        has_legacy = any(r.question_type in [QuestionTypes.DISTRESS_CHECK, QuestionTypes.SEVERITY_RATING] for r in responses)
        
        if has_dds2:
            self._generate_dds2_graphs(responses, user, start_date, end_date, output_dir)
        
        if has_legacy:
            self._generate_legacy_graphs(responses, user, start_date, end_date, output_dir)
    
    def _generate_dds2_graphs(self, responses: List[Response], user: User, start_date: datetime, 
                             end_date: datetime, output_dir: str):
        """Generate DDS-2 specific graphs"""
        # 1. DDS-2 Total Score Timeline
        dds2_data = self._prepare_dds2_session_data(responses)
        if dds2_data:
            self._plot_dds2_timeline(dds2_data, user, output_dir)
        
        # 2. Distress Level Distribution
        self._plot_dds2_distribution(dds2_data, user, output_dir)
        
        # 3. Question-specific trends
        self._plot_dds2_question_trends(responses, user, output_dir)
    
    def _prepare_dds2_session_data(self, responses: List[Response]) -> List[Tuple[datetime, int, str]]:
        """Prepare DDS-2 session data with timestamps, total scores, and distress levels"""
        sessions = {}
        
        for r in responses:
            if r.question_type in QuestionTypes.get_dds2_types():
                session_key = r.response_timestamp.strftime("%Y-%m-%d %H:%M")
                if session_key not in sessions:
                    sessions[session_key] = {'timestamp': r.response_timestamp}
                
                if r.question_type == QuestionTypes.DDS2_Q1_OVERWHELMED:
                    sessions[session_key]['q1'] = int(r.response_value)
                elif r.question_type == QuestionTypes.DDS2_Q2_FAILING:
                    sessions[session_key]['q2'] = int(r.response_value)
        
        # Calculate total scores
        session_data = []
        for session in sessions.values():
            if 'q1' in session and 'q2' in session:
                total_score = session['q1'] + session['q2']
                distress_level = ResponseValues.calculate_dds2_distress_level(total_score)
                session_data.append((session['timestamp'], total_score, distress_level))
        
        return sorted(session_data, key=lambda x: x[0])
    
    def _plot_dds2_timeline(self, session_data: List[Tuple[datetime, int, str]], user: User, output_dir: str):
        """Plot DDS-2 total score timeline"""
        if not session_data:
            return
        
        timestamps, scores, levels = zip(*session_data)
        
        plt.figure(figsize=(12, 6))
        
        # Color points by distress level
        colors = []
        for level in levels:
            if level == 'low':
                colors.append('#2ecc71')  # Green
            elif level == 'moderate':
                colors.append('#f39c12')  # Orange
            else:
                colors.append('#e74c3c')  # Red
        
        plt.scatter(timestamps, scores, c=colors, s=100, alpha=0.7)
        plt.plot(timestamps, scores, 'k-', alpha=0.3)
        
        # Add threshold lines
        plt.axhline(y=4, color='green', linestyle='--', alpha=0.5, label='Low distress threshold')
        plt.axhline(y=8, color='orange', linestyle='--', alpha=0.5, label='Moderate distress threshold')
        
        plt.title(f'DDS-2 Total Score Timeline - {user.first_name} {user.family_name}')
        plt.xlabel('Date')
        plt.ylabel('DDS-2 Total Score (2-12)')
        plt.ylim(1, 13)
        plt.yticks(range(2, 13))
        
        # Format x-axis
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        plt.xticks(rotation=45)
        
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'dds2_timeline.png'))
        plt.close()
    
    def _plot_dds2_distribution(self, session_data: List[Tuple[datetime, int, str]], user: User, output_dir: str):
        """Plot distress level distribution pie chart"""
        if not session_data:
            return
        
        # Count distress levels
        level_counts = {'Low': 0, 'Moderate': 0, 'High': 0}
        for _, _, level in session_data:
            level_counts[level.capitalize()] += 1
        
        # Filter out zero counts
        labels = []
        sizes = []
        colors = []
        
        for level, count in level_counts.items():
            if count > 0:
                labels.append(f'{level}\n({count} sessions)')
                sizes.append(count)
                if level == 'Low':
                    colors.append('#2ecc71')
                elif level == 'Moderate':
                    colors.append('#f39c12')
                else:
                    colors.append('#e74c3c')
        
        if not sizes:
            return
        
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title(f'DDS-2 Distress Level Distribution - {user.first_name} {user.family_name}')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'dds2_distribution.png'))
        plt.close()
    
    def _plot_dds2_question_trends(self, responses: List[Response], user: User, output_dir: str):
        """Plot individual question trends"""
        q1_data = [(r.response_timestamp, int(r.response_value)) 
                   for r in responses if r.question_type == QuestionTypes.DDS2_Q1_OVERWHELMED]
        q2_data = [(r.response_timestamp, int(r.response_value)) 
                   for r in responses if r.question_type == QuestionTypes.DDS2_Q2_FAILING]
        
        if not q1_data and not q2_data:
            return
        
        plt.figure(figsize=(12, 8))
        
        # Plot Q1
        if q1_data:
            timestamps, values = zip(*sorted(q1_data))
            plt.subplot(2, 1, 1)
            plt.plot(timestamps, values, 'b-o', alpha=0.7, label='Q1: Overwhelmed')
            plt.ylabel('Score (1-6)')
            plt.ylim(0.5, 6.5)
            plt.yticks(range(1, 7))
            plt.title('Q1: Feeling overwhelmed by the demands of living with diabetes')
            plt.grid(True, alpha=0.3)
            plt.legend()
        
        # Plot Q2
        if q2_data:
            timestamps, values = zip(*sorted(q2_data))
            plt.subplot(2, 1, 2)
            plt.plot(timestamps, values, 'r-o', alpha=0.7, label='Q2: Failing')
            plt.xlabel('Date')
            plt.ylabel('Score (1-6)')
            plt.ylim(0.5, 6.5)
            plt.yticks(range(1, 7))
            plt.title('Q2: Feeling that I am often failing with my diabetes regimen')
            plt.grid(True, alpha=0.3)
            plt.legend()
        
        plt.suptitle(f'DDS-2 Individual Question Trends - {user.first_name} {user.family_name}')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'dds2_questions.png'))
        plt.close()
    
    def _generate_legacy_graphs(self, responses: List[Response], user: User, start_date: datetime, 
                               end_date: datetime, output_dir: str):
        """Generate legacy questionnaire graphs (existing functionality)"""
        # This would include the existing graph generation code for legacy data
        pass
    
    def _save_pretty_xml(self, root, filepath):
        """Save XML with pretty formatting"""
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent=XMLConstants.INDENT_SPACES)
        
        # Remove extra blank lines
        pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)