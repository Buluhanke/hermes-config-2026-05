#!/usr/bin/env bash
# fact_store_write.sh — cron-friendly fact_store writer (memory tool fallback)
# Usage: ./fact_store_write.sh <topic> <text> <source> <trust> <tags_comma_sep>
# Example: ./fact_store_write.sh "hermes_tip" "useful technique" "docs.url" 0.80 "tip,hermes"
set -euo pipefail

TOPIC="${1:?Usage: $0 <topic> <text> <source> <trust> <tags>}"
TEXT="${2:?missing text}"
SOURCE="${3:-manual}"
TRUST="${4:-0.5}"
TAGS="${5:-general}"

DB="${FACT_STORE_DB:-$HOME/.hermes/memory/fact_store.db}"
NOW=$(date -u +%s)

# Schema reminder:
#   facts(id INTEGER PK, topic, text, source, trust REAL DEFAULT 0.5,
#         created_at REAL DEFAULT 0, updated_at REAL DEFAULT 0, tags TEXT JSON)

# SQL-escape single quotes
TEXT_ESC=$(printf '%s' "$TEXT" | sed "s/'/''/g")
SOURCE_ESC=$(printf '%s' "$SOURCE" | sed "s/'/''/g")
TAGS_JSON="[\"$(echo "$TAGS" | sed 's/,/","/g')\"]"

sqlite3 "$DB" <<EOF
INSERT INTO facts (topic, text, source, trust, created_at, updated_at, tags) VALUES
('$TOPIC', '$TEXT_ESC', '$SOURCE_ESC', $TRUST, $NOW, $NOW, '$TAGS_JSON');
SELECT 'WROTE fact_id=' || last_insert_rowid() || ' topic=' || '$TOPIC' AS result;
EOF