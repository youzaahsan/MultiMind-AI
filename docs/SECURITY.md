# MultiMind AI — Security Architecture & Defenses

MultiMind AI is engineered with defense-in-depth security principles covering authentication, input sanitization, file inspection, safe tool execution, and secret management.

---

## 1. Authentication & Password Security

* **Password Hashing:** Utilizes **PBKDF2-HMAC-SHA256** with 100,000 iterations and a cryptographically secure 16-byte random salt per user (`app/utils/security.py`).
* **JWT Access Tokens:** Issues signed JSON Web Tokens encoded with `HS256` and secret keys stored strictly in `.env`.
* **Zero Hard-Coded Credentials:** All passwords, keys, and tokens are read exclusively from environment variables.

---

## 2. File Ingestion & Storage Validation

* **Path Traversal Prevention:** `sanitize_filename()` strips all occurrences of `..`, `/`, `\`, null bytes, and non-printable control characters.
* **Size Enforcement:** Maximum upload size (default 50MB) is strictly enforced in memory before saving to disk.
* **Magic Byte Verification:** File payloads are verified against binary signatures to prevent MIME spoofing:
  * PDF: `%PDF`
  * PNG: `\x89PNG\r\n\x1a\n`
  * JPEG: `\xff\xd8\xff`
  * DOCX & XLSX: `PK\x03\x04`
  * WEBP: `RIFF`

---

## 3. Safe Agent Tools — Zero Code Execution

* **No `eval()` or `exec()`:** Arbitrary code execution is completely prohibited.
* **AST Mathematical Evaluator:** The `calculator` tool parses queries into an Abstract Syntax Tree (`ast.parse`) and allows ONLY certified binary arithmetic operators (`+`, `-`, `*`, `/`, `^`, `%`). Any variable lookup, attribute access, function invocation, or system import immediately raises a syntax violation error.

---

## 4. Prompt Injection Defenses

* **Regex Pattern Defense (`sanitize_prompt_input`):** Detects and neutralizes adversarial patterns:
  * *"ignore all previous instructions"*
  * *"disregard prior directives"*
  * *"you are now in developer mode"*
  * *"system: override"*
  * *"bypass safety filters"*
* Flagged instructions are purged from the prompt context, and the turn is marked suspicious for audit logging.

---

## 5. Secret Masking in Logs

* **`SecretMaskingFilter` (`app/utils/logging.py`):** Automatically intercepts log records and redacts API keys, Bearer tokens, passwords, and JWT tokens before writing to disk or console.
