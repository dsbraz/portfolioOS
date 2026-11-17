import asyncio
import smtplib
import ssl
from email.message import EmailMessage

from app.domain.email_sender import EmailDeliveryError, EmailDeliveryUncertain

# The relay dropped the session before the transfer began (idle timeout, cap on
# messages per session): nothing was handed over, so a fresh session is safe.
_SESSION_LOST = (smtplib.SMTPServerDisconnected, ConnectionError)


class SmtpEmailSender:
    """Plain SMTP with STARTTLS, from the standard library.

    The provider is configuration, not code: the corporate relay of Google
    Workspace or Microsoft 365, or any transactional service that speaks SMTP.
    `smtplib` is blocking, so each send runs in a worker thread.

    One connection serves the whole run: Google and Microsoft throttle repeated
    logins, and one handshake per recipient would turn that into recorded
    failures. Any failure drops the connection, so the next message starts
    clean instead of inheriting a half-broken session. `close()` ends it.

    The transaction runs in two phases, because they fail differently:
    - addressing (`MAIL`/`RCPT`): a refusal means nothing left, and a session
      the relay closed is reopened once and retried;
    - transfer (`DATA`): an explicit rejection still means nothing left, but a
      transfer that breaks before the relay answers may have been queued, so it
      is reported as uncertain and never retried here.
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
            await asyncio.to_thread(self._deliver, to, message.as_bytes())
        except BaseException:
            await asyncio.to_thread(self._disconnect)
            raise

    async def close(self) -> None:
        await asyncio.to_thread(self._disconnect)

    def _deliver(self, to: str, data: bytes) -> None:
        smtp = self._address(to)
        try:
            smtp.data(data)
        except smtplib.SMTPDataError as exc:
            # The relay answered and said no: the message was not accepted.
            raise EmailDeliveryError(_describe(exc)) from exc
        except Exception as exc:
            raise EmailDeliveryUncertain(_describe(exc)) from exc

    def _address(self, to: str) -> smtplib.SMTP:
        """Open the transaction for `to`, reopening a session the relay closed."""
        for attempt in range(2):
            try:
                smtp = self._session()
                _expect(smtp.mail(self._sender), (250,), smtplib.SMTPSenderRefused, self._sender)
                _expect(smtp.rcpt(to), (250, 251), smtplib.SMTPRecipientsRefused, to)
                return smtp
            except _SESSION_LOST as exc:
                self._disconnect()
                if attempt:
                    raise EmailDeliveryError(_describe(exc)) from exc
            except (smtplib.SMTPException, OSError) as exc:
                raise EmailDeliveryError(_describe(exc)) from exc
        raise AssertionError("unreachable")

    def _session(self) -> smtplib.SMTP:
        if self._smtp is None:
            self._smtp = self._connect()
        return self._smtp

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


def _expect(reply: tuple[int, bytes], accepted: tuple[int, ...], refusal, address: str) -> None:
    code, text = reply
    if code in accepted:
        return
    if code == 421:
        # "Service closing": the relay is ending the session, not refusing.
        raise smtplib.SMTPServerDisconnected(f"{code} {text!r}")
    if refusal is smtplib.SMTPRecipientsRefused:
        raise smtplib.SMTPRecipientsRefused({address: (code, text)})
    raise refusal(code, text, address)


def _describe(exc: BaseException) -> str:
    return f"{exc.__class__.__name__}: {exc}"
