from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

@dataclass
class StandardJob:
    """Standardized job opportunity representation across all discovery sources."""
    title: str
    description: str
    platform: str
    url: Optional[str] = None
    budget: float = 0.0
    currency: str = "INR"
    date_posted: str = ""
    deadline: str = ""
    client_info: str = ""
    skills_required: List[str] = field(default_factory=list)
    discovery_source: str = "adapter"
    date_discovered: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    is_sample: int = 0
    category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts StandardJob instance to a dictionary compatible with add_job()."""
        return {
            "title": self.title,
            "description": self.description,
            "platform": self.platform,
            "url": self.url,
            "budget": self.budget,
            "currency": self.currency,
            "date_posted": self.date_posted or datetime.now().strftime("%Y-%m-%d"),
            "deadline": self.deadline,
            "client_info": self.client_info,
            "skills_required": self.skills_required,
            "discovery_source": self.discovery_source,
            "date_discovered": self.date_discovered,
            "is_sample": self.is_sample,
            "category": self.category
        }

class BaseSourceAdapter(ABC):
    """Abstract base class for all modular discovery adapters."""

    def __init__(self, source_id: str, source_name: str, is_enabled: bool = True):
        self.source_id = source_id
        self.source_name = source_name
        self.is_enabled = is_enabled

    @abstractmethod
    def fetch_jobs(self, search_terms: List[str], max_results: int = 10) -> List[StandardJob]:
        """Fetches and standardizes opportunities matching given search terms."""
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Checks source health and reports integration status."""
        pass
