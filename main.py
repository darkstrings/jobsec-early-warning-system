import smtplib, requests, os, feedparser, re, pytz
from datetime import datetime
from email.mime.text import MIMEText
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from urllib.parse import quote_plus

# Leaving this here for pythonanywhere
from dotenv import load_dotenv
load_dotenv()


MAIL_SERVER = os.environ.get("JOBSEC_EWS_MAIL_SERVER")
SMTP_PORT = int(os.environ.get("JOBSEC_EWS_SMTP_PORT"))
EMAIL_ADDRESS = os.environ.get("JOBSEC_EWS_EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("JOBSEC_EWS_EMAIL_PASSWORD")  # app password
ALERT_COMPANY = os.environ.get("JOBSEC_EWS_ALERT_COMPANY")
# IF USING AN ENV VAR FOR THE REIPIENT LIST 
raw_recipients = os.environ.get("JOBSEC_EWS_ALERT_RECIPIENTS","")
recipient_list = [addr.strip() for addr in raw_recipients.split(",") if addr.strip()]

# OR USE A LIST....THAT'S WHAT THE FUNCTION EXPECTS
# recipient_list = ["someone@somewhere.com","someoneelse@somewhereelse.com"]

analyzer = SentimentIntensityAnalyzer()
# company_name_raw="guitar center"
company_name_raw = ALERT_COMPANY
company_name_formatted = quote_plus(company_name_raw)

url = f"https://news.google.com/rss/search?q={company_name_formatted}&hl=en-US&gl=US&ceid=US:en"

# REMEMBER TO PUT EMAIL ADDRESSES HERE. DB COMING SOON.

custom_strings = {
    # Positive slang
    "killer": 3.0,
    "sick": 2.0,
    "fire": 2.0,
    "dope": 2.0,

    # Critical negatives (-10)
    "bankruptcy": -10.0,
    "to close": -10.0,
    "closure": -10.0,
    "closing": -10.0,
    "store closures": -10.0,
    "layoffs": -10.0,
    "shuttering": -10.0,
    "asset liquidation": -10.0,

    # Highly negative (-0.8)
    "credit downgrade": -0.8,
    "default risk": -0.8,
    "liquidity crisis": -0.8,
    "chapter 11": -0.8,
    "chapter 7": -0.8,
    "fire sale": -0.8,
    "insolvency filing": -0.8,
    "arrested": -0.8,
    "financial distress": -0.8,
    "price increase" : -0.8,
    "price hike" : -0.8,
    "inflation" : -0.8,
    "margin pressure" : -0.8,
    "cost adjustment" : -0.8,
    "shrinkflation" : -0.8,
    "holiday pricing" : -0.8,
    "dynamic pricing" : -0.8,
    "special pricing" : -0.8,
    "MSRP change" : -0.8,

    # Moderate negatives (-0.4)
    "moody's": -0.4,
    "concern": -0.4,
    "arrest": -0.4,
    "arrested": -0.4,
    "felony": -0.4,
    "scheme": -0.4,

    # Mild negatives (-0.2)
    "theft": -0.2,
    "debt": -0.2,
    "restructuring": -0.2,
    "debt restructuring": -0.2,
    "restructuring plan": -0.2,
    "cash crunch": -0.2
}


analyzer.lexicon.update(custom_strings)

def readable_datetime():
        current_timestamp = datetime.now().timestamp()
        dt_object = datetime.fromtimestamp(current_timestamp)
        est = pytz.timezone("US/Eastern")
        est_time = dt_object.astimezone(est)
        return est_time.strftime("%Y-%m-%d %I:%M:%S %p EST")

def is_valid_email(email: str) -> bool:
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern,email) is not None

def send_email_alert(subject, body):
    valid_recipients = [addr for addr in recipient_list if is_valid_email(addr)]
    if not valid_recipients:
        print("No valid email addresses")
        return

    msg = MIMEText(body)
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(valid_recipients)
    msg["Subject"] = subject

    with smtplib.SMTP(MAIL_SERVER, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, valid_recipients, msg.as_string())

    print("MESSAGE SENT to all recipients")


def test_send():
    send_email_alert(
            subject=f"JOBSEC EWS TEST",
            body=f"Test complete"
            )
# test_send()


def get_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    res = requests.get(url, headers=headers, timeout=10)
    data_time = readable_datetime()

    print("Status:", res.status_code)
    print("Preview:", res.text[:500])  # preview first 500 chars

    feed = feedparser.parse(res.text)
    net_negative = 0
    count = 0
    print("DATA START")
    for entry in feed.entries[:15]:
        print(entry.title)
        print(entry.link)
        print(entry.published)
        print(entry.summary)
        text = f"{entry.title} {entry.summary}".lower()
        score = analyzer.polarity_scores(text)
        compound = score["compound"]
        if compound < -0.9:
            severity = "🚨 CRITICAL NEGATIVE"
            print(f"{severity} SENTIMENT DETECTED:", entry.title)
            send_email_alert(
            subject=f"JOBSEC EARLY WARNING SYSTEM ALERT: SEVERITY {severity}",
            body=f"{severity} SENTIMENT DETECTED!!!!:\nTITLE: {entry.title}\nSOURCE: PRIMARY ENTRY POINT: {entry.link}"
            )
        elif compound < -0.8:
            severity = "⚠️ Highly Negative"
            print(f"{severity} sentiment detected:", entry.title)
            send_email_alert(
            subject=f"Jobsec Early Warning System Warning: Severity {severity}",
            body=f"{severity} sentiment detected!!!!:\nTITLE: {entry.title}\nSOURCE: {entry.link}"
            )
        elif compound < -0.4:
            severity = "⚠️ Moderately Negative"
            print(f"{severity} sentiment detected:", entry.title)
            send_email_alert(
            subject=f"Jobsec Early Warning System Advisory: Severity {severity}",
            body=f"Possibly {severity} sentiment detected:\nTITLE: {entry.title}\nSOURCE: {entry.link}"
            )
        elif compound < -0.2:
            severity = "Mildly Negative"
            print(f"{severity} sentiment detected:", entry.title)
            send_email_alert(
            subject=f"Jobsec Early Warning System Advisory: Severity {severity}",
            body=f"{severity} sentiment detected:\nTITLE: {entry.title}\nSOURCE: {entry.link}"
            )
        elif compound > 0.6:
            severity = "Highly Positive"
        elif compound > 0.4:
            severity = "Moderately Positive"
        elif compound > 0.2:
            severity = "Mildly Positive"
        else:
            severity = "Neutral"
        print("----")
        print(severity)
        print("----")
        net_negative += compound
        count += 1
        avg_compound = net_negative / count


    print("DATA END", data_time)
    print("Overall average sentiment:", avg_compound)
get_data()


# if __name__ == "__main__":
