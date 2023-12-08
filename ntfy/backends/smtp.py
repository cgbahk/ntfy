import smtplib
from email.mime.text import MIMEText


def notify(title, message, smtp_arg: dict, email: str, password: str, retcode=None):
    msg = MIMEText(f"{title=}\n{message=}")

    if retcode == 0:
        msg["Subject"] = "[SUCCESS] ntfy"
    else:
        msg["Subject"] = "[FAIL] ntfy"

    msg["From"] = email
    msg["To"] = email

    with smtplib.SMTP(**smtp_arg) as server:
        server.login(email, password)
        server.sendmail(email, email, msg.as_string())
