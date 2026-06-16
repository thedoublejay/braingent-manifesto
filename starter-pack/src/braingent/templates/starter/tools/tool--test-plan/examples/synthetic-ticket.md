# SYN-001 Filter approvals by assigned reviewer

## Summary

Compliance reviewers need the approvals page to show only records assigned to
them by default, while leads can still inspect all records when they choose the
All reviewers filter.

## Acceptance Criteria

- AC-1: Reviewers see only approvals assigned to themselves by default.
- AC-2: Leads can switch to All reviewers and see approvals across reviewers.
- AC-3: The filter state is preserved when the reviewer changes pagination or sorting.
- AC-4: Empty results show a clear empty state without hiding the active filter.

## Notes

The page is a browser UI with a table, filter control, pagination, sorting, and
role-based data access.
