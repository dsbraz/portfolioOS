import pytest

from app.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher


def test_long_password_is_truncated_to_72_bytes():
    # bcrypt only reads 72 bytes. Passlib and bcrypt 4 truncated silently;
    # bcrypt 5 raises instead, which would lock out existing long passwords.
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash("a" * 80)
    assert hasher.verify("a" * 72, hashed)
    assert hasher.verify("a" * 100, hasher.hash("a" * 72))
    assert not hasher.verify("a" * 71, hashed)


@pytest.mark.parametrize("prefix", ["2a", "2b", "2y"])
def test_verifies_existing_passlib_hash(prefix):
    # Generated with Passlib before replacing the adapter.
    stored_hash = f"${prefix}$04$JxIvSTKeIjExcJX5HCljj.IG5XoZa95n1RNzVAxzBP4Cz2dFkSPZi"
    hasher = BcryptPasswordHasher()
    assert hasher.verify("legacy-password", stored_hash)
    assert not hasher.verify("wrong-password", stored_hash)


@pytest.mark.parametrize("password", ["password123", "senha-áçã🔒", "a" * 72, "é" * 40])
def test_hash_round_trip(password):
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash(password)
    assert hashed.startswith("$2b$12$")
    assert hasher.verify(password, hashed)
    assert not hasher.verify("wrong-password", hashed)


def test_hash_uses_random_salt():
    hasher = BcryptPasswordHasher()
    assert hasher.hash("password") != hasher.hash("password")
