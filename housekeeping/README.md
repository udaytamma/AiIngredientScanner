# Housekeeping Scripts

Maintenance and administrative scripts for the AI Ingredient Safety Analyzer.
Run these periodically or as needed to maintain system health.

## Scripts

### audit_qdrant.py

Audits and cleans the Qdrant vector database to remove duplicate ingredients.

**When to run:**
- After noticing duplicate ingredients in API responses
- Periodically (weekly/monthly) as preventive maintenance
- After bulk data imports

**Usage:**

```bash
# Activate virtual environment first
source venv/bin/activate

# List all ingredients in database
python housekeeping/audit_qdrant.py --list

# Find potential duplicates (exact name matches + semantic similarity)
python housekeeping/audit_qdrant.py --find-duplicates

# Preview cleanup (dry run - no changes made)
python housekeeping/audit_qdrant.py --clean --dry-run

# Actually clean duplicates (interactive confirmation)
python housekeeping/audit_qdrant.py --clean

# Delete specific ingredients by name
python housekeeping/audit_qdrant.py --delete "Ingredient Name 1" "Ingredient Name 2"

# Adjust similarity threshold (default: 0.95)
python housekeeping/audit_qdrant.py --find-duplicates --threshold 0.90
```

**Options:**
| Flag | Description |
|------|-------------|
| `--list`, `-l` | List all ingredients in the database |
| `--find-duplicates`, `-f` | Find duplicates by semantic similarity |
| `--delete NAME`, `-d` | Delete ingredients by name |
| `--clean`, `-c` | Interactive cleanup of duplicates |
| `--dry-run` | Preview changes without executing |
| `--threshold`, `-t` | Similarity threshold (default: 0.95) |

**Requirements:**
- Qdrant credentials configured in `.env` (QDRANT_URL, QDRANT_API_KEY)
- Google API key for embeddings (GOOGLE_API_KEY)

---

## Adding New Scripts

When adding new housekeeping scripts:

1. Place the script in this `housekeeping/` directory
2. Add documentation to this README
3. Include `--dry-run` option for destructive operations
4. Add logging for audit trail
5. Test thoroughly before running on production data
