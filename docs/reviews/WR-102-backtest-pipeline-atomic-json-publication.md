# WR-102 — Backtest Pipeline Atomic JSON File Publication Boundary

## Summary

The backtest pipeline JSON writer now publishes complete exports through
a same-directory temporary file and `os.replace()`.

## Publication flow

The writer:

1. serializes the complete result before filesystem mutation;
2. creates the destination directory;
3. creates a uniquely named temporary file in that directory;
4. writes the complete UTF-8 JSON payload;
5. flushes and closes the temporary file;
6. atomically replaces the requested destination path.

The requested destination `Path` remains the return value.

## Failure behavior

Write, flush, close, and replace exceptions propagate unchanged.
Temporary files are removed after failed publication. Because the
destination is not opened directly, a failed publication leaves an
existing destination byte-for-byte unchanged.

## Compatibility

Constructor and method signatures, JSON formatting, successful
overwrite behavior, timestamped filenames, and package exports remain
unchanged.

This boundary provides atomic visibility through same-directory
replacement. It does not promise crash durability and does not add
`fsync`, locking, overwrite policy, concurrency coordination, checksum,
compression, metadata, retention, symlink protection, a CLI, or a
database.
