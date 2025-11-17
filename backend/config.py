"""Centralized configuration for Flask server and LSM engine.

This module provides simple default values used by `backend.app` when
instantiating the `LSMTree`. You can edit these values here for
development, or override them by editing this file in your environment.
"""

# Server binding
HOST = "127.0.0.1"
PORT = 5000

# Storage and engine tuning
# Minimum number of entries kept in memtable before flushing to SST.
# The user requested that memtable hold at least 4 keys by default.
MEMTABLE_MAX_SIZE = 4

# Number of SST files that will trigger compaction when reached.
COMPACTION_THRESHOLD = 4

# Directory to store SST files
DATA_DIR = "data"

# Backwards-compatible placeholders (not used directly)
SERVER_CONFIG = {}
ENGINE_CONFIG = {}
