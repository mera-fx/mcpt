EXP-016 PATH-SEPARATOR CORRECTION — REVISION 2
===============================================

The first correction script assumed both local_path serialization lines used
identical indentation. The committed runner uses 12 spaces in the original
download record and 8 spaces in the amended retry record.

Revision 2 matches the code structurally rather than requiring identical
indentation. It still changes only path representation handling.

No API key is read. No remote request occurs. No raw data, lock file, hash,
sample window, measurement, threshold, strategy, or trading boundary changes.
