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

    One connection serves the whole run: Google and Microsoft throttle repeated
    logins, and one handshake per recipient would turn that into recorded
    failures. Any failure drops the connection, so the next message starts
    clean instead of inheriting a half-broken session. `close()` ends it.
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
        self._smtp: smtplib.SMTP | None = None

    async def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        try:
            await asyncio.to_thread(self._deliver, message)
        except (smtplib.SMTPException, OSError) as exc:
            await asyncio.to_thread(self._disconnect)
            raise EmailDeliveryError(f"{exc.__class__.__name__}: {exc}") from exc

    async def close(self) -> None:
        await asyncio.to_thread(self._disconnect)

    def _deliver(self, message: EmailMessage) -> None:
        if self._smtp is None:
            self._smtp = self._connect()
        self._smtp.send_message(message)

    def _connect(self) -> smtplib.SMTP:
        smtp = smtplib.SMTP(self._host, self._port, timeout=self._timeout)
        try:
            if self._starttls:
                smtp.starttls(context=ssl.create_default_context())
            if self._username:
                smtp.login(self._username, self._password or "")
        except BaseException:
            smtp.close()
            raise
        return smtp

    def _disconnect(self) -> None:
        smtp, self._smtp = self._smtp, None
        if smtp is None:
            return
        try:
            smtp.quit()
        except (smtplib.SMTPException, OSError):
            smtp.close()
