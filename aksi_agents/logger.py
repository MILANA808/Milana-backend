"""
AKSI Logger - Centralized logging and monitoring
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from collections import deque
from datetime import datetime


class AKSILogger:
    """Centralized logger for AKSI operations"""

    def __init__(self, log_dir: str = "logs", max_memory_logs: int = 1000):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.max_memory_logs = max_memory_logs
        self._memory_logs = deque(maxlen=max_memory_logs)
        self.log_file = self.log_dir / f"aksi_{datetime.now().strftime('%Y%m%d')}.jsonl"

    def log(self, event: str, payload: Optional[Dict[str, Any]] = None, level: str = "INFO"):
        """Log an event with optional payload"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "unix_ts": int(time.time()),
            "level": level,
            "event": event,
            "payload": payload or {}
        }

        # Store in memory
        self._memory_logs.append(entry)

        # Write to file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return entry

    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent logs from memory"""
        return list(self._memory_logs)[-limit:]

    def get_logs_by_event(self, event: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get logs filtered by event type"""
        return [log for log in self._memory_logs if log.get("event") == event][-limit:]

    def export_logs(self, start_date: Optional[str] = None) -> str:
        """Export logs as JSONL string"""
        if start_date:
            # Filter by date if provided
            logs = [log for log in self._memory_logs if log.get("timestamp", "").startswith(start_date)]
        else:
            logs = list(self._memory_logs)

        return "\n".join(json.dumps(log, ensure_ascii=False) for log in logs)
