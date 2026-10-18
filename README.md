# Alpha Desk Research — Reddit access review

Private Windows stock-research and paper-trading prototype. This repository is a source-code review snapshot of the proposed Reddit connector, not a complete trading application or a Reddit-approved integration.

## Purpose

Find public discussions about biotechnology, AI, and other listed companies as **unverified leads**. The full local desk then looks for original company announcements and regulatory sources. A Reddit post, ticker match, popularity, or retrieved company document does not establish that a claim is true or that a trade is worthwhile.

The current desk is paper-only, with a separate read-only IBKR connection workflow. This snapshot contains no broker connector or order submission code. The owner's longer-term goal includes investment decisions and autonomous trading. That future use is disclosed for Reddit to assess; it is not enabled here. This is personal investment research, not an academic research project.

## Access requested

- OAuth scope: `read` only; confidential web-app authorization code flow.
- Initial coverage: public submissions in `r/stocks` and `r/Biotechplays`.
- Two listing requests per manual refresh, up to 25 recent submissions per subreddit.
- Selected fields: post ID, title, permalink, publication/observation time, and locally matched company/ticker symbols.
- No comments, post bodies, usernames, profiles, private messages, voting, posting, or moderation actions are needed.
- No Reddit-content model training, resale, or public redistribution is planned. AI-assisted downstream analysis is intended, subject to approval for that use.

**Approval is pending.** Creating an OAuth app or authorizing a user does not constitute Reddit usage approval. Collection must remain disabled until Reddit explicitly approves the described use. The approval flag in this prototype is an operator assertion, not a way to obtain or prove approval.

## Included source

| File | Role |
| --- | --- |
| `backend/discovery.py` | Optional read-only API listing retrieval and unverified lead normalization |
| `backend/reddit_auth.py` | Local OAuth setup and Windows-user DPAPI credential storage |
| `backend/universe.py` | Explicit four-company starter registry and official source locations |
| `tests/test_connector.py` | Offline checks for approval gating, URL restrictions, and unverified output |

The connector is a snapshot of the local project. The broader dashboard, official-document research pipeline, broker probes, personal configuration, and collected data are intentionally outside this repository.

## Local operation

Python 3.12; standard library only. From this repository folder, offline checks can run without Reddit access:

```powershell
python -m unittest discover -s tests -v
```

After usage approval and app registration, the Windows-only setup entry point is:

```powershell
python -m backend.reddit_auth
```

It serves a temporary setup form at `http://127.0.0.1:8765`, using callback `http://127.0.0.1:8765/callback`. Enter credentials only in that local form. OAuth requests only the read scope. Stop the local server after use. Do not launch setup or enable collection as part of reviewing this repository.

Credentials are encrypted for the Windows user in `.local/credentials/reddit.dpapi`; they are never included in this snapshot. DPAPI does not protect against other software already running as the same Windows user. A separate environment-token path also exists in the connector and requires an explicit approval flag; do not enable either path while approval is pending.

## Current limits

- No continuous monitoring or scheduler in this snapshot.
- No independent claim verification or trade authorization in the Reddit connector.
- No automated deletion reconciliation or approved retention schedule yet. Those must be implemented to match the granted terms before ongoing collection.
- Response size caps, timeouts, and redirect refusal exist; full rate-limit/backoff management remains to be added before scheduled operation.
- The app runs outside Reddit on a private Windows machine. Reddit must determine whether this architecture and investment-related use are eligible and which approval/licensing route applies.

See Reddit's [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy). This project does not claim endorsement or approval from Reddit or Interactive Brokers.

Prepared locally for owner review. Nothing has been published or submitted.
