import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import markdown


SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def send(report_markdown: str, subject: str = None) -> None:
    sender = os.environ["EMAIL_SENDER"]
    password = os.environ["EMAIL_PASSWORD"]
    receiver = os.environ["EMAIL_RECEIVER"]

    if subject is None:
        today = datetime.now().strftime("%Y-%m-%d (%a)")
        subject = f"[보안 주간 리포트] {today}"

    html_body = markdown.markdown(
        report_markdown,
        extensions=["tables", "fenced_code", "nl2br"],
    )

    # 가독성을 위한 기본 CSS 래핑
    html_content = f"""
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Malgun Gothic', Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #1a1a2e; border-bottom: 2px solid #16213e; padding-bottom: 8px; }}
        h2 {{ color: #16213e; border-bottom: 1px solid #ccc; padding-bottom: 4px; margin-top: 30px; }}
        h3 {{ color: #0f3460; }}
        a {{ color: #0066cc; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; font-size: 0.9em; }}
        pre {{ background: #f4f4f4; padding: 12px; border-radius: 5px; overflow-x: auto; }}
      </style>
    </head>
    <body>
      {html_body}
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver
    msg.attach(MIMEText(report_markdown, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(sender, password)
        smtp.sendmail(sender, receiver, msg.as_string())

    print(f"이메일 발송 완료: {receiver}")


def send_error(error_message: str) -> None:
    """리포트 생성 실패 시 에러 내용을 이메일로 발송"""
    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"[보안 주간 리포트] ⚠️ 생성 실패 — {today}"
    error_report = f"# ⚠️ 보안 주간 리포트 생성 실패\n\n**날짜:** {today}\n\n**에러 내용:**\n\n```\n{error_message}\n```\n"
    send(error_report, subject=subject)
