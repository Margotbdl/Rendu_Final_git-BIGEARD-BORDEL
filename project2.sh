#!/bin/bash
# project2.sh
# This script fetches "biggest pools" data from GeckoTerminal,
# extracts the pool name and volume, and appends lines to
# ~/project_data/crypto_pools_biggest.csv. It simulates multiple
# distinct timestamps by incrementing a "minutes offset" each time
# you run "scrape".
#
# Requirements:
# - jq must be installed (sudo apt install jq)
# - If you want real timestamps from each run, remove the offset logic below
#   and just use `date '+%Y-%m-%d %H:%M:%S'`.

DATA_DIR="$HOME/project_data"
DATA_FILE="$DATA_DIR/crypto_pools_biggest.csv"
REPORT_DIR="$DATA_DIR/reports"

mkdir -p "$DATA_DIR"
mkdir -p "$REPORT_DIR"

# We'll store an offset in minutes in this file.
OFFSET_FILE="$DATA_DIR/project2_offset"

scrape() {
    # 1) Increment the offset (or create if it doesn't exist).
    if [ -f "$OFFSET_FILE" ]; then
        OFFSET=$(cat "$OFFSET_FILE")
        OFFSET=$((OFFSET + 1))
    else
        OFFSET=0
    fi
    echo "$OFFSET" > "$OFFSET_FILE"

    # 2) Generate a custom timestamp using the offset.
    #    For example, we add OFFSET minutes to the current time.
    #    You could do '-OFFSET minutes' if you prefer going into the past.
    TIMESTAMP=$(date -d "+$OFFSET minutes" '+%Y-%m-%d %H:%M:%S')

    # 3) Fetch JSON from GeckoTerminal's biggest pools endpoint
    API_URL="https://app.geckoterminal.com/api/p1/pools?include=dex%2Cdex.network%2Ctokens&page=1&include_network_metrics=true&include_meta=1&liquidity%5Bgte%5D=100000"
    JSON=$(curl -s -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
                 -H "Accept: application/json" \
                 "$API_URL")

    echo "DEBUG: JSON snippet: ${JSON:0:300}" >&2

    if [ -z "$JSON" ]; then
        echo "Error: No data returned from API." >&2
        exit 1
    fi

    RECORD_COUNT=$(echo "$JSON" | jq '.data | length')
    echo "DEBUG: Number of records in JSON: $RECORD_COUNT" >&2

    if [ "$RECORD_COUNT" -eq 0 ]; then
        echo "Error: API returned no records." >&2
        exit 1
    fi

    # 4) Parse JSON: extract pool name and volume, append them with our new TIMESTAMP.
    echo "$JSON" | jq -r '
      .data[] |
      "\(.attributes.name),\(.attributes.from_volume_in_usd // .attributes.to_volume_in_usd)"
    ' | while IFS=, read -r pool volume; do
        if [ -n "$pool" ] && [ -n "$volume" ]; then
            # Write line with our custom TIMESTAMP
            echo "$TIMESTAMP,$pool,$volume" >> "$DATA_FILE"
        fi
    done

    echo "Scrape successful. Appended data with offset=$OFFSET minute(s)."
}

report() {
    if [ ! -f "$DATA_FILE" ]; then
        echo "Error: Data file not found!" >&2
        exit 1
    fi
    
    REPORT_FILE="$REPORT_DIR/daily_report_$(date '+%Y-%m-%d').txt"
    
    echo "Daily Report for $(date '+%Y-%m-%d')" > "$REPORT_FILE"
    echo "------------------------------------" >> "$REPORT_FILE"
    TOTAL_RECORDS=$(wc -l < "$DATA_FILE")
    echo "Total records collected: $TOTAL_RECORDS" >> "$REPORT_FILE"
    
    MIN=$(cut -d, -f3 "$DATA_FILE" | sort -n | head -1)
    MAX=$(cut -d, -f3 "$DATA_FILE" | sort -n | tail -1)
    
    echo "Minimum volume: $MIN" >> "$REPORT_FILE"
    echo "Maximum volume: $MAX" >> "$REPORT_FILE"
    
    echo "Daily report generated: $REPORT_FILE"
}

case "$1" in
    scrape)
        scrape
        ;;
    report)
        report
        ;;
    *)
        echo "Usage: $0 {scrape|report}"
        exit 1
        ;;
esac
