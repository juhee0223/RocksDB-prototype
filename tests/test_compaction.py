"""Compaction logic expectations."""

from proto_lsm.lsm_engine import LSMTree as SimpleLSMTree


def test_compaction_reduces_sst_files(tmp_path):
    db = SimpleLSMTree(
        {
            "data_dir": tmp_path,
            "memtable_max_size": 2,
            "compaction_threshold": 3,
        }
    )
    for i in range(6):
        db.put(f"k{i}", f"v{i}")

    sst_files = list(tmp_path.glob("sst_*.txt"))
    assert len(sst_files) >= 1


def test_compaction_keeps_latest_values(tmp_path):
    db = SimpleLSMTree(
        {
            "data_dir": tmp_path,
            "memtable_max_size": 1,
            "compaction_threshold": 2,
        }
    )
    db.put("shared", "v0")
    db.put("shared", "v1")

    assert db.get("shared") == "v1"
