# Get current player count from stats.db

cd "$(dirname "$0")"
RESULTS=$(sqlite3 ./stats.db <<EOF
  SELECT
    player_count,
    mspt_60s_avg
  FROM stats
  ORDER BY timestamp DESC
  LIMIT 1;
EOF
)

PLAYER_COUNT=$(echo "$RESULTS" | cut -d '|' -f 1)
MSPT=$(echo "$RESULTS" | cut -d '|' -f 2)

echo -ne "\033[0;32m[${PLAYER_COUNT} players]\033[0m \033[0;33m[${MSPT} ms/tick]\033[0m"