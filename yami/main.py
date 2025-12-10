"""Console entry point"""

import logging
from yami.music import MusicPlayer

import sys
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def entry(): 
    try:
        logger.info("Starting Yami music player...")
        app = MusicPlayer()
        app.mainloop()
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == "__main__":
    entry()
