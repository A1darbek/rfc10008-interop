# Security

Do not submit private authorization tokens, cookies, production customer data,
or unredacted sensitive request bodies in fixtures or receipts.

If a target requires authentication, use local environment variables and redact
all sensitive evidence before committing receipts.
