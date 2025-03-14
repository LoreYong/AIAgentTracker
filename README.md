# AIAgentTracker

A tool for tracking GitHub AI Agent projects and their popularity.

## Overview

AIAgentTracker automatically searches for and tracks AI Agent-related projects on GitHub. It collects key metrics like star count, fork count, and update frequency, storing this data in a historical timeline.

## Features

- Daily automatic scraping of GitHub for AI Agent repositories
- Detailed data collection including stars, forks, and descriptions
- Historical data tracking with daily snapshots
- Sorted results by popularity (star count)

## Usage

### Manual Run

```bash
# Run immediate data collection
python -m scripts.daily_update --now
```
### Schedule Daily Updates

```bash
# Schedule updates to run daily at 2:00 AM
python -m scripts.daily_update
```

## Configuration

Edit `config/config.yaml` to customize:
- Search keywords
- Minimum star threshold
- Data storage format
