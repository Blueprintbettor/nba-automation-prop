# NBA PRA Automation (Cloud Run Ready)

## What This Does

- Pulls NBA prop lines from Google Sheets (`INPUT_LINES` tab)
- Connects to BallDontLie API for player stats (last 5 games)
- Formats message
- Sends it to a Discord webhook
- Can run manually or deploy to Google Cloud Run

---

## Setup

### 1. Clone the Repo

You can use GitHub Desktop or:

```bash
git clone https://github.com/Blueprintbettor/nba-automation.git
cd nba-automation
