"""Database management for Amazon Jobs Monitor v2."""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

from .models import Job, JobHistory, ChangeType, JobStatus


class Database:
    """SQLite database manager."""
    
    def __init__(self, db_path: str = "data/jobs.db"):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """Ensure database exists with proper schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Jobs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    job_title TEXT NOT NULL,
                    location_name TEXT NOT NULL,
                    city TEXT,
                    state TEXT,
                    postal_code TEXT,
                    employment_type TEXT,
                    job_type TEXT,
                    distance REAL,
                    is_flexible INTEGER DEFAULT 0,
                    is_under_20h INTEGER DEFAULT 0,
                    hours_per_week INTEGER,
                    status TEXT DEFAULT 'active',
                    first_seen TEXT,
                    last_seen TEXT,
                    last_updated TEXT,
                    raw_data TEXT
                )
            """)
            
            # Job history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS job_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    previous_values TEXT,
                    new_values TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs (job_id)
                )
            """)
            
            # Search configs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    location TEXT NOT NULL,
                    radius_miles REAL,
                    job_type TEXT,
                    keyword TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def save_job(self, job: Job) -> None:
        """Save or update a job."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO jobs (
                    job_id, job_title, location_name, city, state, postal_code,
                    employment_type, job_type, distance, is_flexible, is_under_20h,
                    hours_per_week, status, first_seen, last_seen, last_updated, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id,
                job.job_title,
                job.location_name or "",
                job.city or "",
                job.state or "",
                job.postal_code or "",
                job.employment_type or "",
                job.job_type or "",
                job.distance or 0.0,
                1 if job.is_flexible else 0,
                1 if job.is_under_20h else 0,
                job.hours_per_week,
                job.status.value,
                job.first_seen.isoformat(),
                job.last_seen.isoformat(),
                job.last_updated.isoformat(),
                json.dumps(job.raw_data)
            ))
            conn.commit()
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?",
                (job_id,)
            ).fetchone()
            
            if row:
                return self._row_to_job(row)
            return None
    
    def get_all_jobs(self, status: Optional[JobStatus] = None) -> List[Job]:
        """Get all jobs, optionally filtered by status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if status:
                rows = conn.execute(
                    "SELECT * FROM jobs WHERE status = ?",
                    (status.value,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM jobs").fetchall()
            
            return [self._row_to_job(row) for row in rows]
    
    def get_jobs_by_type(self, job_type: str) -> List[Job]:
        """Get jobs by type (part-time/full-time)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM jobs WHERE LOWER(job_type) LIKE ?",
                (f"%{job_type.lower()}%",)
            ).fetchall()
            return [self._row_to_job(row) for row in rows]
    
    def get_flexible_jobs(self) -> List[Job]:
        """Get flexible jobs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM jobs WHERE is_flexible = 1"
            ).fetchall()
            return [self._row_to_job(row) for row in rows]
    
    def get_under_20h_jobs(self) -> List[Job]:
        """Get under 20h jobs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM jobs WHERE is_under_20h = 1"
            ).fetchall()
            return [self._row_to_job(row) for row in rows]
    
    def mark_job_removed(self, job_id: str) -> None:
        """Mark a job as removed."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE jobs SET status = ? WHERE job_id = ?",
                (JobStatus.REMOVED.value, job_id)
            )
            conn.commit()
    
    def add_history(self, history: JobHistory) -> None:
        """Add a history entry."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO job_history (job_id, change_type, previous_values, new_values, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                history.job_id,
                history.change_type.value,
                json.dumps(history.previous_values),
                json.dumps(history.new_values),
                history.timestamp.isoformat()
            ))
            conn.commit()
    
    def get_job_history(self, job_id: str) -> List[JobHistory]:
        """Get history for a specific job."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM job_history WHERE job_id = ? ORDER BY timestamp DESC",
                (job_id,)
            ).fetchall()
            
            return [self._row_to_history(row) for row in rows]
    
    def get_recent_history(self, limit: int = 100) -> List[JobHistory]:
        """Get recent history entries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM job_history ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
            
            return [self._row_to_history(row) for row in rows]
    
    def cleanup_old_jobs(self, days: int = 30) -> int:
        """Remove jobs that haven't been seen for specified days."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM jobs WHERE last_seen < ?",
                (cutoff,)
            )
            conn.commit()
            return cursor.rowcount
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total_jobs = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE status = 'active'"
            ).fetchone()[0]
            
            part_time = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE LOWER(job_type) LIKE '%part%' AND status = 'active'"
            ).fetchone()[0]
            
            full_time = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE LOWER(job_type) LIKE '%full%' AND status = 'active'"
            ).fetchone()[0]
            
            flexible = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE is_flexible = 1 AND status = 'active'"
            ).fetchone()[0]
            
            under_20h = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE is_under_20h = 1 AND status = 'active'"
            ).fetchone()[0]
            
            with_hours = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE hours_per_week IS NOT NULL AND status = 'active'"
            ).fetchone()[0]
            
            removed = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE status = 'removed'"
            ).fetchone()[0]
            
            history_count = conn.execute(
                "SELECT COUNT(*) FROM job_history"
            ).fetchone()[0]
            
            return {
                "total_jobs": total_jobs,
                "part_time": part_time,
                "full_time": full_time,
                "flexible": flexible,
                "under_20h": under_20h,
                "with_hours": with_hours,
                "removed": removed,
                "history_entries": history_count,
            }
    
    def _row_to_job(self, row: sqlite3.Row) -> Job:
        """Convert database row to Job object."""
        data = dict(row)
        data["is_flexible"] = bool(data.get("is_flexible", 0))
        data["is_under_20h"] = bool(data.get("is_under_20h", 0))
        data["hours_per_week"] = data.get("hours_per_week")
        data["status"] = JobStatus(data.get("status", "active"))
        
        # Parse timestamps
        for field in ["first_seen", "last_seen", "last_updated"]:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        
        # Parse raw_data
        if data.get("raw_data"):
            try:
                data["raw_data"] = json.loads(data["raw_data"])
            except json.JSONDecodeError:
                data["raw_data"] = {}
        
        return Job(**data)
    
    def _row_to_history(self, row: sqlite3.Row) -> JobHistory:
        """Convert database row to JobHistory object."""
        data = dict(row)
        data["change_type"] = ChangeType(data["change_type"])
        data["previous_values"] = json.loads(data.get("previous_values", "{}"))
        data["new_values"] = json.loads(data.get("new_values", "{}"))
        
        if data.get("timestamp"):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        
        return JobHistory(**data)
