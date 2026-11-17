from typing import Protocol


class EmailDeliveryError(Exception):
    """The message did not leave: the relay refused it or could not be reached.

    Raised only when nothing was handed over — the sender or a recipient was
    refused, or the message was rejected outright — so retrying cannot
    duplicate it. Adapters translate their own failures into this, so a use
    case can record the failure without knowing which transport was in use.
    """


class EmailDeliveryUncertain(Exception):
    """The message may have left: the transfer broke before the relay answered.

    The relay could have queued it a moment before the connection dropped.
    Retrying could put a second copy in the inbox, so the send must be left
    for a person to confirm instead.
    """


class EmailSender(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

    async def close(self) -> None:
        """Release whatever the sender kept open between messages."""
        ...
