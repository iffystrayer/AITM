"""
File system monitoring for real-time code analysis.
"""

import os
import time
import asyncio
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any
from enum import Enum
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from app.models.quality import QualityIssue


class FileChangeType(str, Enum):
    """Types of file system changes."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileChangeEvent:
    """Represents a file system change event."""
    event_type: FileChangeType
    file_path: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    old_path: Optional[str] = None  # For move events
    file_size: Optional[int] = None
    is_directory: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize computed fields."""
        if os.path.exists(self.file_path) and not self.is_directory:
            try:
                self.file_size = os.path.getsize(self.file_path)
            except (OSError, IOError):
                self.file_size = None


class FileSystemMonitor:
    """Monitors file system changes for real-time code analysis."""
    
    def __init__(self, project_path: str, project_id: str):
        self.project_path = Path(project_path).resolve()
        self.project_id = project_id
        self.observer = Observer()
        self.event_handler = CodeAnalysisEventHandler(self)
        self.is_monitoring = False
        
        # Configuration
        self.watched_extensions: Set[str] = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c',
            '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.scala',
            '.html', '.css', '.scss', '.less', '.sql', '.yaml', '.yml',
            '.json', '.xml', '.md', '.sh', '.bash', '.zsh'
        }
        
        self.ignored_patterns: Set[str] = {
            '__pycache__', '.git', '.svn', '.hg', 'node_modules',
            '.pytest_cache', '.mypy_cache', '.coverage', 'dist',
            'build', '.DS_Store', '*.pyc', '*.pyo', '*.pyd',
            '*.so', '*.dll', '*.dylib', '*.egg-info', '.venv',
            'venv', '.env', '.idea', '.vscode'
        }
        
        self.ignored_directories: Set[str] = {
            '__pycache__', '.git', '.svn', '.hg', 'node_modules',
            '.pytest_cache', '.mypy_cache', 'dist', 'build',
            '.venv', 'venv', '.idea', '.vscode', '.tox'
        }
        
        # Event callbacks
        self.change_callbacks: List[Callable[[FileChangeEvent], None]] = []
        self.analysis_callbacks: List[Callable[[str, List[QualityIssue]], None]] = []
        
        # Event queue for batch processing
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.batch_size = 10
        self.batch_timeout = 5.0  # seconds
        
        # Statistics
        self.stats = {
            'events_processed': 0,
            'files_analyzed': 0,
            'analysis_errors': 0,
            'start_time': None,
            'last_event_time': None
        }
    
    def add_change_callback(self, callback: Callable[[FileChangeEvent], None]) -> None:
        """Add a callback for file change events."""
        self.change_callbacks.append(callback)
    
    def add_analysis_callback(self, callback: Callable[[str, List[QualityIssue]], None]) -> None:
        """Add a callback for analysis results."""
        self.analysis_callbacks.append(callback)
    
    def should_monitor_file(self, file_path: str) -> bool:
        """Check if a file should be monitored."""
        path = Path(file_path)
        
        # Check extension
        if path.suffix.lower() not in self.watched_extensions:
            return False
        
        # Check ignored patterns
        for pattern in self.ignored_patterns:
            if pattern in str(path):
                return False
        
        # Check if in ignored directory
        for part in path.parts:
            if part in self.ignored_directories:
                return False
        
        return True
    
    def should_monitor_directory(self, dir_path: str) -> bool:
        """Check if a directory should be monitored."""
        path = Path(dir_path)
        
        # Check ignored directories
        for part in path.parts:
            if part in self.ignored_directories:
                return False
        
        return True
    
    def start_monitoring(self) -> None:
        """Start monitoring the file system."""
        if self.is_monitoring:
            return
        
        self.observer.schedule(
            self.event_handler,
            str(self.project_path),
            recursive=True
        )
        
        self.observer.start()
        self.is_monitoring = True
        self.stats['start_time'] = datetime.now(timezone.utc)
        
        # Start event processing task
        asyncio.create_task(self._process_events())
    
    def stop_monitoring(self) -> None:
        """Stop monitoring the file system."""
        if not self.is_monitoring:
            return
        
        self.observer.stop()
        self.observer.join()
        self.is_monitoring = False
    
    async def _process_events(self) -> None:
        """Process file change events in batches."""
        batch = []
        last_batch_time = time.time()
        
        while self.is_monitoring:
            try:
                # Wait for events with timeout
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=1.0
                    )
                    batch.append(event)
                except asyncio.TimeoutError:
                    pass
                
                current_time = time.time()
                
                # Process batch if it's full or timeout reached
                if (len(batch) >= self.batch_size or 
                    (batch and current_time - last_batch_time >= self.batch_timeout)):
                    
                    await self._process_event_batch(batch)
                    batch.clear()
                    last_batch_time = current_time
                
            except Exception as e:
                print(f"Error processing events: {e}")
                self.stats['analysis_errors'] += 1
    
    async def _process_event_batch(self, events: List[FileChangeEvent]) -> None:
        """Process a batch of file change events."""
        # Group events by file to avoid duplicate processing
        file_events = {}
        for event in events:
            if event.file_path not in file_events:
                file_events[event.file_path] = []
            file_events[event.file_path].append(event)
        
        # Process each file's events
        for file_path, file_event_list in file_events.items():
            try:
                # Get the latest event for this file
                latest_event = max(file_event_list, key=lambda e: e.timestamp)
                
                # Notify callbacks
                for callback in self.change_callbacks:
                    try:
                        callback(latest_event)
                    except Exception as e:
                        print(f"Error in change callback: {e}")
                
                self.stats['events_processed'] += 1
                self.stats['last_event_time'] = latest_event.timestamp
                
            except Exception as e:
                print(f"Error processing file events for {file_path}: {e}")
                self.stats['analysis_errors'] += 1
    
    def _queue_event(self, event: FileChangeEvent) -> None:
        """Queue a file change event for processing."""
        try:
            self.event_queue.put_nowait(event)
        except asyncio.QueueFull:
            print("Event queue is full, dropping event")
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        stats = self.stats.copy()
        if stats['start_time']:
            uptime = datetime.now(timezone.utc) - stats['start_time']
            stats['uptime_seconds'] = uptime.total_seconds()
        
        stats['is_monitoring'] = self.is_monitoring
        stats['queue_size'] = self.event_queue.qsize()
        stats['watched_extensions'] = list(self.watched_extensions)
        stats['ignored_patterns'] = list(self.ignored_patterns)
        
        return stats
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the file monitor."""
        if 'watched_extensions' in config:
            self.watched_extensions = set(config['watched_extensions'])
        
        if 'ignored_patterns' in config:
            self.ignored_patterns = set(config['ignored_patterns'])
        
        if 'ignored_directories' in config:
            self.ignored_directories = set(config['ignored_directories'])
        
        if 'batch_size' in config:
            self.batch_size = config['batch_size']
        
        if 'batch_timeout' in config:
            self.batch_timeout = config['batch_timeout']


class CodeAnalysisEventHandler(FileSystemEventHandler):
    """Handles file system events for code analysis."""
    
    def __init__(self, monitor: FileSystemMonitor):
        super().__init__()
        self.monitor = monitor
    
    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if event.is_directory:
            if not self.monitor.should_monitor_directory(event.src_path):
                return
        else:
            if not self.monitor.should_monitor_file(event.src_path):
                return
        
        change_event = FileChangeEvent(
            event_type=FileChangeType.CREATED,
            file_path=event.src_path,
            is_directory=event.is_directory
        )
        
        self.monitor._queue_event(change_event)
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if event.is_directory:
            return  # Ignore directory modifications
        
        if not self.monitor.should_monitor_file(event.src_path):
            return
        
        change_event = FileChangeEvent(
            event_type=FileChangeType.MODIFIED,
            file_path=event.src_path,
            is_directory=event.is_directory
        )
        
        self.monitor._queue_event(change_event)
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events."""
        if event.is_directory:
            if not self.monitor.should_monitor_directory(event.src_path):
                return
        else:
            if not self.monitor.should_monitor_file(event.src_path):
                return
        
        change_event = FileChangeEvent(
            event_type=FileChangeType.DELETED,
            file_path=event.src_path,
            is_directory=event.is_directory
        )
        
        self.monitor._queue_event(change_event)
    
    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move events."""
        if event.is_directory:
            if not (self.monitor.should_monitor_directory(event.src_path) or
                    self.monitor.should_monitor_directory(event.dest_path)):
                return
        else:
            if not (self.monitor.should_monitor_file(event.src_path) or
                    self.monitor.should_monitor_file(event.dest_path)):
                return
        
        change_event = FileChangeEvent(
            event_type=FileChangeType.MOVED,
            file_path=event.dest_path,
            old_path=event.src_path,
            is_directory=event.is_directory
        )
        
        self.monitor._queue_event(change_event)


class RealTimeAnalysisCoordinator:
    """Coordinates real-time analysis based on file changes."""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.monitors: Dict[str, FileSystemMonitor] = {}
        self.analysis_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        
        # Debouncing to avoid excessive analysis
        self.debounce_delay = 2.0  # seconds
        self.pending_analyses: Dict[str, float] = {}  # file_path -> timestamp
    
    def add_project_monitor(self, project_path: str) -> FileSystemMonitor:
        """Add a file system monitor for a project."""
        monitor = FileSystemMonitor(project_path, self.project_id)
        monitor.add_change_callback(self._on_file_change)
        self.monitors[project_path] = monitor
        return monitor
    
    def start_monitoring(self) -> None:
        """Start monitoring all registered projects."""
        for monitor in self.monitors.values():
            monitor.start_monitoring()
        
        self.is_running = True
        asyncio.create_task(self._process_analysis_queue())
    
    def stop_monitoring(self) -> None:
        """Stop monitoring all projects."""
        for monitor in self.monitors.values():
            monitor.stop_monitoring()
        
        self.is_running = False
    
    def _on_file_change(self, event: FileChangeEvent) -> None:
        """Handle file change events."""
        if event.event_type in [FileChangeType.MODIFIED, FileChangeType.CREATED]:
            # Schedule analysis with debouncing
            current_time = time.time()
            self.pending_analyses[event.file_path] = current_time
            
            # Schedule debounced analysis
            asyncio.create_task(self._debounced_analysis(event.file_path, current_time))
    
    async def _debounced_analysis(self, file_path: str, schedule_time: float) -> None:
        """Perform debounced analysis of a file."""
        await asyncio.sleep(self.debounce_delay)
        
        # Check if this is still the latest schedule for this file
        if (file_path in self.pending_analyses and 
            self.pending_analyses[file_path] == schedule_time):
            
            # Queue for analysis
            await self.analysis_queue.put(file_path)
            del self.pending_analyses[file_path]
    
    async def _process_analysis_queue(self) -> None:
        """Process the analysis queue."""
        while self.is_running:
            try:
                file_path = await asyncio.wait_for(
                    self.analysis_queue.get(),
                    timeout=1.0
                )
                
                # Trigger analysis (this would integrate with the scanning framework)
                print(f"Analyzing file: {file_path}")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing analysis queue: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        stats = {
            'total_monitors': len(self.monitors),
            'is_running': self.is_running,
            'pending_analyses': len(self.pending_analyses),
            'queue_size': self.analysis_queue.qsize(),
            'monitors': {}
        }
        
        for path, monitor in self.monitors.items():
            stats['monitors'][path] = monitor.get_monitoring_stats()
        
        return stats