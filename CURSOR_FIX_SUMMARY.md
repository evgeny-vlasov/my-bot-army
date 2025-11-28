# RealDictCursor Indexing Fix - Complete Summary

## Problem
The codebase uses `psycopg2.extras.RealDictCursor` which returns query results as dictionaries, but code was trying to access them as tuples using numeric indexing `[0]`, `[1]`, etc., causing `KeyError: 0` errors.

## Root Cause
- Database cursors configured with `RealDictCursor` in `shared/database.py`
- RealDictCursor returns rows as `dict` objects with column names as keys
- Code incorrectly used tuple-style indexing: `row[0]`, `row[1]`, etc.
- Correct usage requires column names: `row['column_name']`

## Files Fixed

### 1. shared/rag/embedder.py (3 fixes)

#### Fix 1: Line 323 - INSERT...RETURNING pattern
```python
# BEFORE (❌ BROKEN):
document_id = cur.fetchone()[0]

# AFTER (✅ FIXED):
document_id = cur.fetchone()['id']
```
**Impact**: This was causing immediate failure when adding documents.

#### Fix 2: Lines 169-173 - Tuple unpacking
```python
# BEFORE (❌ BROKEN):
bot_id, title, content, source, metadata_json = row

# AFTER (✅ FIXED):
bot_id = row['bot_id']
title = row['title']
content = row['content']
source = row['source']
metadata_json = row['metadata']
```
**Impact**: Tuple unpacking doesn't work with dict objects - would cause TypeError.

#### Fix 3: Lines 277-284 - Dict construction with numeric indexing
```python
# BEFORE (❌ BROKEN):
return {
    'id': row[0],
    'bot_id': row[1],
    'title': row[2],
    'source': row[3],
    'created_at': row[4],
    'updated_at': row[5],
    'chunk_count': row[6] or 0
}

# AFTER (✅ FIXED):
return {
    'id': row['id'],
    'bot_id': row['bot_id'],
    'title': row['title'],
    'source': row['source'],
    'created_at': row['created_at'],
    'updated_at': row['updated_at'],
    'chunk_count': row['chunk_count'] or 0
}
```
**Impact**: Would fail when calling `get_document_info()` method.

### 2. scripts/reindex_bot.py (1 fix)

#### Fix: Line 160 - Conditional column access
```python
# BEFORE (❌ BROKEN):
content = row[0] if row else ""

# AFTER (✅ FIXED):
content = row['content'] if row else ""
```
**Impact**: Would fail when reindexing documents for a bot.

## Testing Strategy

Created `test_db_cursor_fixes.py` to validate all fix patterns:
1. ✅ Basic fetchone()/fetchall() operations
2. ✅ INSERT...RETURNING id pattern
3. ✅ Multiple column access from dict
4. ✅ Dict construction from row
5. ✅ Conditional single column access

## Validation Commands

### Test document addition (original failing command):
```bash
python scripts/add_document.py \
  --bot_id therapist \
  --title "Test Document" \
  --file bots/therapist/knowledge_base/services_overview.txt \
  --verbose
```

### Run comprehensive tests:
```bash
python test_db_cursor_fixes.py
```

## Related Code Patterns

### ✅ CORRECT patterns already in codebase:
- `scripts/add_document.py:158` - Already uses `result['id']`
- `shared/database.py:206` - Already uses `result['id']`
- Many files have defensive code: `row['col'] if isinstance(row, dict) else row[0]`

### Pattern Guide for Future Development:

```python
# ✅ CORRECT - Use column names:
row = cur.fetchone()
value = row['column_name']

# ✅ CORRECT - Multiple columns:
row = cur.fetchone()
col1 = row['col1']
col2 = row['col2']

# ✅ CORRECT - INSERT RETURNING:
cur.execute("INSERT INTO table (...) VALUES (...) RETURNING id")
new_id = cur.fetchone()['id']

# ✅ CORRECT - Building dict:
doc = {
    'id': row['id'],
    'title': row['title']
}

# ❌ WRONG - Numeric indexing:
row = cur.fetchone()
value = row[0]  # KeyError: 0

# ❌ WRONG - Tuple unpacking:
col1, col2 = cur.fetchone()  # TypeError

# ❌ WRONG - Direct numeric access:
new_id = cur.fetchone()[0]  # KeyError: 0
```

## Impact
- **Before**: `KeyError: 0` on document addition, reindexing, and document info queries
- **After**: All database operations work correctly with RealDictCursor
- **Files changed**: 2 files (embedder.py, reindex_bot.py)
- **Lines changed**: 4 critical bugs fixed

## Commit Message
```
Fix all RealDictCursor indexing issues

- Fix embedder.py:323 fetchone()[0] → fetchone()['id']
- Fix embedder.py:169 tuple unpacking to dict key access
- Fix embedder.py:274-280 numeric indexing to column names
- Fix reindex_bot.py:160 row[0] → row['content']

All database queries now correctly use column names instead of
numeric indexing, resolving KeyError: 0 failures when adding
documents or performing other database operations.
```

## Prevention
To prevent this issue in future:
1. Always use column names: `row['column']` not `row[0]`
2. Remember RealDictCursor returns dict, not tuple
3. Use type hints: `row: Dict[str, Any]` makes this clearer
4. Run test suite before committing database query changes
