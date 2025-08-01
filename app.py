from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
from datetime import datetime
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from io import BytesIO
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Files to store data
JOBS_FILE = 'jobs_data.json'
COLUMNS_FILE = 'columns_config.json'

# Email configuration
EMAIL_CONFIG = {
    'sender_email': 'sameermujahid7777@gmail.com',
    'sender_password': 'aodh onnb xbap gpew',
    'recipient_email': 'sameermujahid7777@gmail.com',
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}

# Initialize scheduler (only for local development)
scheduler = None
if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.start()

def load_jobs():
    """Load jobs from JSON file"""
    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_jobs(jobs):
    """Save jobs to JSON file"""
    with open(JOBS_FILE, 'w') as f:
        json.dump(jobs, f, indent=2)

def load_columns():
    """Load column configuration"""
    if os.path.exists(COLUMNS_FILE):
        try:
            with open(COLUMNS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass

    # Default columns
    default_columns = [
        {
            "id": "company",
            "name": "Company Name",
            "type": "text",
            "required": True,
            "order": 1
        },
        {
            "id": "title",
            "name": "Job Title / Role",
            "type": "text",
            "required": True,
            "order": 2
        },
        {
            "id": "location",
            "name": "Job Location",
            "type": "text",
            "required": True,
            "order": 3
        },
        {
            "id": "application_date",
            "name": "Application Date",
            "type": "date",
            "required": True,
            "order": 4
        },
        {
            "id": "platform",
            "name": "Application Platform",
            "type": "select",
            "options": ["LinkedIn", "Indeed", "Glassdoor", "Company Website", "Other"],
            "editable": True,
            "required": True,
            "order": 5
        },
        {
            "id": "status",
            "name": "Application Status",
            "type": "select",
            "options": ["Applied", "Interviewing", "Offer", "Rejected", "Withdrawn"],
            "editable": True,
            "required": True,
            "order": 6
        },
        {
            "id": "website_link",
            "name": "Website Link",
            "type": "url",
            "required": False,
            "order": 7
        },
        {
            "id": "notes",
            "name": "Notes",
            "type": "textarea",
            "required": False,
            "order": 8
        }
    ]

    save_columns(default_columns)
    return default_columns

def save_columns(columns):
    """Save column configuration"""
    with open(COLUMNS_FILE, 'w') as f:
        json.dump(columns, f, indent=2)

def send_email(subject, body):
    """Send email using Gmail SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['recipient_email']
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['recipient_email'], text)
        server.quit()
        
        print(f"Email sent successfully: {subject}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def generate_job_summary():
    """Generate job application summary for email"""
    jobs = load_jobs()
    
    if not jobs:
        return "No job applications found."
    
    # Get recent applications (last 7 days)
    recent_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    recent_jobs = []
    
    for job in jobs:
        try:
            app_date = datetime.fromisoformat(job.get('application_date', '').replace('Z', '+00:00'))
            if (recent_date - app_date).days <= 7:
                recent_jobs.append(job)
        except:
            pass
    
    # Get status breakdown
    status_counts = {}
    for job in jobs:
        status = job.get('status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Generate HTML email
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
            .stat {{ text-align: center; }}
            .stat-number {{ font-size: 2em; font-weight: bold; color: #6366f1; }}
            .recent-jobs {{ margin: 20px 0; }}
            .job-item {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #6366f1; }}
            .status-applied {{ border-left-color: #10b981; }}
            .status-interviewing {{ border-left-color: #f59e0b; }}
            .status-offer {{ border-left-color: #6366f1; }}
            .status-rejected {{ border-left-color: #ef4444; }}
            .footer {{ background: #f8f9fa; padding: 15px; text-align: center; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📋 Job Application Tracker - Daily Update</h1>
            <p>Hi Sameer, here's your job application summary</p>
        </div>
        
        <div class="content">
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">{len(jobs)}</div>
                    <div>Total Applications</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{len(recent_jobs)}</div>
                    <div>Recent (7 days)</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{status_counts.get('Interviewing', 0)}</div>
                    <div>Interviewing</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{status_counts.get('Offer', 0)}</div>
                    <div>Offers</div>
                </div>
            </div>
            
            <h2>📊 Status Breakdown</h2>
            <ul>
    """
    
    for status, count in status_counts.items():
        html_content += f"<li><strong>{status}:</strong> {count} applications</li>"
    
    html_content += """
            </ul>
            
            <h2>🆕 Recent Applications (Last 7 Days)</h2>
    """
    
    if recent_jobs:
        for job in recent_jobs:
            status_class = f"status-{job.get('status', '').lower()}"
            html_content += f"""
            <div class="job-item {status_class}">
                <h3>{job.get('title', 'N/A')}</h3>
                <p><strong>Company:</strong> {job.get('company', 'N/A')}</p>
                <p><strong>Location:</strong> {job.get('location', 'N/A')}</p>
                <p><strong>Status:</strong> {job.get('status', 'N/A')}</p>
                <p><strong>Applied:</strong> {job.get('application_date', 'N/A')}</p>
            </div>
            """
    else:
        html_content += "<p>No recent applications in the last 7 days.</p>"
    
    html_content += """
        </div>
        
        <div class="footer">
            <p>💡 <strong>Action Items:</strong></p>
            <ul style="text-align: left; max-width: 500px; margin: 0 auto;">
                <li>Follow up on applications that haven't received responses</li>
                <li>Prepare for upcoming interviews</li>
                <li>Apply to new positions</li>
                <li>Update application statuses</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    return html_content

def send_morning_reminder():
    """Send morning reminder email"""
    subject = "🌅 Good Morning Sameer! - Job Application Reminder"
    body = generate_job_summary()
    send_email(subject, body)

def send_afternoon_reminder():
    """Send afternoon reminder email"""
    subject = "☀️ Afternoon Check-in - Job Application Update"
    body = generate_job_summary()
    send_email(subject, body)

def send_evening_reminder():
    """Send evening reminder email"""
    subject = "🌙 Evening Wrap-up - Job Application Summary"
    body = generate_job_summary()
    send_email(subject, body)

@app.route('/')
def index():
    return render_template('job_tracker.html')

@app.route('/api/columns', methods=['GET'])
def get_columns():
    """Get column configuration"""
    columns = load_columns()
    return jsonify(columns)

@app.route('/api/columns', methods=['POST'])
def add_column():
    """Add a new column"""
    try:
        data = request.get_json()

        if not data.get('name') or not data.get('type'):
            return jsonify({'error': 'Column name and type are required'}), 400

        columns = load_columns()

        # Generate unique ID
        column_id = data.get('id') or f"custom_{len(columns) + 1}"

        # Find max order
        max_order = max([col.get('order', 0) for col in columns]) if columns else 0

        new_column = {
            "id": column_id,
            "name": data['name'],
            "type": data['type'],
            "required": data.get('required', False),
            "order": max_order + 1
        }

        # Add type-specific properties
        if data['type'] == 'select':
            new_column['options'] = data.get('options', [])
            new_column['editable'] = data.get('editable', True)
        elif data['type'] == 'url':
            new_column['placeholder'] = 'https://example.com'

        columns.append(new_column)
        save_columns(columns)

        return jsonify({'success': True, 'column': new_column})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/columns/<column_id>', methods=['PUT'])
def update_column(column_id):
    """Update a column"""
    try:
        data = request.get_json()
        columns = load_columns()

        for column in columns:
            if column['id'] == column_id:
                column.update(data)
                save_columns(columns)
                return jsonify({'success': True, 'column': column})

        return jsonify({'error': 'Column not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/columns/<column_id>', methods=['DELETE'])
def delete_column(column_id):
    """Delete a column"""
    try:
        columns = load_columns()
        columns = [col for col in columns if col['id'] != column_id]
        save_columns(columns)

        # Also remove this field from all jobs
        jobs = load_jobs()
        for job in jobs:
            if column_id in job:
                del job[column_id]
        save_jobs(jobs)

        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get all jobs with optional filtering"""
    try:
        jobs = load_jobs()

        # Apply filters
        search = request.args.get('search', '').lower()
        status_filter = request.args.get('status', '')
        platform_filter = request.args.get('platform', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        if search:
            jobs = [job for job in jobs if any(
                search in str(value).lower()
                for value in job.values()
                if value is not None
            )]

        if status_filter:
            jobs = [job for job in jobs if job.get('status') == status_filter]

        if platform_filter:
            jobs = [job for job in jobs if job.get('platform') == platform_filter]

        if date_from:
            jobs = [job for job in jobs if job.get('application_date', '') >= date_from]

        if date_to:
            jobs = [job for job in jobs if job.get('application_date', '') <= date_to]

        return jsonify(jobs)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs', methods=['POST'])
def add_job():
    """Add a new job"""
    try:
        data = request.get_json()
        columns = load_columns()

        # Validate required fields
        required_fields = [col['id'] for col in columns if col.get('required', False)]
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Create new job with all column fields
        new_job = {
            'id': str(uuid.uuid4()),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # Add all column fields
        for column in columns:
            field_id = column['id']
            if field_id in data:
                new_job[field_id] = data[field_id]
            elif column.get('required', False):
                new_job[field_id] = ''

        # Load existing jobs and add new one
        jobs = load_jobs()
        jobs.append(new_job)
        save_jobs(jobs)

        return jsonify({'success': True, 'job': new_job})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/<job_id>', methods=['PUT'])
def update_job(job_id):
    """Update an existing job"""
    try:
        data = request.get_json()
        jobs = load_jobs()

        # Find and update the job
        for job in jobs:
            if job['id'] == job_id:
                job.update(data)
                job['updated_at'] = datetime.now().isoformat()
                save_jobs(jobs)
                return jsonify({'success': True, 'job': job})

        return jsonify({'error': 'Job not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job"""
    try:
        jobs = load_jobs()
        jobs = [job for job in jobs if job['id'] != job_id]
        save_jobs(jobs)
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/excel')
def export_excel():
    """Export jobs to Excel file"""
    try:
        jobs = load_jobs()
        columns = load_columns()

        if not jobs:
            return jsonify({'error': 'No jobs to export'}), 404

        # Create DataFrame with only the configured columns
        df_data = []
        for job in jobs:
            row = {}
            for column in sorted(columns, key=lambda x: x.get('order', 0)):
                field_id = column['id']
                row[column['name']] = job.get(field_id, '')
            df_data.append(row)

        df = pd.DataFrame(df_data)

        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Job Applications', index=False)

            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Job Applications']

            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

            # Style the header row
            from openpyxl.styles import Font, PatternFill, Alignment
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
            header_alignment = Alignment(horizontal="center", vertical="center")

            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment

        output.seek(0)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'job_applications_{timestamp}.xlsx'

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get job application statistics"""
    try:
        jobs = load_jobs()

        if not jobs:
            return jsonify({
                'total_applications': 0,
                'status_breakdown': {},
                'platform_breakdown': {},
                'recent_applications': 0
            })

        # Calculate statistics
        total_applications = len(jobs)

        # Status breakdown
        status_counts = {}
        for job in jobs:
            status = job.get('status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1

        # Platform breakdown
        platform_counts = {}
        for job in jobs:
            platform = job.get('platform', 'Unknown')
            platform_counts[platform] = platform_counts.get(platform, 0) + 1

        # Recent applications (last 30 days)
        recent_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        recent_applications = 0
        for job in jobs:
            try:
                app_date = datetime.fromisoformat(job.get('application_date', '').replace('Z', '+00:00'))
                if (recent_date - app_date).days <= 30:
                    recent_applications += 1
            except:
                pass
        
        return jsonify({
            'total_applications': total_applications,
            'status_breakdown': status_counts,
            'platform_breakdown': platform_counts,
            'recent_applications': recent_applications
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/options/<field_name>', methods=['GET', 'POST', 'DELETE'])
def manage_options(field_name):
    """Manage options for select fields"""
    try:
        columns = load_columns()
        column = next((col for col in columns if col['id'] == field_name), None)
        
        if not column or column['type'] != 'select':
            return jsonify({'error': 'Field not found or not a select field'}), 404
        
        if request.method == 'GET':
            return jsonify({'options': column.get('options', [])})
        
        elif request.method == 'POST':
            data = request.get_json()
            new_option = data.get('option', '').strip()
            
            if not new_option:
                return jsonify({'error': 'Option cannot be empty'}), 400
            
            if new_option not in column.get('options', []):
                column['options'].append(new_option)
                save_columns(columns)
            
            return jsonify({'success': True, 'options': column['options']})
        
        elif request.method == 'DELETE':
            data = request.get_json()
            option_to_delete = data.get('option', '').strip()
            
            if not option_to_delete:
                return jsonify({'error': 'Option to delete cannot be empty'}), 400
            
            if option_to_delete in column.get('options', []):
                column['options'].remove(option_to_delete)
                save_columns(columns)
                
                # Also remove this option from all jobs that use it
                jobs = load_jobs()
                for job in jobs:
                    if job.get(field_name) == option_to_delete:
                        job[field_name] = ''
                save_jobs(jobs)
                
                return jsonify({'success': True, 'options': column['options']})
            else:
                return jsonify({'error': 'Option not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/bulk-update', methods=['PUT'])
def bulk_update_jobs():
    """Bulk update multiple jobs"""
    try:
        data = request.get_json()
        job_ids = data.get('jobIds', [])
        updates = data.get('updates', {})
        
        if not job_ids:
            return jsonify({'error': 'No job IDs provided'}), 400
        
        if not updates:
            return jsonify({'error': 'No updates provided'}), 400
        
        jobs = load_jobs()
        columns = load_columns()
        column_ids = [col['id'] for col in columns]
        
        updated_count = 0
        for job in jobs:
            if job['id'] in job_ids:
                # Update only valid column fields
                for field, value in updates.items():
                    if field in column_ids:
                        job[field] = value
                updated_count += 1
        
        if updated_count == 0:
            return jsonify({'error': 'No valid jobs found to update'}), 404
        
        save_jobs(jobs)
        return jsonify({
            'success': True, 
            'message': f'Successfully updated {updated_count} jobs',
            'updated_count': updated_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/bulk-delete', methods=['DELETE'])
def bulk_delete_jobs():
    """Bulk delete multiple jobs"""
    try:
        data = request.get_json()
        job_ids = data.get('jobIds', [])
        
        if not job_ids:
            return jsonify({'error': 'No job IDs provided'}), 400
        
        jobs = load_jobs()
        original_count = len(jobs)
        
        # Remove jobs by ID
        jobs = [job for job in jobs if job['id'] not in job_ids]
        
        deleted_count = original_count - len(jobs)
        
        if deleted_count == 0:
            return jsonify({'error': 'No valid jobs found to delete'}), 404
        
        save_jobs(jobs)
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} jobs',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Setup scheduled email reminders
def setup_email_scheduler():
    """Setup scheduled email reminders"""
    if scheduler is None:
        print("Scheduler not available in serverless environment")
        return
        
    try:
        # Morning reminder at 11:00 AM
        scheduler.add_job(
            func=send_morning_reminder,
            trigger=CronTrigger(hour=11, minute=0),
            id='morning_reminder',
            name='Morning Job Application Reminder',
            replace_existing=True
        )
        
        # Afternoon reminder at 3:30 PM
        scheduler.add_job(
            func=send_afternoon_reminder,
            trigger=CronTrigger(hour=15, minute=30),
            id='afternoon_reminder',
            name='Afternoon Job Application Reminder',
            replace_existing=True
        )
        
        # Evening reminder at 9:30 PM
        scheduler.add_job(
            func=send_evening_reminder,
            trigger=CronTrigger(hour=21, minute=30),
            id='evening_reminder',
            name='Evening Job Application Reminder',
            replace_existing=True
        )
        
        print("Email scheduler setup completed successfully!")
        print("Scheduled reminders:")
        print("- Morning: 11:00 AM")
        print("- Afternoon: 3:30 PM")
        print("- Evening: 9:30 PM")
        
    except Exception as e:
        print(f"Error setting up email scheduler: {e}")

# API endpoint to send manual email
@app.route('/api/send-email', methods=['POST'])
def send_manual_email():
    """Send a manual email reminder"""
    try:
        data = request.get_json()
        email_type = data.get('type', 'summary')
        
        if email_type == 'morning':
            send_morning_reminder()
        elif email_type == 'afternoon':
            send_afternoon_reminder()
        elif email_type == 'evening':
            send_evening_reminder()
        else:
            # Send general summary
            subject = "📋 Job Application Summary"
            body = generate_job_summary()
            send_email(subject, body)
        
        return jsonify({'success': True, 'message': 'Email sent successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint to get scheduler status
@app.route('/api/scheduler-status', methods=['GET'])
def get_scheduler_status():
    """Get the status of scheduled jobs"""
    try:
        jobs = scheduler.get_jobs()
        job_list = []
        
        for job in jobs:
            job_list.append({
                'id': job.id,
                'name': job.name,
                'next_run': str(job.next_run_time) if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return jsonify({
            'scheduler_running': scheduler.running,
            'jobs': job_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Setup email scheduler when app starts
    setup_email_scheduler()
    app.run(debug=True, host='0.0.0.0', port=5000) 
