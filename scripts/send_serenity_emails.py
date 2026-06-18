#!/usr/bin/env python3
"""Send Serenity/Bean哥 tweets to full recipient list via BCC (batched).
Usage:
  python3 send_serenity_emails.py "subject" body_file.txt
  python3 send_serenity_emails.py "subject" body_file.txt --tweet-id 2064576200211861981
"""
import smtplib, email.utils, sys, time, argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
FROM = "zhangsa1122@gmail.com"
PASSWORD = "rpjc foip oplw esbb"

CACHE_DIR = Path("/opt/data/scripts/.serenity_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LAST_EMAILED_FILE = CACHE_DIR / "last_emailed_id.txt"

RECIPIENTS = [
    "17832274061@163.com", "n3100t@yeah.net", "584678850@qq.com",
    "383352741@qq.com", "1352469675@qq.com", "525425856@qq.com",
    "sophia5277@qq.com", "2859618084@qq.com", "729872914@qq.com",
    "victoriawang5168@163.com", "18800115016@163.com", "1805597122@qq.com",
    "2254497867@qq.com", "polo.li@live.com", "494328369@qq.com",
    "757804376@qq.com", "2282070079@qq.com", "1445634636@qq.com",
    "1902245237@qq.com", "14535005@qq.com", "463301239@qq.com",
    "2935611900@qq.com", "1240577850@qq.com", "187386317@qq.com",
    "577063290@qq.com", "370327163@qq.com", "54023049@qq.com",
    "327838779@qq.com", "shao270828864@qq.com", "343533478@qq.com",
    "1261520109@qq.com", "534408654@qq.com", "zhoumi2026gpt@gmail.com",
    "9731145@qq.com", "358350729@qq.com", "3557612433@qq.com",
    "625339818@qq.com", "625339819@qq.com", "363293032@qq.com", "49183054@qq.com",
    "42093416@qq.com", "2523367478@qq.com", "hechao.he@taobao.com",
    "alphacat007@126.com", "colin195@163.com", "871662306@qq.com",
    "winnt0304@outlook.com", "61686470@qq.com", "80810616@qq.com",
    "rinya_yj@hotmail.com", "842442837@qq.com", "1296881069@qq.com",
    "401729482@qq.com", "277259042@qq.com", "3985020@qq.com",
    "329435794@qq.com", "275881053@qq.com", "326850763@qq.com",
    "416433424@qq.com", "12621649@qq.com",
    "noora2025@163.com",
    "2017744752@qq.com", "shuben19930215@163.com",
    "491842554@qq.com",
    "18856962177@163.com",
    "13319294101@163.com",
    "47131567@qq.com",
]

BATCH = 20

def send_bcc(subject, body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = FROM
    msg["To"] = FROM
    msg["Bcc"] = ", ".join(RECIPIENTS)
    msg["Date"] = email.utils.formatdate()
    part = MIMEText(body, "plain", "utf-8")
    msg.attach(part)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.starttls()
        server.login(FROM, PASSWORD)
        server.sendmail(FROM, RECIPIENTS, msg.as_string())
    print(f"OK BCC sent to {len(RECIPIENTS)} recipients")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send BCC email to all recipients")
    parser.add_argument("subject", help="Email subject")
    parser.add_argument("body_file", help="Path to email body file")
    parser.add_argument("--tweet-id", help="Tweet ID for dedup (skip if already sent)")
    args = parser.parse_args()

    # Dedup: skip if this tweet was already emailed
    if args.tweet_id:
        if LAST_EMAILED_FILE.exists():
            last_id = LAST_EMAILED_FILE.read_text().strip()
            if last_id == args.tweet_id:
                print(f"SKIP: tweet {args.tweet_id} already emailed (dedup)")
                sys.exit(0)

    subject = args.subject
    with open(args.body_file, "r") as f:
        body = f.read()
    send_bcc(subject, body)

    # Write cache AFTER successful send (NOT before — prevents cache poisoning on SMTP failure)
    if args.tweet_id:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        LAST_EMAILED_FILE.write_text(args.tweet_id)