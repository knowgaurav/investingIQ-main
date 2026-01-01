"""
Queue Worker - DEPRECATED.

Note: Message processing is now handled by Azure Functions.
This file is kept for backward compatibility but is not used.
"""
import logging

logger = logging.getLogger(__name__)


def main():
    """Main entry point - deprecated."""
    logger.warning("queue_worker.py is deprecated - use Azure Functions instead")
    print("This worker is deprecated. Use Azure Functions for message processing.")


if __name__ == "__main__":
    main()
