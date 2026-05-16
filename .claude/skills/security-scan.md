---
name: security-scan
description: Run security-focused code scans across the project
---

Perform a security sweep across the codebase. Check for:

1. **Hardcoded secrets**: Search for API keys, passwords, tokens in source files
2. **SQL injection risks**: Verify SQLAlchemy parameterized queries, check raw SQL in `backend/app/`
3. **XSS vulnerabilities**: Check frontend rendering of user data without sanitization
4. **Command injection**: Check any `os.system`, `subprocess`, or shell execution points
5. **JWT/auth issues**: Review `backend/app/core/security.py` for token validation, expiration, bcrypt rounds
6. **Judge bypass**: Run `backend/tests/unit/test_bypass_detection.py` and verify bypass patterns are caught
7. **Dependencies**: Check `requirements.txt` and `package.json` for known vulnerabilities (if tools available)

Report findings with file paths and line numbers. Flag critical issues immediately.
