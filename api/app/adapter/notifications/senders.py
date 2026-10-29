"""Каналы уведомлений владельца о новых заявках."""

import html
import logging
import smtplib
from email.message import EmailMessage

import httpx

from app.core.config import Settings
from app.core.logging import log_event
from app.domain.notifications import LeadMessage, TemporaryError
from app.port.notifications import Sender

log = logging.getLogger("app.notify")


class TelegramSender:
    channel = "telegram"

    def __init__(self, token: str, chat_id: str, client: httpx.Client | None = None):
        self.token = token
        self.chat_id = chat_id
        self.client = client or httpx.Client(timeout=10)

    def send(self, lead: LeadMessage) -> None:
        e = html.escape
        text = (
            f"<b>Новая заявка №{e(lead.public_number)}</b>\n"
            f"Имя: {e(lead.name)}\n"
            f"Контакт: {e(lead.contact)}\n"
            f"Услуга: {e(lead.service or 'не указана')}\n"
        )
        if lead.message:
            text += f"\n{e(lead.message[:3000])}\n"
        text += f'\n<a href="{e(lead.admin_url)}">Открыть в админке</a>'
        try:
            resp = self.client.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
        except httpx.HTTPError as exc:
            raise TemporaryError(f"telegram network error: {type(exc).__name__}") from exc
        if resp.status_code >= 500 or resp.status_code == 429:
            raise TemporaryError(f"telegram http {resp.status_code}")
        if resp.status_code >= 400:
            # Неверный токен или chat_id: повторы бесполезны, но задача уйдёт в failed по лимиту.
            raise TemporaryError(f"telegram http {resp.status_code}: {resp.text[:200]}")


class EmailSender:
    channel = "email"

    def __init__(self, settings: Settings):
        self.s = settings

    def send(self, lead: LeadMessage) -> None:
        msg = EmailMessage()
        msg["Subject"] = f"Новая заявка №{lead.public_number}"
        msg["From"] = self.s.notify_email_from
        msg["To"] = self.s.notify_email_to
        msg.set_content(
            f"Имя: {lead.name}\nКонтакт: {lead.contact}\n"
            f"Услуга: {lead.service or 'не указана'}\n\n{lead.message}\n\n{lead.admin_url}\n"
        )
        try:
            with smtplib.SMTP(self.s.smtp_host, self.s.smtp_port, timeout=15) as smtp:
                if self.s.smtp_starttls:
                    smtp.starttls()
                if self.s.smtp_user:
                    password = (
                        self.s.smtp_password.get_secret_value() if self.s.smtp_password else ""
                    )
                    smtp.login(self.s.smtp_user, password)
                smtp.send_message(msg)
        except (OSError, smtplib.SMTPException) as exc:
            raise TemporaryError(f"smtp error: {type(exc).__name__}") from exc


class LogSender:
    """Используется, когда внешние каналы не настроены (local, staging без ключей)."""

    channel = "log"

    def send(self, lead: LeadMessage) -> None:
        log_event(log, "lead notification (log channel)", public_number=lead.public_number)


def configured_senders(settings: Settings) -> list[Sender]:
    senders: list[Sender] = []
    if settings.telegram_bot_token and settings.telegram_chat_id:
        senders.append(
            TelegramSender(
                settings.telegram_bot_token.get_secret_value(), settings.telegram_chat_id
            )
        )
    if settings.smtp_host and settings.notify_email_from and settings.notify_email_to:
        senders.append(EmailSender(settings))
    return senders or [LogSender()]
