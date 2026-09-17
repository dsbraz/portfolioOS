import bcrypt

# bcrypt reads at most 72 bytes of the password. Truncating here keeps the rule
# explicit and independent of the library version: bcrypt 5 raises on longer
# input, while passlib and bcrypt 4 truncated silently.
_MAX_PASSWORD_BYTES = 72


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:_MAX_PASSWORD_BYTES]


class BcryptPasswordHasher:
    def hash(self, password: str) -> str:
        return bcrypt.hashpw(_encode(password), bcrypt.gensalt(rounds=12)).decode(
            "ascii"
        )

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(_encode(plain_password), hashed_password.encode("ascii"))
