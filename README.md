# RTSP webcam restreaming

## Configuration

__Create file `settings.py` in project's root folder. There's its template below.__
```python
import datetime

# Global settings

VIDEO_FOLDER: str = ...  # Videos will be saved there on both remote and local servers.

# Remote server settings

REMOTE_PORT: int = ...
# Remote URL must include REMOTE_PORT, example: f"http://127.0.0.1:{REMOTE_PORT}/upload/"
REMOTE_URL: str = ...  
# Max size of storage in bytes, which may be taken by videos.
REMOTE_MAX_SIZE: int = ...

# Local server settings

RTSP_URL: str = ...
# Example: datetime.timedelta(minutes=10)
MAX_DURATION: datetime.timedelta = ...
# Max size of storage in bytes, which may be taken by videos.
LOCAL_MAX_SIZE: int = ...
```
