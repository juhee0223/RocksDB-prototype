"""Simplified LSM-tree engine that backs the prototype key/value store."""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

try:
    # compact_all is not implemented yet, but the call site should exist.
    from proto_lsm.compaction import compact_all  # type: ignore
except (ImportError, AttributeError):  # pragma: no cover
    def compact_all(_data_dir, _seqs):  # type: ignore
        """Fallback stub used until compaction implementation arrives."""
        return None


class LSMTree:
    """Entry point for put/get operations and background maintenance."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.data_dir = self.config.get("data_dir") or os.path.join(os.getcwd(), "data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.memtable_max_size = int(self.config.get("memtable_max_size", 50))
        if self.memtable_max_size <= 0:
            self.memtable_max_size = 1

        self.compaction_threshold = int(self.config.get("compaction_threshold", 4))
        if self.compaction_threshold < 0:
            self.compaction_threshold = 0

        self.memtable: Dict = {}
        self.sst_files: List[Tuple[int, str]] = []
        self.sst_seq = 0
        self._load_existing_ssts()
        self.schedule_compaction()

    def put(self, key, value) -> None:
        """Store a key/value pair in the memtable and flush when needed."""
        self.memtable[key] = value
        if len(self.memtable) >= self.memtable_max_size:
            self.flush_memtable()

    def get(self, key):
        """Retrieve a value by consulting the memtable followed by SSTs."""
        if key in self.memtable:
            return self.memtable[key]

        str_key = str(key)
        for _, path in reversed(self.sst_files):
            value = self._read_value_from_sst(path, str_key)
            if value is not None:
                return value
        return None

    def stats(self) -> Dict:
        """Expose basic state for debugging and UI display."""
        return {
            "memtable_size": len(self.memtable),
            "memtable_max_size": self.memtable_max_size,
            "sst_count": len(self.sst_files),
            "sst_files": [path for _, path in self.sst_files],
            "next_sst_seq": self.sst_seq,
        }

    def flush_memtable(self) -> None:
        """Persist the memtable into a new SST file inside data_dir."""
        if not self.memtable:
            return

        entries = sorted(self.memtable.items(), key=lambda item: str(item[0]))
        filename = f"sst_{self.sst_seq}.txt"
        file_path = os.path.join(self.data_dir, filename)

        with open(file_path, "w", encoding="utf-8") as sst_file:
            for key, value in entries:
                sst_file.write(f"{key}\t{value}\n")

        self.sst_files.append((self.sst_seq, file_path))
        self.memtable.clear()
        self.sst_seq += 1
        self.schedule_compaction()

    def schedule_compaction(self) -> None:
        """Invoke compaction when the SST count crosses the configured limit."""
        if not self.compaction_threshold:
            return

        if len(self.sst_files) >= self.compaction_threshold:
            sequences = [seq for seq, _ in self.sst_files]
            try:
                compact_all(self.data_dir, sequences)
            except NotImplementedError:
                pass

    def _load_existing_ssts(self) -> None:
        """Scan the data directory and rebuild SST metadata."""
        existing: List[Tuple[int, str]] = []
        highest = -1

        for name in os.listdir(self.data_dir):
            if not (name.startswith("sst_") and name.endswith(".txt")):
                continue
            seq_token = name[4:-4]
            if not seq_token.isdigit():
                continue
            seq = int(seq_token)
            file_path = os.path.join(self.data_dir, name)
            existing.append((seq, file_path))
            highest = max(highest, seq)

        existing.sort(key=lambda item: item[0])
        self.sst_files = existing
        self.sst_seq = (highest + 1) if highest >= 0 else 0

    def _read_value_from_sst(self, file_path: str, key: str):
        """Search for a key inside an SST file."""
        try:
            with open(file_path, "r", encoding="utf-8") as sst_file:
                for line in sst_file:
                    stripped = line.rstrip("\n")
                    if "\t" not in stripped:
                        continue
                    entry_key, entry_value = stripped.split("\t", 1)
                    if entry_key == key:
                        return entry_value
        except FileNotFoundError:
            # The SST could have been deleted by compaction; ignore the miss.
            return None
        return None
