"""The application mailbox, connected directly (no Claude connector): IMAP to read replies, SMTP to send.

It is the address you apply with (standing answers → email). Gmail works with an app password:
Google Account → Security → 2-Step Verification on → App passwords → create one, then put it in .env:

    JHA_MAIL_APP_PASSWORD=abcd efgh ijkl mnop
    # optional: JHA_MAIL_ADDRESS (defaults to the standing-answers email), JHA_IMAP_HOST, JHA_SMTP_HOST

Reading is strictly read-only: the folder is opened read-only and bodies are fetched with BODY.PEEK, so nothing is
marked read, moved, labelled or deleted. Sending only happens for rows you approved (run.py outbox checks them).
"""
from __future__ import annotations
import email
import email.utils
import imaplib
import os
import re
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import quote


def settings() -> dict:
    from .setup_answers import load
    addr = os.getenv("JHA_MAIL_ADDRESS") or (load().get("email") or "")
    host = addr.split("@")[-1].lower() if "@" in addr else ""
    gmail = host in ("gmail.com", "googlemail.com") or os.getenv("JHA_IMAP_HOST", "").endswith("gmail.com")
    return {"address": addr.strip(), "password": (os.getenv("JHA_MAIL_APP_PASSWORD") or "").replace(" ", ""),
            "imap": os.getenv("JHA_IMAP_HOST") or ("imap.gmail.com" if gmail else f"imap.{host}"),
            "smtp": os.getenv("JHA_SMTP_HOST") or ("smtp.gmail.com" if gmail else f"smtp.{host}"),
            "gmail": gmail}


def configured() -> bool:
    from . import config
    if config.is_demo():          # a demo account has no mailbox: nothing is read or sent
        return False
    s = settings()
    return bool(s["address"] and s["password"])


def _dec(v) -> str:
    try:
        return str(make_header(decode_header(v or "")))
    except Exception:
        return v or ""


def _text(msg: email.message.Message) -> str:
    """Plain text of a message (HTML stripped when there is no text part)."""
    parts = msg.walk() if msg.is_multipart() else [msg]
    plain, html = "", ""
    for p in parts:
        if p.get_content_maintype() == "multipart" or p.get("Content-Disposition", "").startswith("attachment"):
            continue
        try:
            payload = p.get_payload(decode=True) or b""
            t = payload.decode(p.get_content_charset() or "utf-8", errors="replace")
        except Exception:
            continue
        if p.get_content_type() == "text/plain" and not plain:
            plain = t
        elif p.get_content_type() == "text/html" and not html:
            html = t
    if not plain and html:
        import html as _h
        plain = _h.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", html)))
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n\n", plain)).strip()


def test() -> str:
    s = settings()
    if not configured():
        return "not configured: add JHA_MAIL_APP_PASSWORD to .env (see agent/mailbox.py)"
    with imaplib.IMAP4_SSL(s["imap"]) as m:
        m.login(s["address"], s["password"])
        typ, data = m.select("INBOX", readonly=True)
        n = data[0].decode() if data and data[0] else "?"
    with smtplib.SMTP_SSL(s["smtp"], 465, context=ssl.create_default_context()) as sm:
        sm.login(s["address"], s["password"])
    return f"ok: {s['address']} (inbox has {n} messages; read and send both work)"


def fetch(days: int = 3, gmail_query: str = "") -> list[dict]:
    """Recent inbox messages as dicts for replies.ingest(). Read-only."""
    s = settings()
    out = []
    with imaplib.IMAP4_SSL(s["imap"]) as m:
        m.login(s["address"], s["password"])
        box = '"[Gmail]/All Mail"' if s["gmail"] else "INBOX"
        typ, _ = m.select(box, readonly=True)
        if typ != "OK":
            m.select("INBOX", readonly=True)
        if s["gmail"]:
            typ, data = m.search(None, "X-GM-RAW", f'"newer_than:{days}d -in:sent -in:drafts -in:spam -in:trash"')
        else:
            since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%d-%b-%Y")
            typ, data = m.search(None, "SINCE", since)
        ids = (data[0] or b"").split()[-300:]
        for i in ids:
            fields = "(BODY.PEEK[] X-GM-THRID)" if s["gmail"] else "(BODY.PEEK[])"
            typ, d = m.fetch(i, fields)
            if typ != "OK" or not d or not isinstance(d[0], tuple):
                continue
            meta, raw = d[0][0].decode(errors="replace"), d[0][1]
            msg = email.message_from_bytes(raw)
            sender = _dec(msg.get("From"))
            if s["address"].lower() in sender.lower():
                continue   # your own messages
            mid = (msg.get("Message-ID") or f"imap-{i.decode()}").strip()
            thr = re.search(r"X-GM-THRID (\d+)", meta)
            try:
                date = email.utils.parsedate_to_datetime(msg.get("Date")).astimezone(timezone.utc).isoformat()
            except Exception:
                date = None
            view = (f"https://mail.google.com/mail/u/{s['address']}/#search/rfc822msgid%3A{quote(mid.strip('<>'))}" if s["gmail"] else None)
            out.append({"msg_id": mid, "thread_id": thr.group(1) if thr else None, "date": date, "sender": sender,
                        "subject": _dec(msg.get("Subject")), "body": _text(msg)[:4000], "view_url": view})
    return out


def send(to: list[str], subject: str, body: str, html: str | None = None, attachment: str | None = None) -> str:
    from . import config
    if config.is_demo():
        raise PermissionError("demo account: emails are never sent")
    """Send one approved email from the application address. Returns the Message-ID."""
    s = settings()
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = s["address"], ", ".join(to), subject
    msg["Message-ID"] = email.utils.make_msgid(domain=s["address"].split("@")[-1])
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")
    if attachment and Path(attachment).exists():
        msg.add_attachment(Path(attachment).read_bytes(), maintype="application", subtype="pdf", filename=Path(attachment).name)
    with smtplib.SMTP_SSL(s["smtp"], 465, context=ssl.create_default_context()) as sm:
        sm.login(s["address"], s["password"])
        sm.send_message(msg)
    return msg["Message-ID"]
