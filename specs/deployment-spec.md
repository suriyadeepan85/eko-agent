# Deployment Spec

Depends on: `specs/ui-spec.md`.

Hosts the Streamlit UI on Streamlit Community Cloud so a reviewer can use the system
without an AWS account of their own.

**This is out of scope per the case study brief**, which excludes cloud and production
deployment. It exists to remove a reviewer's setup burden, not to satisfy a
requirement. Build it only after the evaluation runs and the README are complete.

---

## What this trades

Queries run on **your** AWS account, billed to you. There is no way around this: if a
reviewer uses a hosted app without their own credentials, yours are doing the work.

Three consequences, each with a control below:

| Risk | Control |
|---|---|
| Public URL — Streamlit Community Cloud apps have no auth by default | Shared password via secrets |
| Unbounded spend — Bedrock has no per-app cap, and AWS credits offset the bill rather than stopping it | Per-session question cap |
| Credential blast radius — the key sits in a third party's secrets store | Dedicated IAM user, one permission |

AWS credits do not act as a spending limit. They offset charges until exhausted, then
billing continues. The $100 of credits is cushion, not a ceiling.

---

## AWS credentials

**A dedicated IAM user**, created for this deployment and deleted when it comes down.
Never the credentials used for local development.

If the deployed key leaks, the damage is Bedrock model invocations on one model —
visible in usage metrics and stopped instantly by deleting the user. A leaked
development key would expose whatever that user can do, which on a personal account
is usually everything.

### Creating it

IAM → Users → Create user → name `eko-streamlit-demo` → **no console access** →
attach an inline policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0",
        "arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude-sonnet-4-5-20250929-v1:0"
      ]
    }
  ]
}
```

Both ARNs are needed: an inference profile call resolves to the underlying foundation
model, and the policy must permit each. Verify the exact ARNs in the Bedrock console
rather than trusting this file — they vary by account and region.

No `bedrock:ListFoundationModels`, no marketplace permissions, no S3, no IAM. The
user can invoke one model and nothing else.

Then create an access key for it. This key goes into Streamlit secrets and nowhere
else — not into the repository, not into `.env`, not into a commit.

---

## Secrets

Streamlit Community Cloud stores secrets per app, editable in the app's settings.

```toml
AWS_ACCESS_KEY_ID = "..."
AWS_SECRET_ACCESS_KEY = "..."
AWS_REGION = "us-east-1"
BEDROCK_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
APP_PASSWORD = "..."
```

**Code change required.** Locally, boto3 finds credentials through the AWS credential
chain at `~/.aws`. On Streamlit there is no such file. Whatever creates the
`bedrock-runtime` client must read `st.secrets` when present and fall back to the
credential chain otherwise, so the same code runs both ways.

This is the only code change deployment requires. The pipeline does not know where it
runs.

Before deploying, confirm nothing is committed:

```bash
git ls-files | grep -iE "\.env|secret|credential"
git grep -iE "AKIA" $(git rev-list --all) | head
```

Both must return nothing.

---

## Access control

**Shared password.** A single password from `st.secrets`, entered before the app is
usable. Given to reviewers directly.

Not real authentication — no accounts, no rate limiting per user, no audit trail of
who asked what. It is a gate against a public URL being found, indexed, or forwarded.
That is proportionate to what is behind it: a demo that can invoke one model.

Implementation: check the password in `st.session_state` before rendering anything
else. On failure, show only the password prompt — do not render the corpus status or
the question input.

---

## Usage cap

**30 questions per session.** An exit button resets the count.

Counted in `st.session_state`, so it is per browser session. A visitor who refreshes
gets another 30 — this is a soft limit, not a hard one, and the password gate is what
actually bounds exposure.

At roughly 5,000 tokens per question across four LLM calls, 30 questions is on the
order of cents. The cap exists to bound a runaway tab or an automated loop, not to
manage cost in normal use.

When the cap is reached, show a clear message and disable the input. Do not fail
silently or return an error that reads as a system fault.

---

## Corpus and ephemeral storage

Streamlit Community Cloud containers are ephemeral and restart on idle.

**`chroma_db/` does not survive.** It is gitignored, so a fresh deploy has no
collection at all. Ingestion runs at startup per `specs/ui-spec.md` — the collection
count check handles both first deploy and post-restart with no special casing.

Do not commit `chroma_db/` to work around this. It would add binary files to the
repository and couple it to a Chroma version, to save a few seconds of startup.

**`runs/` does not survive either.** Run records written by the hosted app are lost on
restart. Acceptable: the durable evidence is the committed records in `evidence/`,
produced by local runs. Note this in the app rather than implying records persist.

---

## Deploying

1. Push to GitHub. The app deploys from the repository.
2. `requirements.txt` must exist and list every dependency — `streamlit`, `boto3`,
   `chromadb`. Streamlit Cloud installs from it and will not guess.
3. share.streamlit.io → New app → select the repository, branch, and `app.py`.
4. Add secrets in the app's settings before the first run, or it will start and fail
   on the first Bedrock call.
5. Verify with the three build-target questions from `specs/ui-spec.md`.

---

## Teardown

Delete both when evaluation is complete:

1. The Streamlit app, from share.streamlit.io.
2. The IAM user `eko-streamlit-demo`, which invalidates the key.

Delete the IAM user even if the app is only paused. A paused app's secrets still hold
a live key.

Removing the deployment does not reduce what a reviewer can see — `evidence/` holds
committed run records with full traces, and those need no credentials at all.

---

## Done-criteria

1. The IAM user can invoke Claude Sonnet 4.5 and nothing else. Verify by attempting
   an unrelated call — for example `aws s3 ls` with that key — and confirming it is
   denied.
2. No credentials appear anywhere in the repository or its history.
3. The app prompts for the password before rendering any other content.
4. On first load after deploy, the corpus ingests and shows "Corpus loaded: 20
   documents".
5. The three build-target questions return the same answers as the CLI, with the
   Precedence panel naming D4 over C3 on Q2.
6. Reaching 30 questions disables input with a clear message.
7. Teardown removes both the app and the IAM user.
