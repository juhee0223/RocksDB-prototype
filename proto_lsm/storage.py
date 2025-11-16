"""SST file format abstractions for the prototype engine."""


class SSTableWriter:
    """Handles serialization of sorted key/value pairs to disk."""

    def __init__(self, file_path):
        # TODO: Prepare file handles or buffers.
        pass

    def write_entries(self, entries):
        # TODO: Persist ordered entries into SST representation.
        pass


class SSTableReader:
    """Provides sequential and point lookup access into SST files."""

    def __init__(self, file_path):
        # TODO: Load metadata blocks and indexes.
        pass

    def get(self, key):
        # TODO: Return value if key exists, otherwise None.
        pass

    def iter_range(self, start_key, end_key):
        # TODO: Yield entries within given key range.
        pass
