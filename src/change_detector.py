"""Job change detection for Amazon Jobs Monitor v2."""

from datetime import datetime
from typing import List, Dict, Any

from .models import Job, JobChanges, JobHistory, ChangeType
from .database import Database


class ChangeDetector:
    """Detect changes between fetched jobs and stored jobs."""
    
    def __init__(self, database: Database):
        self.db = database
    
    def detect_changes(self, fetched_jobs: List[Job]) -> JobChanges:
        """
        Detect changes between fetched jobs and stored jobs.
        
        Returns JobChanges with new, updated, and removed jobs.
        """
        # Create lookup maps
        fetched_map: Dict[str, Job] = {j.job_id: j for j in fetched_jobs}
        
        # Get all currently active jobs from database
        stored_jobs = self.db.get_all_jobs(status=None)
        stored_active = {j.job_id: j for j in stored_jobs if j.status.value == "active"}
        
        changes = JobChanges()
        
        # Find new and updated jobs
        for job_id, fetched_job in fetched_map.items():
            if job_id not in stored_active:
                # New job
                fetched_job.first_seen = datetime.utcnow()
                fetched_job.last_seen = datetime.utcnow()
                changes.new_jobs.append(fetched_job)
                
                # Record history
                history = JobHistory(
                    job_id=job_id,
                    change_type=ChangeType.NEW,
                    new_values=fetched_job.to_db_dict()
                )
                self.db.add_history(history)
            else:
                # Existing job - check for updates
                stored_job = stored_active[job_id]
                updated_fields = self._get_changes(stored_job, fetched_job)
                
                if updated_fields and not self._was_updated_today(job_id):
                    # Job was updated (and not already updated today)
                    fetched_job.first_seen = stored_job.first_seen
                    fetched_job.last_seen = datetime.utcnow()
                    fetched_job.last_updated = datetime.utcnow()
                    changes.updated_jobs.append(fetched_job)
                    
                    # Record history
                    history = JobHistory(
                        job_id=job_id,
                        change_type=ChangeType.UPDATED,
                        previous_values={k: stored_job.to_db_dict().get(k) for k in updated_fields.keys()},
                        new_values=updated_fields
                    )
                    self.db.add_history(history)
                elif updated_fields:
                    # Changes detected but already updated today - just save without recording history
                    fetched_job.first_seen = stored_job.first_seen
                    fetched_job.last_seen = datetime.utcnow()
                    fetched_job.last_updated = stored_job.last_updated
                    self.db.save_job(fetched_job)
                else:
                    # No changes, just update last_seen
                    fetched_job.first_seen = stored_job.first_seen
                    fetched_job.last_seen = datetime.utcnow()
                    fetched_job.last_updated = stored_job.last_updated
                
                # Save the job (whether updated or not)
                self.db.save_job(fetched_job)
        
        # Find removed jobs
        for job_id, stored_job in stored_active.items():
            if job_id not in fetched_map:
                # Job was removed
                changes.removed_jobs.append(stored_job)
                self.db.mark_job_removed(job_id)
                
                # Record history
                history = JobHistory(
                    job_id=job_id,
                    change_type=ChangeType.REMOVED,
                    previous_values=stored_job.to_db_dict()
                )
                self.db.add_history(history)
        
        # Save new jobs
        for job in changes.new_jobs:
            self.db.save_job(job)
        
        return changes
    
    def _was_updated_today(self, job_id: str) -> bool:
        """Check if job was already updated today."""
        from datetime import date
        today = date.today().isoformat()
        
        # Get recent history for this job
        history = self.db.get_job_history(job_id)
        for entry in history:
            if entry.change_type == ChangeType.UPDATED:
                entry_date = entry.timestamp.date().isoformat() if entry.timestamp else None
                if entry_date == today:
                    return True
        return False
    
    def _get_changes(self, old: Job, new: Job) -> Dict[str, Any]:
        """
        Get fields that have changed between old and new job.
        
        Returns dict of changed field names and their new values.
        Only includes meaningful fields (not distance which fluctuates).
        """
        changes = {}
        
        old_dict = old.to_db_dict()
        new_dict = new.to_db_dict()
        
        # Only compare meaningful fields (exclude distance which changes frequently)
        compare_fields = [
            "job_title", "location_name", "city", "state",
            "postal_code", "employment_type", "job_type"
        ]
        
        for field in compare_fields:
            old_val = old_dict.get(field)
            new_val = new_dict.get(field)
            # Treat None and empty string as equal
            if (old_val or None) != (new_val or None):
                changes[field] = new_val
        
        return changes
