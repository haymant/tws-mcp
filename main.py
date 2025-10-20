import uvicorn
from src.server import app
import os
import logging

# Filter to suppress known harmless ib-async warnings
class IBAsyncTickTypeFilter(logging.Filter):
    """Suppress tickType warnings from ib-async that don't affect functionality."""
    def filter(self, record):
        # Suppress "tickString with tickType XX: unhandled value" errors
        # These are informational - the library receives tick types it doesn't recognize
        # but this doesn't affect the streaming functionality
        if "tickString with tickType" in record.getMessage() and "unhandled value" in record.getMessage():
            return False
        return True

if __name__ == "__main__":
    # Apply the filter to suppress harmless tickType warnings
    # The ib_async library uses logger "ib_async.wrapper" (see wrapper.py:250)
    tick_filter = IBAsyncTickTypeFilter()
    
    # Apply to the specific ib_async.wrapper logger
    ib_logger = logging.getLogger("ib_async.wrapper")
    ib_logger.addFilter(tick_filter)
    
    # Also apply to root logger as backup
    logging.getLogger().addFilter(tick_filter)
    
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", 8000))
    uvicorn.run(app, host=host, port=port)
