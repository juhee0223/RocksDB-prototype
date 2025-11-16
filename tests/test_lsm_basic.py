"""Basic put/get behaviors for proto LSM."""

from proto_lsm.lsm_engine import LSMTree as SimpleLSMTree


def test_put_get_basic(tmp_path):
    db = SimpleLSMTree({"data_dir": tmp_path})
    db.put("a", "1")
    db.put("b", "2")
    assert db.get("a") == "1"
    assert db.get("b") == "2"


def test_flush_trigger(tmp_path):
    db = SimpleLSMTree(
        {"data_dir": tmp_path, "memtable_max_size": 2, "compaction_threshold": 100}
    )
    db.put("k1", "v1")
    db.put("k2", "v2")  # triggers flush when next insert happens
    db.put("k3", "v3")

    sst_files = list(tmp_path.glob("sst_*.txt"))
    assert sst_files, "expected at least one SST after flush"
