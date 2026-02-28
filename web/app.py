"""Flask web dashboard for Amazon Jobs Monitor v2."""

from flask import Flask, render_template, jsonify, request
import sys
import os
import threading
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.database import Database
from src.monitor import JobMonitor

# Global monitor thread
_monitor_thread = None

def start_monitor_in_background(config: Config):
    """Start the job monitor in a background thread."""
    global _monitor_thread
    
    def run_monitor():
        """Run the monitor in a separate thread."""
        # Suppress console output from monitor in web mode
        import logging
        logging.getLogger().setLevel(logging.WARNING)
        
        monitor = JobMonitor(config)
        asyncio.run(monitor.run())
    
    if _monitor_thread is None or not _monitor_thread.is_alive():
        _monitor_thread = threading.Thread(target=run_monitor, daemon=True)
        _monitor_thread.start()
        print("✓ Monitor started in background (fetching every 30s)")
        import time
        time.sleep(1)  # Give monitor time to start
    else:
        print("✓ Monitor already running")


def create_app(config: Config = None, start_monitor: bool = True):
    """Create and configure Flask app."""
    if config is None:
        config = Config()
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    
    db = Database(config.database_path)
    
    # Start monitor in background if requested
    if start_monitor:
        start_monitor_in_background(config)
    
    @app.route('/')
    def dashboard():
        """Main dashboard page."""
        stats = db.get_stats()
        return render_template('dashboard.html', stats=stats)
    
    @app.route('/api/jobs')
    def api_jobs():
        """API endpoint for jobs."""
        job_type = request.args.get('type', 'all')
        
        if job_type == 'part-time':
            jobs = db.get_jobs_by_type('part')
        elif job_type == 'full-time':
            jobs = db.get_jobs_by_type('full')
        elif job_type == 'flexible':
            jobs = db.get_flexible_jobs()
        elif job_type == 'under-20h':
            jobs = db.get_under_20h_jobs()
        else:
            jobs = db.get_all_jobs()
        
        return jsonify([job.to_db_dict() for job in jobs])
    
    @app.route('/api/stats')
    def api_stats():
        """API endpoint for statistics."""
        return jsonify(db.get_stats())
    
    @app.route('/api/history')
    def api_history():
        """API endpoint for job history."""
        limit = request.args.get('limit', 50, type=int)
        history = db.get_recent_history(limit=limit)
        return jsonify([
            {
                "id": h.id,
                "job_id": h.job_id,
                "change_type": h.change_type.value,
                "timestamp": h.timestamp.isoformat() if h.timestamp else None
            }
            for h in history
        ])
    
    @app.route('/jobs')
    def jobs_page():
        """Jobs listing page."""
        job_type = request.args.get('type', 'all')
        
        if job_type == 'part-time':
            jobs = db.get_jobs_by_type('part')
            title = "Part-Time Jobs"
        elif job_type == 'full-time':
            jobs = db.get_jobs_by_type('full')
            title = "Full-Time Jobs"
        elif job_type == 'flexible':
            jobs = db.get_flexible_jobs()
            title = "Flexible Jobs"
        elif job_type == 'under-20h':
            jobs = db.get_under_20h_jobs()
            title = "Under 20h Jobs"
        else:
            jobs = db.get_all_jobs()
            title = "All Jobs"
        
        return render_template('jobs.html', jobs=jobs, title=title, job_type=job_type)
    
    @app.route('/history')
    def history_page():
        """History page."""
        history = db.get_recent_history(limit=100)
        # Get job details for each history entry
        history_with_jobs = []
        for entry in history:
            job = db.get_job(entry.job_id)
            history_with_jobs.append({
                'entry': entry,
                'job': job
            })
        return render_template('history.html', history_with_jobs=history_with_jobs)
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
