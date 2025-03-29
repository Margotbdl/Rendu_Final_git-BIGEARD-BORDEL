#!/bin/bash
# fetch_prices.sh
#
# This script merges tokens from two CSV files (from project.sh and project2.sh),
# creates a unique list of tokens, and then fetches each token's USD price using Binance's public API.
# The token names and their prices are saved into a separate CSV file.
#
# Requirements:
# - curl (typically pre-installed)
# - jq (install with: sudo apt install jq)
#
# File paths:
# - Project 1 CSV: ~/project_data/crypto_pools_extended.csv
# - Project 2 CSV: ~/project_data/crypto_pools_biggest.csv
# - Tokens output: ~/project_data/crypto_tokens.csv
# - Prices output: ~/project_data/crypto_prices.csv

# Define file paths and directories
DATA_DIR="$HOME/project_data"
FILE1="$DATA_DIR/crypto_pools_extended.csv"   # From project.sh
FILE2="$DATA_DIR/crypto_pools_biggest.csv"      # From project2.sh
TOKENS_FILE="$DATA_DIR/crypto_tokens.csv"
PRICES_FILE="$DATA_DIR/crypto_prices.csv"

# Ensure DATA_DIR exists
mkdir -p "$DATA_DIR"

# Clear or create the tokens file
> "$TOKENS_FILE"

# Extract tokens from both CSV files (assume pool names are in column 2)
for file in "$FILE1" "$FILE2"; do
    if [ -f "$file" ]; then
        awk -F, '{print $2}' "$file" | tr '/' '\n' | sed 's/^[ \t]*//;s/[ \t]*$//' >> "$TOKENS_FILE"
    fi
done

# Get unique token names and save them back to TOKENS_FILE
sort -u "$TOKENS_FILE" -o "$TOKENS_FILE"

# Prepare the prices CSV file with header
echo "Token,Price(USD)" > "$PRICES_FILE"

# Declare an associative array for Binance symbol mapping (requires bash 4+)
declare -A token_mapping
# Add mappings for tokens that need special conversion.
token_mapping["weth"]="ETHUSDT"       # Treat WETH as ETH
token_mapping["eth"]="ETHUSDT"
token_mapping["btc"]="BTCUSDT"
token_mapping["sol"]="SOLUSDT"
token_mapping["usdc"]="USDCUSDT"
token_mapping["usdt"]="USDT"          # For USDT, price is 1 (special handling below)
# Add more mappings as needed.

# Loop over each token and fetch its price from Binance.
while IFS= read -r token; do
    # Skip empty lines
    [ -z "$token" ] && continue

    # Convert token name to lowercase for mapping lookup.
    token_lc=$(echo "$token" | tr '[:upper:]' '[:lower:]')
    [ -z "$token_lc" ] && continue

    # Use parameter expansion to check if key exists
    if [ "${token_mapping[$token_lc]+exists}" ]; then
        token_id="${token_mapping[$token_lc]}"
    else
        # Default: convert token to uppercase and append "USDT"
        token_id=$(echo "$token" | tr '[:lower:]' '[:upper:]' | sed 's/ //g')USDT
    fi

    # For USDT, we know the price is 1.
    if [ "$token_id" = "USDT" ]; then
        price=1
    else
        # Fetch price from Binance API.
        API_URL="https://api.binance.com/api/v3/ticker/price?symbol=${token_id}"
        JSON=$(curl -s "$API_URL")
        # Extract the price using jq; if not available, return "N/A".
        price=$(echo "$JSON" | jq -r '.price // "N/A"')
    fi

    echo "$token,$price" >> "$PRICES_FILE"
    # Optional: delay to avoid rate limits.
    sleep 1
done < "$TOKENS_FILE"

echo "Token prices have been written to $PRICES_FILE"
