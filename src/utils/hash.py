from __future__ import annotations

from hashlib import pbkdf2_hmac

def channel_hash(channel_name: str, passwd: str) -> str:
  """Hash a channel with a password, return a long string of the hashed password."""
  passwd_bytes = passwd.encode()
  channl_bytes = channel_name.encode()
  resulting_hash = pbkdf2_hmac("sha512", passwd_bytes, channl_bytes, 32768)
  return resulting_hash.hex()