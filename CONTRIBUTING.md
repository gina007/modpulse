# Contributing to ModPulse

Thanks for your interest in contributing! ModPulse is built for the Reddit moderation community and we welcome contributions of all kinds.

## Ways to Contribute

- 🐛 Report bugs via GitHub Issues
- 💡 Suggest new analytics features
- 🔧 Submit pull requests
- 📖 Improve documentation

## Development Setup

```bash
git clone https://github.com/modpulse-app/modpulse.git
cd modpulse
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your Reddit API credentials to .env
pytest tests/
```

## Guidelines

- All new features must include tests
- Keep Reddit API calls read-only — no posting or voting
- Respect Reddit's rate limits (60 req/min)
- Never store or expose user personal data

## Code of Conduct

Be respectful. This tool exists to help moderators build healthier communities.
