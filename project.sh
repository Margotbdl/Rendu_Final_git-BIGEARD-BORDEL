#!/bin/bash
# project.sh
# This script uses GeckoTerminal’s API endpoint to fetch the latest pool data
# (for pools aged <72 hours). It extracts the pool name and the volume (from "from_volume_in_usd")
# and appends them to a CSV file.
#
# API Endpoint:
# https://app.geckoterminal.com/api/p1/latest_pools?include=dex%2Cdex.network%2Cpool_metric%2Ctokens&page=1&include_network_metrics=true&volume_24h%5Bgte%5D=100000&sort=-24h_volume&pool_creation_hours_ago%5Blte%5D=72
#
# Usage:
#   ./project.sh scrape   # Run the scraper (to be scheduled every 5 minutes)
#   ./project.sh report   # Generate the daily report (to be scheduled at 8 PM)
#
# Requirements:
# - jq must be installed (sudo apt install jq)

# Set directories and file paths
DATA_DIR="$HOME/project_data"
DATA_FILE="$DATA_DIR/crypto_pools_extended.csv"   # Project 1 CSV
REPORT_DIR="$HOME/project_data/reports"

# Ensure necessary directories exist
mkdir -p "$DATA_DIR"
mkdir -p "$REPORT_DIR"

scrape() {
    API_URL="https://app.geckoterminal.com/api/p1/latest_pools?include=dex%2Cdex.network%2Cpool_metric%2Ctokens&page=1&include_network_metrics=true&volume_24h%5Bgte%5D=100000&sort=-24h_volume&pool_creation_hours_ago%5Blte%5D=72"
    
    # Fetch JSON data from the API using curl with browser-like headers.
    JSON=$(curl -s -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" -H "Accept: application/json" "$API_URL")
    
    # Debug: Print a snippet of the JSON response (first 300 characters)
    echo "DEBUG: JSON snippet: ${JSON:0:300}" >&2

    # Check if JSON is empty
    if [ -z "$JSON" ]; then
        echo "Error: No data returned from API." >&2
        exit 1
    fi
    
    # Count records in the JSON response
    RECORD_COUNT=$(echo "$JSON" | jq '.data | length')
    echo "DEBUG: Number of records in JSON: $RECORD_COUNT" >&2

    if [ "$RECORD_COUNT" -eq 0 ]; then
        echo "Error: API returned no records." >&2
        exit 1
    fi

    # Parse JSON and extract the pool name and the pool volume (from_volume_in_usd)
    echo "$JSON" | jq -r '.data[] | "\(.attributes.name),\(.attributes.from_volume_in_usd)"' | while IFS=, read -r pool pool_volume; do
        if [ -n "$pool" ] && [ -n "$pool_volume" ]; then
            echo "$(date '+%Y-%m-%d %H:%M:%S'),$pool,$pool_volume" >> "$DATA_FILE"
        fi
    done
    
    echo "Scrape successful: Data appended to $DATA_FILE"
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
    
    # Assuming pool volume is in the 3rd CSV column.
    MIN=$(cut -d, -f3 "$DATA_FILE" | sort -n | head -1)
    MAX=$(cut -d, -f3 "$DATA_FILE" | sort -n | tail -1)
    
    echo "Minimum pool volume: $MIN" >> "$REPORT_FILE"
    echo "Maximum pool volume: $MAX" >> "$REPORT_FILE"
    
    echo "Daily report generated: $REPORT_FILE"
}

# Main: Determine action based on provided argument.
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

