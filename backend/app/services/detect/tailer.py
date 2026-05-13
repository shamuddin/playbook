"""Log file tailer for real-time event ingestion.

Uses watchdog (when available) or simple polling to monitor log directories
and feed new events into the detection pipeline.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Callable, Optional

from app.core.config import get_settings
from app.services.detect.normalizer import NormalizationError, normalize_event


class LogTailer:
    """Tail log files and feed events to a callback.

    Usage (async context manager):
        async with LogTailer(on_event=handle_event) as tailer:
            await tailer.start()
            # ... run until shutdown
    """

    def __init__(
        self,
        log_dir: Optional[str] = None,
        glob_pattern: str = "*.log",
        poll_interval: float = 1.0,
        on_event: Optional[Callable[[dict], None]] = None,
    ):
        settings = get_settings()
        self.log_dir = Path(log_dir or settings.log_dir)
        self.glob_pattern = glob_pattern
        self.poll_interval = poll_interval
        self.on_event = on_event
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._file_positions: dict[str, int] = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
        return False

    async def start(self) -> None:
        """Start tailing in the background."""
        if self._running:
            return
        self._running = True
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        """Stop tailing."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _poll_loop(self) -> None:
        """Main polling loop."""
        while self._running:
            try:
                await self._scan_files()
            except Exception as exc:
                # Log but don't crash — tailer should be resilient
                print(f"[LogTailer] Error during scan: {exc}")
            await asyncio.sleep(self.poll_interval)

    async def _scan_files(self) -> None:
        """Scan log files for new lines."""
        if not self.log_dir.exists():
            return

        for log_file in self.log_dir.glob(self.glob_pattern):
            await self._read_new_lines(log_file)

    async def _read_new_lines(self, path: Path) -> None:
        """Read any new lines from a single file."""
        file_key = str(path)
        current_size = path.stat().st_size
        last_pos = self._file_positions.get(file_key, 0)

        if current_size < last_pos:
            # File was truncated — start over
            last_pos = 0

        if current_size == last_pos:
            return

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(last_pos)
                for line in f:
                    line = line.strip()
                    if line:
                        await self._process_line(line)
                self._file_positions[file_key] = f.tell()
        except OSError:
            pass

    async def _process_line(self, line: str) -> None:
        """Parse a log line and emit an event."""
        # Try JSON first
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            # Fallback: treat as plain text event
            raw = {"message": line, "source": "log_tailer", "timestamp": None}

        if self.on_event:
            try:
                event = normalize_event(raw)
                self.on_event(event)
            except NormalizationError:
                # Silently skip unnormalizable lines
                pass

    def ingest_file(self, path: Path) -> int:
        """Synchronously ingest an entire file (for demo/manual use).

        Returns the number of events processed.
        """
        count = 0
        if not path.exists():
            return 0

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                except json.JSONDecodeError:
                    raw = {"message": line, "source": "log_tailer"}

                if self.on_event:
                    try:
                        event = normalize_event(raw)
                        self.on_event(event)
                        count += 1
                    except NormalizationError:
                        pass
        return count
