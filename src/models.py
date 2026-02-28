"""Data models for Amazon Jobs Monitor v2."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class JobType(str, Enum):
    """Job type enumeration."""
    PART_TIME = "part-time"
    FULL_TIME = "full-time"
    FLEXIBLE = "flexible"


class JobStatus(str, Enum):
    """Job status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    REMOVED = "removed"


class ChangeType(str, Enum):
    """Change type enumeration."""
    NEW = "new"
    UPDATED = "updated"
    REMOVED = "removed"


class Job(BaseModel):
    """Job model representing a job listing."""
    
    job_id: str = Field(..., alias="jobId")
    job_title: str = Field(..., alias="jobTitle")
    location_name: Optional[str] = Field("", alias="locationName")
    city: Optional[str] = ""
    state: Optional[str] = ""
    postal_code: Optional[str] = Field("", alias="postalCode")
    employment_type: Optional[str] = Field("", alias="employmentType")
    job_type: Optional[str] = Field("", alias="jobType")
    distance: Optional[float] = 0.0
    
    # Computed fields
    is_flexible: bool = False
    is_under_20h: bool = False
    hours_per_week: Optional[int] = None  # Extracted from job title
    status: JobStatus = JobStatus.ACTIVE
    
    # Timestamps
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Raw data for reference
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @property
    def is_part_time(self) -> bool:
        """Check if job is part-time."""
        return "part" in self.job_type.lower() or "part" in self.employment_type.lower()
    
    @property
    def is_full_time(self) -> bool:
        """Check if job is full-time."""
        return "full" in self.job_type.lower() or "full" in self.employment_type.lower()
    
    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "job_id": self.job_id,
            "job_title": self.job_title,
            "location_name": self.location_name,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "employment_type": self.employment_type,
            "job_type": self.job_type,
            "distance": self.distance,
            "is_flexible": self.is_flexible,
            "is_under_20h": self.is_under_20h,
            "hours_per_week": self.hours_per_week,
            "status": self.status.value,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "raw_data": str(self.raw_data),
        }
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "Job":
        """Create Job from API response data."""
        import re
        job = cls(**data)
        job.raw_data = data
        
        # Compute flexible status
        title_lower = job.job_title.lower()
        job.is_flexible = any(
            keyword in title_lower
            for keyword in ["flexible", "variable", "shifts to suit"]
        )
        
        # Compute under 20h status
        job.is_under_20h = any(
            keyword in title_lower
            for keyword in ["under 20", "< 20", "less than 20", "up to 20"]
        )
        
        # Extract hours per week from title (e.g., "40 hours", "20hrs/week", "15 hr")
        hours_patterns = [
            r'(\d+)\s*hours?\s*(?:per\s*)?week',
            r'(\d+)\s*hrs?[/\s]*week',
            r'(\d+)\s*hr[/\s]*wk',
            r'(\d+)\s*hrs?',
        ]
        for pattern in hours_patterns:
            match = re.search(pattern, title_lower)
            if match:
                hours = int(match.group(1))
                if 1 <= hours <= 80:  # Reasonable range for work hours
                    job.hours_per_week = hours
                    break
        
        return job


class JobHistory(BaseModel):
    """Job history entry for tracking changes."""
    
    id: Optional[int] = None
    job_id: str
    change_type: ChangeType
    previous_values: Dict[str, Any] = Field(default_factory=dict)
    new_values: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SearchConfig(BaseModel):
    """Search configuration."""
    
    id: Optional[int] = None
    name: str = "default"
    location: str = "Leeds, UK"
    radius_miles: float = 50.0
    job_type: Optional[JobType] = None
    keyword: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobSearchResult(BaseModel):
    """Result of a job search."""
    
    jobs: List[Job] = Field(default_factory=list)
    total_count: int = 0
    next_token: Optional[str] = None
    search_location: str = ""
    search_radius: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class JobChanges(BaseModel):
    """Collection of job changes detected."""
    
    new_jobs: List[Job] = Field(default_factory=list)
    updated_jobs: List[Job] = Field(default_factory=list)
    removed_jobs: List[Job] = Field(default_factory=list)
    
    @property
    def has_changes(self) -> bool:
        """Check if any changes were detected."""
        return bool(self.new_jobs or self.updated_jobs or self.removed_jobs)
    
    @property
    def summary(self) -> str:
        """Get a summary of changes."""
        return (
            f"New: {len(self.new_jobs)}, "
            f"Updated: {len(self.updated_jobs)}, "
            f"Removed: {len(self.removed_jobs)}"
        )
