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
        smtp = smtp_class.return_value.__enter__.return_value

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
        smtp = smtp_class.return_value.__enter__.return_value

        await _sender(username=None, password=None).send("a@x.com", "s", "b")

    smtp.login.assert_not_called()


@pytest.mark.parametrize(
    "failure",
    [smtplib.SMTPRecipientsRefused({"a@x.com": (550, b"no")}), ConnectionRefusedError()],
)
@pytest.mark.asyncio
async def test_transport_failures_become_delivery_errors(failure):
    with patch("app.infrastructure.smtp_email_sender.smtplib.SMTP") as smtp_class:
        smtp_class.return_value.__enter__.return_value.send_message = MagicMock(
            side_effect=failure
        )

        with pytest.raises(EmailDeliveryError):
            await _sender().send("a@x.com", "s", "b")
