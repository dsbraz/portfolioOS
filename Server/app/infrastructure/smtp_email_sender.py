import asyncio
import smtplib
import ssl
from email.message import EmailMessage

from app.domain.email_sender import EmailDeliveryError


class SmtpEmailSender:
    """Plain SMTP with STARTTLS, from the standard library.

    The provider is configuration, not code: the corporate relay of Google
    Workspace or Microsoft 365, or any transactional service that speaks SMTP.
    `smtplib` is blocking, so each send runs in a worker thread.
    """

    def __init__(
        self,
        host: str,
        port: int,
        sender: str,
        username: str | None = None,
        password: str | None = None,
        starttls: bool = True,
        timeout: float = 30.0,
    ) -> None:
        self._host = host
        self._port = port
        self._sender = sender
        self._username = username
        self._password = password
        self._starttls = starttls
        self._timeout = timeout

    async def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        try:
            await asyncio.to_thread(self._deliver, message)
        except (smtplib.SMTPException, OSError) as exc:
            raise EmailDeliveryError(f"{exc.__class__.__name__}: {exc}") from exc

    def _deliver(self, message: EmailMessage) -> None:
        with smtplib.SMTP(self._host, self._port, timeout=self._timeout) as smtp:
            if self._starttls:
                smtp.starttls(context=ssl.create_default_context())
            if self._username:
                smtp.login(self._username, self._password or "")
            smtp.send_message(message)
