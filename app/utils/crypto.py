"""Cryptographic utilities for LedgerLens.
Supports offline Ed25519 signature checks for release manifests and commercial licenses.
Zero internet or phone-home needed.
"""

from __future__ import annotations
import base64
import hashlib
from typing import Optional
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

# Embedded public verification key for official LedgerLens releases and offline licenses
# Corresponds to official release signing key
DEFAULT_PUBLIC_KEY_HEX = "7d4b68e95c1a89b7e3f20d65b4c1a9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2"

def verify_ed25519_signature(
    data_bytes: bytes,
    signature_b64: str,
    public_key_hex: str = DEFAULT_PUBLIC_KEY_HEX
) -> bool:
    """Verify an Ed25519 signature offline against known public key."""
    try:
        pub_key_bytes = bytes.fromhex(public_key_hex)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_key_bytes)
        try:
            signature_bytes = base64.b64decode(signature_b64)
        except Exception:
            signature_bytes = bytes.fromhex(signature_b64)
        public_key.verify(signature_bytes, data_bytes)
        return True
    except (InvalidSignature, ValueError, Exception):
        return False

def compute_sha256(data: bytes) -> str:
    """Calculate the sha256 checksum of raw bytes."""
    return hashlib.sha256(data).hexdigest()

def compute_file_sha256(file_path: str) -> str:
    """Calculate the sha256 checksum of a file on disk."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def verify_offline_license(license_key: str) -> dict:
    """Validate an offline commercial license key formatted as PAYLOAD.SIG.
    Returns status dict with active status and license metadata.
    """
    if not license_key or "." not in license_key:
        return {"valid": False, "tier": "free", "reason": "No license key provided or invalid format"}

    parts = license_key.strip().split(".", 1)
    payload_b64, sig_b64 = parts[0], parts[1]

    try:
        payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8") + b"==")
        payload_str = payload_bytes.decode("utf-8")
        
        # Verify Ed25519 signature
        is_valid = verify_ed25519_signature(payload_bytes, sig_b64)
        if is_valid:
            return {
                "valid": True,
                "tier": "pro",
                "payload": payload_str,
                "reason": "Verified offline perpetual license"
            }
        else:
            return {"valid": False, "tier": "free", "reason": "Invalid cryptographic signature"}
    except Exception as e:
        return {"valid": False, "tier": "free", "reason": f"License verification error: {e}"}
