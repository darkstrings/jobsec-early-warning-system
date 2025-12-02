# JobSec Early Warning System (EWS)

A Python portfolio project that monitors the financial health of **any company you configure**.  
It scrapes Google News RSS feeds, applies sentiment analysis, and sends early‑warning alerts via email when risk signals are detected.

---

## ✨ Features
- 🔍 Scrapes Google News RSS feeds for company‑specific mentions
- 📊 Uses VADER sentiment analysis with a custom lexicon for financial distress keywords
- 🗄️ Tracks sentiment severity levels (Critical, Highly Negative, Moderately Negative, Mildly Negative, Neutral, Positive)
- 📧 Sends alerts via SMTP to a configurable recipient list
- 🕒 Formats timestamps dynamically in Eastern Standard Time
- ⚙️ All sensitive values (SMTP server, sender account, recipients) managed via environment variables

---

## 🚀 Installation
Clone the repository and install dependencies:

```bash
git clone https://github.com/yourusername/jobsec-ews.git
cd jobsec-ews
pip install -r requirements.txt

**Be sure to set up recipient email addresses either in an environment variable or a list for alerts.**

---