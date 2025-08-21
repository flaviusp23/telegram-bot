"""
Data export endpoints for admin panel
"""
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd

from admin.core.permissions import require_viewer, AdminUser, require_admin
from database.database import get_db
from database.models import User, Response

router = APIRouter(tags=["export"])

@router.get("/responses")
async def export_responses(
    format: str = Query("csv", description="Export format: csv or excel"),
    days: int = Query(30, description="Number of days to export", ge=1, le=365),
    patient_id: Optional[int] = Query(None, description="Filter by specific patient ID"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(require_viewer)
):
    """
    Export response data in CSV or Excel format
    """
    # Calculate date range using UTC
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Query responses with patient info
    query = db.query(
        Response.id,
        User.first_name,
        User.family_name,
        User.telegram_id,
        Response.question_type,
        Response.response_value,
        Response.response_timestamp
    ).join(User).filter(
        Response.response_timestamp >= start_date
    )
    
    # Filter by patient if specified
    if patient_id:
        query = query.filter(Response.user_id == patient_id)
    
    query = query.order_by(Response.response_timestamp.desc())
    
    # Convert to DataFrame
    data = []
    for row in query.all():
        data.append({
            'Response ID': row.id,
            'First Name': row.first_name,
            'Last Name': row.family_name,
            'Telegram ID': row.telegram_id,
            'Question Type': row.question_type,
            'Response': row.response_value,
            'Timestamp': row.response_timestamp
        })
    
    df = pd.DataFrame(data)
    
    # Generate file
    if format == "excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Responses', index=False)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=responses_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.xlsx"
            }
        )
    else:  # CSV
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=responses_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )

@router.get("/users")
async def export_users(
    format: str = Query("csv", description="Export format: csv or excel"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(require_admin)
):
    """
    Export patient data (requires admin role)
    """
    # Query all patients
    patients = db.query(User).all()
    
    # Convert to DataFrame
    data = []
    for patient in patients:
        data.append({
            'Patient ID': patient.id,
            'First Name': patient.first_name,
            'Last Name': patient.family_name,
            'Telegram ID': patient.telegram_id,
            'Email': patient.email,
            'Phone': patient.phone_number,
            'Status': patient.status.value,
            'Registration Date': patient.registration_date,
            'Last Interaction': patient.last_interaction
        })
    
    df = pd.DataFrame(data)
    
    # Generate file
    if format == "excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Patients', index=False)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=users_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.xlsx"
            }
        )
    else:  # CSV
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=users_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )


@router.get("/patient-report/{patient_id}")
async def export_patient_report(
    patient_id: int,
    format: str = Query("excel", description="Export format: excel"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(require_viewer)
):
    """
    Export comprehensive patient report with charts data
    """
    # Get patient details
    patient = db.query(User).filter(User.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get all patient responses
    responses = db.query(Response).filter(
        Response.user_id == patient_id
    ).order_by(Response.response_timestamp.desc()).all()
    
    # Prepare data for multiple sheets
    sheets_data = {}
    
    # Sheet 1: Patient Information
    patient_info = pd.DataFrame([{
        'Patient ID': patient.id,
        'First Name': patient.first_name,
        'Last Name': patient.family_name,
        'Telegram ID': patient.telegram_id,
        'Email': patient.email or 'N/A',
        'Phone': patient.phone_number or 'N/A',
        'Status': patient.status.value,
        'Registration Date': patient.registration_date,
        'Last Interaction': patient.last_interaction,
        'Total Responses': len(responses)
    }])
    sheets_data['Patient Info'] = patient_info
    
    # Sheet 2: All Responses
    responses_data = []
    for resp in responses:
        responses_data.append({
            'Date': resp.response_timestamp.date(),
            'Time': resp.response_timestamp.time(),
            'Question Type': resp.question_type,
            'Response': resp.response_value
        })
    
    if responses_data:
        sheets_data['All Responses'] = pd.DataFrame(responses_data)
    
    # Sheet 3: Daily Summary
    daily_summary = {}
    
    for resp in responses:
        date_key = resp.response_timestamp.date()
        
        if date_key not in daily_summary:
            daily_summary[date_key] = {
                'Date': date_key,
                'Total Responses': 0,
                'Distress Checks': 0,
                'DDS-2 Q1 (Overwhelmed)': 0,
                'DDS-2 Q2 (Failing)': 0,
                'Legacy Severity Ratings': 0,
                'Average DDS-2 Score': [],
                'Average Legacy Severity': []
            }
        
        daily_summary[date_key]['Total Responses'] += 1
        
        if resp.question_type == 'distress_check':
            daily_summary[date_key]['Distress Checks'] += 1
        elif resp.question_type == 'dds2_q1_overwhelmed':
            daily_summary[date_key]['DDS-2 Q1 (Overwhelmed)'] += 1
            daily_summary[date_key]['Average DDS-2 Score'].append(int(resp.response_value))
        elif resp.question_type == 'dds2_q2_failing':
            daily_summary[date_key]['DDS-2 Q2 (Failing)'] += 1
            daily_summary[date_key]['Average DDS-2 Score'].append(int(resp.response_value))
        elif resp.question_type == 'severity_rating':
            daily_summary[date_key]['Legacy Severity Ratings'] += 1
            daily_summary[date_key]['Average Legacy Severity'].append(int(resp.response_value))
    
    # Calculate averages
    daily_data = []
    for date_key, data in sorted(daily_summary.items()):
        avg_dds2_score = sum(data['Average DDS-2 Score']) / len(data['Average DDS-2 Score']) if data['Average DDS-2 Score'] else 0
        avg_legacy_severity = sum(data['Average Legacy Severity']) / len(data['Average Legacy Severity']) if data['Average Legacy Severity'] else 0
        daily_data.append({
            'Date': data['Date'],
            'Total Responses': data['Total Responses'],
            'Distress Checks': data['Distress Checks'],
            'DDS-2 Q1 (Overwhelmed)': data['DDS-2 Q1 (Overwhelmed)'],
            'DDS-2 Q2 (Failing)': data['DDS-2 Q2 (Failing)'],
            'Legacy Severity Ratings': data['Legacy Severity Ratings'],
            'Average DDS-2 Score (1-6)': round(avg_dds2_score, 2),
            'Average Legacy Severity (1-5)': round(avg_legacy_severity, 2)
        })
    
    if daily_data:
        sheets_data['Daily Summary'] = pd.DataFrame(daily_data)
    
    # Sheet 4: Weekly Summary
    weekly_summary = {}
    
    for resp in responses:
        # Get week start date (Monday)
        date = resp.response_timestamp.date()
        week_start = date - timedelta(days=date.weekday())
        week_key = week_start
        
        if week_key not in weekly_summary:
            weekly_summary[week_key] = {
                'Week Starting': week_key,
                'Total Responses': 0,
                'Average DDS-2 Score': [],
                'Average Legacy Severity': []
            }
        
        weekly_summary[week_key]['Total Responses'] += 1
        
        if resp.question_type in ['dds2_q1_overwhelmed', 'dds2_q2_failing']:
            weekly_summary[week_key]['Average DDS-2 Score'].append(int(resp.response_value))
        elif resp.question_type == 'severity_rating':
            weekly_summary[week_key]['Average Legacy Severity'].append(int(resp.response_value))
    
    weekly_data = []
    for week_key, data in sorted(weekly_summary.items()):
        avg_dds2_score = sum(data['Average DDS-2 Score']) / len(data['Average DDS-2 Score']) if data['Average DDS-2 Score'] else 0
        avg_legacy_severity = sum(data['Average Legacy Severity']) / len(data['Average Legacy Severity']) if data['Average Legacy Severity'] else 0
        weekly_data.append({
            'Week Starting': data['Week Starting'],
            'Total Responses': data['Total Responses'],
            'Average DDS-2 Score (1-6)': round(avg_dds2_score, 2),
            'Average Legacy Severity (1-5)': round(avg_legacy_severity, 2)
        })
    
    if weekly_data:
        sheets_data['Weekly Summary'] = pd.DataFrame(weekly_data)
    
    # Sheet 5: DDS-2 Score Distribution
    dds2_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    legacy_severity_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    for resp in responses:
        if resp.question_type in ['dds2_q1_overwhelmed', 'dds2_q2_failing']:
            level = int(resp.response_value)
            if 1 <= level <= 6:
                dds2_counts[level] += 1
        elif resp.question_type == 'severity_rating':
            level = int(resp.response_value)
            if 1 <= level <= 5:
                legacy_severity_counts[level] += 1
    
    # DDS-2 Distribution with clinical descriptions
    dds2_labels = [
        "Not a problem", "A slight problem", "A moderate problem", 
        "Somewhat serious problem", "A serious problem", "A very serious problem"
    ]
    
    dds2_dist = pd.DataFrame([
        {'DDS-2 Score': f'Level {k} - {dds2_labels[k-1]}', 
         'Count': v, 
         'Percentage': round(v / sum(dds2_counts.values()) * 100, 1) if sum(dds2_counts.values()) > 0 else 0}
        for k, v in dds2_counts.items()
    ])
    sheets_data['DDS-2 Score Distribution'] = dds2_dist
    
    # Legacy Severity Distribution (if any legacy data exists)
    if sum(legacy_severity_counts.values()) > 0:
        legacy_dist = pd.DataFrame([
            {'Legacy Severity Level': f'Level {k} ({["Low", "Low-Medium", "Medium", "Medium-High", "High"][k-1]})', 
             'Count': v, 
             'Percentage': round(v / sum(legacy_severity_counts.values()) * 100, 1) if sum(legacy_severity_counts.values()) > 0 else 0}
            for k, v in legacy_severity_counts.items()
        ])
        sheets_data['Legacy Severity Distribution'] = legacy_dist
    
    # Generate Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in sheets_data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
    
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=patient_{patient_id}_report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.xlsx"
        }
    )