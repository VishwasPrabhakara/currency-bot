# Security Policy

## Reporting

Report suspected vulnerabilities privately through GitHub's security advisory
feature. Do not include API keys or credentials in public issues.

## Credentials and data

- Never commit `.env` or Gemini credentials.
- Configure production secrets through Cloud Run or Secret Manager.
- User prompts are sent to Gemini.
- Currency requests are sent to the public Frankfurter API.
- The bundled ADK web UI is a demonstration surface and does not add
  application-level authentication, rate limiting, or abuse controls.
