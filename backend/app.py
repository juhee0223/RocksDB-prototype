"""Flask entry point exposing LSM operations."""

import os
from typing import Any, Dict
import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

# from backend import config
from . import config
from proto_lsm.lsm_engine import LSMTree as SimpleLSMTree

# Serve frontend static files from the repository `frontend/` directory so
# the app can provide both UI and API from the same origin during development.
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app = Flask(__name__, static_folder=frontend_dir, static_url_path="")
# Development: enable CORS so frontend served from another port can call API
CORS(app)


@app.route("/")
def index():
    """Serve the SPA entrypoint from the frontend static folder."""
    return app.send_static_file("index.html")


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
    if value is None:
        return jsonify({"error": "value is required"}), 400

    generated = False
    if key is None or str(key).strip() == "":
        # Generate a UUID key when client doesn't supply one
        key = str(uuid.uuid4())
        generated = True

    db.put(key, value)
    return jsonify({"status": "ok", "key": key, "value": value, "key_generated": generated})


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


@app.route("/keys", methods=["GET"])
def list_keys():
    """Return a paginated list of keys present in memtable and SST files.

    Query params:
      - page: 1-based page number (default 1)
      - per_page: items per page (default 50)
      - q: optional substring filter for keys
    """
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 50))
    except ValueError:
        return jsonify({"error": "invalid pagination parameters"}), 400

    q = request.args.get("q")

    # Collect keys from memtable
    keys = set(map(str, db.memtable.keys()))

    # Collect keys from SST files (scan each SST file for keys)
    for _, path in db.sst_files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.rstrip("\n")
                    if "\t" not in stripped:
                        continue
                    k, _ = stripped.split("\t", 1)
                    keys.add(k)
        except FileNotFoundError:
            # file removed by compaction, ignore
            continue

    # Apply optional substring filter
    all_keys = sorted(keys)
    if q:
        q = str(q)
        all_keys = [k for k in all_keys if q in k]

    total = len(all_keys)
    # pagination (1-based page)
    if per_page <= 0:
        per_page = 50
    start = (max(page, 1) - 1) * per_page
    end = start + per_page
    page_keys = all_keys[start:end]

    # For each key, resolve latest value and source info.
    items = []
    for k in page_keys:
        value = None
        source = None
        sst_seq = None

        # Check memtable first
        if str(k) in map(str, db.memtable.keys()):
            value = db.memtable.get(k)
            source = "memtable"
        else:
            # Look through SSTs from newest to oldest to find latest value and seq
            for seq, path in reversed(db.sst_files):
                try:
                    v = db._read_value_from_sst(path, str(k))
                except Exception:
                    v = None
                if v is not None:
                    value = v
                    source = "sst"
                    sst_seq = seq
                    break

        # As a final fallback, call db.get (this also covers any in-memory overrides)
        if value is None:
            try:
                value = db.get(k)
                if value is not None:
                    source = source or ("memtable" if k in db.memtable else "sst")
            except Exception:
                value = None

        items.append({"key": k, "value": value, "source": source, "sst_seq": sst_seq})

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "keys": items,
    })


if __name__ == "__main__":
    host = getattr(config, "HOST", "127.0.0.1")
    port = getattr(config, "PORT", 5000)
    app.run(host=host, port=port, debug=True)
