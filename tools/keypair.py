import getpass
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


def generate(path):
    password = getpass.getpass("Password (Enter for none):")
    private_key = ed25519.Ed25519PrivateKey.generate()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode())
        if password
        else serialization.NoEncryption(),
    )
    with open(f"{path}.key", "wb") as f:
        f.write(private_pem)

    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with open(f"{path}.pub", "wb") as f:
        f.write(public_pem)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: keypair.py <keyfilename-prefix>")
        sys.exit(1)
    generate(sys.argv[1])
