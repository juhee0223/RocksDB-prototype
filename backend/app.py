"""Flask entry point exposing LSM operations."""

import os
from typing import Any, Dict

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from backend import config
from proto_lsm.lsm_engine import LSMTree as SimpleLSMTree

app = Flask(__name__)


def _create_engine() -> SimpleLSMTree:
    """Instantiate the LSM engine with configuration defaults."""
    data_dir = getattr(config, "DATA_DIR", os.path.join(os.getcwd(), "data"))
    memtable_size = getattr(config, "MEMTABLE_MAX_SIZE", 50)
    compaction_threshold = getattr(config, "COMPACTION_THRESHOLD", 4)
    engine_cfg: Dict[str, Any] = {
        "data_dir": data_dir,
        "memtable_max_size": memtable_size,
        "compaction_threshold": compaction_threshold,
    }
    return SimpleLSMTree(engine_cfg)


db = _create_engine()


@app.errorhandler(HTTPException)
def handle_http_exception(exc: HTTPException):
    return jsonify({"error": exc.description}), exc.code


@app.errorhandler(Exception)
def handle_unexpected_exception(exc: Exception):  # pragma: no cover - safeguard
    return jsonify({"error": "internal server error"}), 500


@app.route("/put", methods=["POST"])
def put():
    payload = request.get_json(silent=True) or {}
    key = payload.get("key")
    value = payload.get("value")
    if key is None or value is None:
        return jsonify({"error": "key and value are required"}), 400

    db.put(key, value)
    return jsonify({"status": "ok", "key": key, "value": value})


@app.route("/get", methods=["GET"])
def get_value():
    key = request.args.get("key")
    if key is None:
        return jsonify({"error": "key is required"}), 400

    value = db.get(key)
    if value is None:
        return jsonify({"found": False, "key": key})
    return jsonify({"found": True, "key": key, "value": value})


@app.route("/stats", methods=["GET"])
def stats():
    snapshot = db.stats()
    response = {
        "memtable_size": snapshot.get("memtable_size", 0),
        "num_sst_files": snapshot.get("sst_count", 0),
    }
    return jsonify(response)


if __name__ == "__main__":
    host = getattr(config, "HOST", "127.0.0.1")
    port = getattr(config, "PORT", 5000)
    app.run(host=host, port=port, debug=True)
