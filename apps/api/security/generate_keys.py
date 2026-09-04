"""
AstroOS — RSA Key Generation Script

Run once to generate the RS256 key pair used for JWT signing:
    python apps/api/security/generate_keys.py

Keys are written to apps/api/security/keys/ which is gitignored.
In production, mount these keys as secrets (e.g., Kubernetes Secret or
environment-injected files); do not bake them into container images.
"""

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

KEY_DIR = Path(__file__).parent / "keys"
PRIVATE_KEY_PATH = KEY_DIR / "private.pem"
PUBLIC_KEY_PATH = KEY_DIR / "public.pem"


def generate_rsa_key_pair(key_size: int = 2048) -> None:
    KEY_DIR.mkdir(parents=True, exist_ok=True)

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )

    # Write private key (PEM, PKCS8, no passphrase)
    PRIVATE_KEY_PATH.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    PRIVATE_KEY_PATH.chmod(0o600)

    # Write public key (PEM, SubjectPublicKeyInfo)
    PUBLIC_KEY_PATH.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    PUBLIC_KEY_PATH.chmod(0o644)

    print(f"[OK] Private key -> {PRIVATE_KEY_PATH}")
    print(f"[OK] Public  key -> {PUBLIC_KEY_PATH}")


if __name__ == "__main__":
    generate_rsa_key_pair()
