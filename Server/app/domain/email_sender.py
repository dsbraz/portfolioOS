from typing import Protocol


class EmailDeliveryError(Exception):
    """The message did not leave: the relay refused it or could not be reached.

    Adapters translate their own failures into this, so a use case can record
    the failure and move on without knowing which transport was in use.
    """


class EmailSender(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

    async def close(self) -> None:
        """Release whatever the sender kept open between messages."""
        ...
