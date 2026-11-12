class ConsoleEmailSender:
    """Prints the message instead of sending it.

    The default outside production, so running the monthly job against a
    development database can never mail a real investee.
    """

    async def send(self, to: str, subject: str, body: str) -> None:
        print(f"--- e-mail (não enviado) ---\nPara: {to}\nAssunto: {subject}\n\n{body}\n")

    async def close(self) -> None:
        return None
