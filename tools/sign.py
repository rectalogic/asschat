import base64
import sys
import time

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


def load_privkey(filename: str) -> ed25519.Ed25519PrivateKey:
    with open(filename, "rb") as f:
        keydata = f.read()
    key = serialization.load_pem_private_key(
        keydata,
        password=None,  # Use a password if your key is encrypted
    )
    if not isinstance(key, ed25519.Ed25519PrivateKey):
        raise TypeError(f"{filename} is not an ed25519 private key")
    return key


def sign(username: str, timeout: int) -> str:
    key = load_privkey("keys/dev.key")
    timestamp = int(time.time() + timeout)
    message = f"{username}:{timestamp}"
    signature = base64.urlsafe_b64encode(key.sign(message.encode())).decode()
    return f"?message={message}&signature={signature}"


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: sign.py <username> <timeout-seconds")
        sys.exit(1)
    print(sign(sys.argv[1], int(sys.argv[2])))
