"""Compaction helpers for the prototype LSM engine."""

import os
from typing import Dict, List, Optional


def compact_all(data_dir: str, seqs: List[int]) -> Optional[int]:
    """Merge the provided SST sequences into a single sorted SST file."""
    if not seqs:
        return None

    merged: Dict[str, str] = {}
    existing_seqs: List[int] = []

    for seq in sorted(seqs):
        path = _sst_path(data_dir, seq)
        if not os.path.exists(path):
            continue
        existing_seqs.append(seq)
        entries = _read_sst_file(path)
        # Later sequences should override earlier ones.
        merged.update(entries)

    if not existing_seqs or not merged:
        return None

    new_seq = max(existing_seqs) + 1
    new_path = _sst_path(data_dir, new_seq)
    _write_sst_file(new_path, merged)

    for seq in existing_seqs:
        _remove_sst_file(_sst_path(data_dir, seq))

    return new_seq


def _sst_path(data_dir: str, seq: int) -> str:
    return os.path.join(data_dir, f"sst_{seq}.txt")


def _read_sst_file(path: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as sst_file:
            for line in sst_file:
                stripped = line.rstrip("\n")
                if "\t" not in stripped:
                    continue
                key, value = stripped.split("\t", 1)
                data[key] = value
    except FileNotFoundError:
        return {}
    return data


def _write_sst_file(path: str, entries: Dict[str, str]) -> None:
    sorted_items = sorted(entries.items(), key=lambda item: item[0])
    with open(path, "w", encoding="utf-8") as sst_file:
        for key, value in sorted_items:
            sst_file.write(f"{key}\t{value}\n")


def _remove_sst_file(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        return
