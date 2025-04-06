# Crypto Pools Dashboard

This repository contains the code for a Crypto Pools Dashboard project developed for a hackathon focused on innovative solutions in the blockchain and financial sectors. The dashboard provides real-time visualizations of various crypto pool data and crypto prices.

## Overview

The project leverages an AXS instance to continuously retrieve, store, and update data from multiple sources. This allows us to display real-time analytics and generate daily reports. The dashboard is built using [Dash](https://dash.plotly.com/), a Python framework for creating interactive web applications.

## Data Storage and Management

- **AXS Instance:**  
  We use an AXS instance to handle our data storage needs. The instance is responsible for:
  - Retrieving and storing data about crypto pools (e.g., pools with less than 72 hours and the largest pools).
  - Fetching and updating current crypto prices.
  - Generating daily reports summarizing the collected data.

- **CSV Files:**  
  Raw data is stored in CSV format and organized in the `data/` directory. These files are periodically updated via automated scripts.

- **Daily Reports:**  
  Generated reports are saved in the `reports/` directory, allowing for historical analysis and review.

## Project Structure

- **app.py**: Main application code that builds and runs the Dash dashboard.
- **.gitignore**: Specifies files and directories (e.g., the virtual environment, log files, and sensitive files such as SSH keys) that are not tracked by Git.
- **data/**: Directory containing CSV files with raw data.
- **reports/**: Directory containing daily generated reports.
- **Additional Scripts**: Scripts like `fetch_prices.sh`, `project.sh`, etc., automate data collection and processing.

## Setup and Running the Application

1. **Clone the Repository:**

   ```bash
   git clone git@github.com:Margotbdl/Rendu_Final_git-BIGEARD-BORDEL.git
   cd Rendu_Final_git-BIGEARD-BORDEL
