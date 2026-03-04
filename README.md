# ModPulse 🔍

**Community Health Analytics for Reddit Moderators**
## Status: Beta

ModPulse is a free, open-source dashboard that gives subreddit moderators real-time visibility into their community's health — detecting spam waves, visualizing engagement trends, and surfacing actionable insights to reduce moderation workload.

![ModPulse Dashboard](docs/dashboard-preview.png)

---

## Why ModPulse?

Moderating a large subreddit is overwhelming. Most mods rely on manual review and gut instinct to detect coordinated spam, engagement drops, or topic drift. ModPulse changes that by giving moderators a data-driven view of their community — automatically.

### Key Features

- 📊 **Engagement Trend Dashboard** — Visualize post volume, comment depth, and upvote patterns over time
- 🚨 **Anomaly Alerts** — Detect sudden spikes in low-effort or repetitive posts
- 🔑 **Keyword Frequency Tracker** — See which topics dominate your community week over week
- 👥 **Account Age Heatmap** — Identify unusual concentrations of new accounts posting simultaneously
- 📬 **Weekly Mod Digest** — Auto-generated summary of community activity delivered via email
- 🔗 **Multi-Subreddit Comparison** — Compare health metrics across communities side by side

---

## How It Works

ModPulse is a **read-only** tool. It never posts, comments, votes, or takes any action on Reddit. It only reads public data that is already visible to anyone.

```
Subreddit Public Feed
        ↓
  Reddit OAuth API (read-only)
        ↓
  ModPulse Aggregation Engine
        ↓
  Moderator Dashboard (web)
        ↓
  Optional: Email/Webhook Alerts
```

---

## Tech Stack

- **Backend**: Python 3.11, FastAPI
- **Reddit Integration**: PRAW (Python Reddit API Wrapper)
- **Data Storage**: SQLite (local) / PostgreSQL (production)
- **Dashboard**: React + Recharts
- **Scheduling**: APScheduler
- **Alerts**: SMTP email + webhook support

---

## Getting Started

### Prerequisites

```bash
python >= 3.11
node >= 18
```

### Installation

```bash
# Clone the repo
git clone https://github.com/modpulse-app/modpulse.git
cd modpulse

# Install Python dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your Reddit API credentials
```

### Reddit API Setup

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Create a new **web app**
3. Set redirect URI to `http://localhost:8080/auth/callback`
4. Copy `client_id` and `client_secret` into your `.env` file

### Running ModPulse

```bash
# Start the backend
python src/main.py

# In a separate terminal, start the dashboard
cd dashboard && npm install && npm start
```

Visit `http://localhost:3000` to access your dashboard.

---

## Configuration

Edit `.env` to configure ModPulse:

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=ModPulse/1.0 by u/your_username

# Subreddits to monitor (comma-separated)
TARGET_SUBREDDITS=python,datascience,MachineLearning

# Alert thresholds
SPIKE_THRESHOLD=2.5        # Alert when post volume exceeds 2.5x 7-day average
NEW_ACCOUNT_RATIO=0.4      # Alert when >40% of posts are from <30 day accounts

# Email digest (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
ALERT_EMAIL=your@email.com
```

---

## Privacy & Ethics

ModPulse is committed to responsible data use:

- ✅ **Read-only** — No posting, voting, or account actions ever
- ✅ **Public data only** — Only accesses posts/comments visible to all users
- ✅ **No data resale** — Community data is never sold or shared with third parties
- ✅ **Rate limit compliant** — Strictly respects Reddit's 60 req/min OAuth limit
- ✅ **Opt-in only** — Moderators must explicitly add their subreddit
- ✅ **GDPR-aware** — No personal data stored beyond Reddit usernames in public posts

---

## Roadmap

- [ ] v0.1 — Core metrics dashboard (post volume, engagement depth)
- [ ] v0.2 — Anomaly detection alerts
- [ ] v0.3 — Weekly digest emails
- [ ] v0.4 — Multi-subreddit comparison view
- [ ] v0.5 — Moderator Chrome extension
- [ ] v1.0 — Public hosted version at modpulse.app

---

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

```bash
# Run tests
pytest tests/

# Lint
flake8 src/
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Contact

Built for the Reddit moderator community. Questions or partnership inquiries: hello@modpulse.app
Add project status badge
