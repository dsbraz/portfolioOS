import email
import smtplib
import socket
from unittest.mock import MagicMock, patch

import pytest

from app.domain.email_sender import EmailDeliveryError, EmailDeliveryUncertain
from app.infrastructure.smtp_email_sender import SmtpEmailSender

SMTP = "app.infrastructure.smtp_email_sender.smtplib.SMTP"


def _sender(**overrides):
    options = dict(
        host="smtp.example.com",
        port=587,
        sender="portfolio@example.com",
        username="portfolio@example.com",
        password="app-password",
    )
    options.update(overrides)
    return SmtpEmailSender(**options)


def _relay():
    """A session that accepts everything, as a healthy relay would."""
    smtp = MagicMock()
    smtp.mail.return_value = (250, b"ok")
    smtp.rcpt.return_value = (250, b"ok")
    smtp.data.return_value = (250, b"queued")
    return smtp


@pytest.mark.asyncio
async def test_sends_over_starttls_with_login():
    smtp = _relay()
    with patch(SMTP, return_value=smtp) as smtp_class:
        await _sender().send("ana@payface.com", "Assunto", "Corpo")

    smtp_class.assert_called_once_with("smtp.example.com", 587, timeout=30.0)
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with("portfolio@example.com", "app-password")
    smtp.mail.assert_called_once_with("portfolio@example.com")
    smtp.rcpt.assert_called_once_with("ana@payface.com")
    message = email.message_from_bytes(smtp.data.call_args.args[0])
    assert message["From"] == "portfolio@example.com"
    assert message["To"] == "ana@payface.com"
    assert message["Subject"] == "Assunto"
    assert message.get_payload(decode=True).decode().strip() == "Corpo"


@pytest.mark.asyncio
async def test_relay_without_authentication_skips_login():
    smtp = _relay()
    with patch(SMTP, return_value=smtp):
        await _sender(username=None, password=None).send("a@x.com", "s", "b")

    smtp.login.assert_not_called()


@pytest.mark.asyncio
async def test_one_connection_and_one_login_serve_the_whole_run():
    smtp = _relay()
    with patch(SMTP, return_value=smtp) as smtp_class:
        sender = _sender()
        await sender.send("a@x.com", "s", "b")
        await sender.send("b@x.com", "s", "b")
        await sender.close()

    smtp_class.assert_called_once()
    smtp.login.assert_called_once()
    assert smtp.data.call_count == 2
    smtp.quit.assert_called_once()


@pytest.mark.parametrize(
    "configure",
    [
        lambda smtp: setattr(smtp.rcpt, "return_value", (550, b"no such user")),
        lambda smtp: setattr(smtp.mail, "return_value", (553, b"sender refused")),
        lambda smtp: setattr(
            smtp.data, "side_effect", smtplib.SMTPDataError(554, b"rejected")
        ),
    ],
    ids=["recipient-refused", "sender-refused", "message-rejected"],
)
@pytest.mark.asyncio
async def test_an_explicit_refusal_is_a_delivery_error(configure):
    # The relay answered "no": nothing was accepted, so a retry cannot duplicate.
    smtp = _relay()
    configure(smtp)
    with patch(SMTP, return_value=smtp):
        with pytest.raises(EmailDeliveryError):
            await _sender().send("a@x.com", "s", "b")


@pytest.mark.parametrize(
    "failure",
    [smtplib.SMTPServerDisconnected("gone"), socket.timeout("timed out"), ValueError("?")],
    ids=["disconnected", "timeout", "unexpected"],
)
@pytest.mark.asyncio
async def test_a_transfer_broken_before_the_reply_is_uncertain(failure):
    # The relay may have queued it a moment before: not a failure to retry.
    first, second = _relay(), _relay()
    first.data.side_effect = failure
    with patch(SMTP, side_effect=[first, second]) as smtp_class:
        sender = _sender()

        with pytest.raises(EmailDeliveryUncertain):
            await sender.send("a@x.com", "s", "b")
        # The half-open session is dropped, never reused.
        await sender.send("b@x.com", "s", "b")

    first.data.assert_called_once()
    assert smtp_class.call_count == 2
    second.data.assert_called_once()


@pytest.mark.parametrize(
    "lost",
    [
        lambda smtp: setattr(
            smtp.mail, "side_effect", smtplib.SMTPServerDisconnected("idle")
        ),
        lambda smtp: setattr(smtp.mail, "return_value", (421, b"closing")),
        lambda smtp: setattr(smtp.rcpt, "side_effect", ConnectionResetError()),
    ],
    ids=["disconnected", "421-closing", "reset"],
)
@pytest.mark.asyncio
async def test_a_session_the_relay_closed_is_reopened_once_before_the_transfer(lost):
    # Idle timeout or a per-session cap: nothing was handed over yet.
    stale, fresh = _relay(), _relay()
    lost(stale)
    with patch(SMTP, side_effect=[stale, fresh]) as smtp_class:
        await _sender().send("a@x.com", "s", "b")

    assert smtp_class.call_count == 2
    stale.data.assert_not_called()
    fresh.data.assert_called_once()


@pytest.mark.asyncio
async def test_a_session_lost_twice_is_a_delivery_error():
    stale, again = _relay(), _relay()
    for smtp in (stale, again):
        smtp.mail.side_effect = smtplib.SMTPServerDisconnected("gone")
    with patch(SMTP, side_effect=[stale, again]):
        with pytest.raises(EmailDeliveryError):
            await _sender().send("a@x.com", "s", "b")

    again.data.assert_not_called()


@pytest.mark.asyncio
async def test_an_unreachable_relay_is_a_delivery_error():
    with patch(SMTP, side_effect=ConnectionRefusedError()):
        with pytest.raises(EmailDeliveryError):
            await _sender().send("a@x.com", "s", "b")


@pytest.mark.asyncio
async def test_close_without_a_connection_does_nothing():
    with patch(SMTP) as smtp_class:
        await _sender().close()

    smtp_class.assert_not_called()
