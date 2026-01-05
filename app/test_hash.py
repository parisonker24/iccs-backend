from app.core.security import get_password_hash, verify_password


def test_password_hash_and_verify():
	"""Hash a password with the project's context and verify it."""
	password = "Paris@224"
	hashed = get_password_hash(password)
	assert verify_password(password, hashed)
	assert not verify_password("wrong-password", hashed)
