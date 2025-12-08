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

keywords = ["bankruptcy", "financial", "debt", "to close", "closure", "closing", "restructuring", "moody's," "shuttering"]

custom_strings = {
    # Positive slang
    "killer": 3.0,
    "sick": 2.0,
    "fire": 2.0,
    "dope": 2.0,

    # Critial negatives (-6)
    "bankruptcy": -6.0,
    "to close": -6.0,
    "closure": -6.0,
    "closing": -6.0,
    "store closures": -6.0,
    "layoffs announced": -6.0,
    "shuttering": -6.0,
    "asset liquidation": -6.0,

    # Highly negative (-5)
    "credit downgrade": -5.0,
    "default risk": -5.0,
    "liquidity crisis": -5.0,
    "chapter 11": -5.0,
    "chapter 7": -5.0,
    "fire sale": -5.0,
    "insolvency filing": -5.0,
    "employee arrested": -5.0,

    # Moderate negatives (-4)
    "moody's": -4.0,
    "growing concern": -4.0,
    "financial distress": -4.0,
    "arrest" : -4.0,
    "arrested" : -4.0,
    "felony" : -4.0,
    

    # Mild negatives (-2)
    "theft" : -2.0,
    "debt": -2.0,
    "restructuring": -2.0,
    "debt restructuring": -2.0,
    "restructuring plan": -2.0,
    "cash crunch": -2.0
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
        if compound < -0.6:
            severity = "🚨 CRITICAL NEGATIVE"
            print(f"{severity} SENTIMENT DETECTED:", entry.title)
            send_email_alert(
            subject=f"JOBSEC EARLY WARNING SYSTEM ALERT: SEVERITY {severity}",
            body=f"{severity} SENTIMENT DETECTED!!!!:\nTITLE: {entry.title}\nSOURCE: PRIMARY ENTRY POINT: {entry.link}"
            )
        elif compound < -0.5:
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
