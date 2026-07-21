# EXP-016 Path-Separator Correction — Revision 2

The first application utility stopped before writing because its exact-text
guard expected two identically indented serialization lines. Inspection showed:

- original download serialization: 12 leading spaces;
- amended retry serialization: 8 leading spaces;
- `run_exp016_audit.py` remained unchanged;
- no correction helper was present;
- no remote request or API-key access occurred.

Revision 2 uses indentation-preserving regular expressions for the two
serialization sites and two project-path resolution sites. The research and
access boundaries are unchanged.
