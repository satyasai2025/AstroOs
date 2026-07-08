---
name: AstroOS bcrypt/passlib
description: AstroOS uses bcrypt directly, not passlib, due to version conflict
---

passlib<1.8 crashes with bcrypt>=4.0. AstroOS bypasses this by importing bcrypt directly in security/password.py rather than using passlib.CryptContext.

**Why:** The project targets bcrypt>=4.0 for security. passlib is not in requirements.txt.

**How to apply:** Never add passlib as a dependency. All password hashing goes through apps/api/security/password.py which wraps bcrypt directly.
