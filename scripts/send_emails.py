"""drafts/ klasorundeki her taslagi tek tek gosterir, gonderilsin mi diye
sorar ve onaylanirsa Gmail SMTP + App Password ile CV ekli olarak gonderir.

Hicbir mail sizin onayiniz olmadan gitmez.
"""

import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DRAFTS_DIR = ROOT / "drafts"
SENT_DIR = ROOT / "sent"
CV_PATH = ROOT / os.environ.get("CV_PATH", "cv/CV.pdf")

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
SENDER_NAME = os.environ.get("SENDER_NAME", "")


def parse_draft(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("ALICI:"):
        raise ValueError(f"{path.name}: ilk satirda 'ALICI:' bekleniyordu")
    to_email = lines[0].replace("ALICI:", "").strip()

    rest = "\n".join(lines[1:]).strip()
    if "---" not in rest:
        raise ValueError(f"{path.name}: 'KONU: ... ---' formati bulunamadi")
    subject_part, body = rest.split("---", 1)
    subject = subject_part.replace("KONU:", "").strip()
    return to_email, subject, body.strip()


def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg["From"] = f"{SENDER_NAME} <{GMAIL_ADDRESS}>" if SENDER_NAME else GMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with open(CV_PATH, "rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename=CV_PATH.name)
    msg.attach(attachment)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)


def main():
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        raise SystemExit(
            ".env icinde GMAIL_ADDRESS ve GMAIL_APP_PASSWORD tanimli olmali."
        )
    if not CV_PATH.exists():
        raise SystemExit(f"CV bulunamadi: {CV_PATH}")

    SENT_DIR.mkdir(exist_ok=True)
    draft_files = sorted(DRAFTS_DIR.glob("*.txt"))
    if not draft_files:
        print("drafts/ klasorunde taslak yok. Once: python scripts/research_and_draft.py")
        return

    for draft_path in draft_files:
        sent_marker = SENT_DIR / draft_path.name
        if sent_marker.exists():
            continue

        try:
            to_email, subject, body = parse_draft(draft_path)
        except ValueError as exc:
            print(f"[GECERSIZ TASLAK] {exc}")
            continue

        print("=" * 70)
        print(f"DOSYA : {draft_path.name}")
        print(f"ALICI : {to_email}")
        print(f"KONU  : {subject}")
        print("-" * 70)
        print(body)
        print("=" * 70)

        answer = input("Bu maili gonder? [e = evet, h = hayir/atla, q = tamamen dur]: ").strip().lower()

        if answer == "q":
            print("Durduruldu.")
            break
        if answer != "e":
            print("Atlandi.\n")
            continue

        send_email(to_email, subject, body)
        sent_marker.write_text(f"gonderildi -> {to_email}\n", encoding="utf-8")
        print(f"[GONDERILDI] {to_email}\n")


if __name__ == "__main__":
    main()
