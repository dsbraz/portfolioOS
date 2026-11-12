import smtplib
from unittest.mock import MagicMock, patch

import pytest

from app.domain.email_sender import EmailDeliveryError
from app.infrastructure.smtp_email_sender import SmtpEmailSender


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


@pytest.mark.asyncio
async def test_sends_over_starttls_with_login():
    with patch("app.infrastructure.smtp_email_sender.smtplib.SMTP") as smtp_class:
        smtp = smtp_class.return_value

        await _sender().send("ana@payface.com", "Assunto", "Corpo")

    smtp_class.assert_called_once_with("smtp.example.com", 587, timeout=30.0)
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with("portfolio@example.com", "app-password")
    message = smtp.send_message.call_args.args[0]
    assert message["From"] == "portfolio@example.com"
    assert message["To"] == "ana@payface.com"
    assert message["Subject"] == "Assunto"
    assert message.get_content().strip() == "Corpo"


@pytest.mark.asyncio
async def test_relay_without_authentication_skips_login():
    with patch("app.infrastructure.smtp_email_sender.smtplib.SMTP") as smtp_class:
        await _sender(username=None, password=None).send("a@x.com", "s", "b")

    smtp_class.return_value.login.assert_not_called()


@pytest.mark.asyncio
async def test_one_connection_and_one_login_serve_the_whole_run():
    with patch("app.infrastructure.smtp_email_sender.smtplib.SMTP") as smtp_class:
        smtp = smtp_class.return_value
        sender = _sender()

        await sender.send("a@x.com", "s", "b")
        await sender.send("b@x.com", "s", "b")
        await sender.close()

    smtp_class.assert_called_once()
    smtp.login.assert_called_once()
    assert smtp.send_message.call_count == 2
    smtp.quit.assert_called_once()


@pytest.mark.parametrize(
    "failure",
    [smtplib.SMTPRecipientsRefused({"a@x.com": (550, b"no")}), ConnectionResetError()],
)
@pytest.mark.asyncio
async def test_a_failure_drops_the_connection_and_the_next_send_reconnects(failure):
    first, second = MagicMock(), MagicMock()
    first.send_message.side_effect = failure
    with patch(
        "app.infrastructure.smtp_email_sender.smtplib.SMTP",
        side_effect=[first, second],
    ) as smtp_class:
        sender = _sender()

        with pytest.raises(EmailDeliveryError):
            await sender.send("a@x.com", "s", "b")
        await sender.send("b@x.com", "s", "b")

    assert smtp_class.call_count == 2
    first.quit.assert_called_once()
    second.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_an_unreachable_relay_is_a_delivery_error():
    with patch(
        "app.infrastructure.smtp_email_sender.smtplib.SMTP",
        side_effect=ConnectionRefusedError(),
    ):
        with pytest.raises(EmailDeliveryError):
            await _sender().send("a@x.com", "s", "b")


@pytest.mark.asyncio
async def test_close_without_a_connection_does_nothing():
    with patch("app.infrastructure.smtp_email_sender.smtplib.SMTP") as smtp_class:
        await _sender().close()

    smtp_class.assert_not_called()
