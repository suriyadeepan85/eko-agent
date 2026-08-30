# SETUP

> **Note:** This documents the original development environment setup (Windows/WSL/VS Code/Claude Code). It is **not required** to run this project. See the root [README.md](../../README.md) for usage instructions.

Local environment for the Enterprise Knowledge Ops Agent.
Windows → WSL Ubuntu → VS Code, with Claude via Amazon Bedrock.
No Anthropic subscription or API key is involved anywhere in this path.

**This file covers only what a script cannot do.** Everything else is in
`setup.sh`. Step IDs match `SETUP-FULL.md`, which holds the complete manual
copy if you would rather run every command yourself.

Order: **A → D → `./setup.sh` → E2 → F4/F6**

---

## A — WSL

Windows side. Run in **PowerShell as administrator**.

| ID | Step |
|----|------|
| **A1** | `wsl -l -v` — check what is already installed |
| **A2** | `wsl --update` |
| **A4** | `wsl -d Ubuntu` — first launch asks you to create a Linux username and password, separate from your Windows login |

A1 reporting `Ubuntu Stopped 2` means Ubuntu is already installed. Skip
`wsl --install`; it will fail with `ERROR_ALREADY_EXISTS`.

**If A4 fails** — see Troubleshooting below. On the reference build, `wsl --update`
alone cleared a `Wsl/Service/E_UNEXPECTED` failure.

**On a work laptop:** WSL install and update may be blocked by policy or need
admin rights you do not have. Confirm this before planning around the rest.

---

## D — AWS account wiring

Console plus one terminal command. **Repeat this whole section for each AWS
account** — this is the part that changes when you move from a personal account
to a company one.

| ID | Step |
|----|------|
| **D0** | IAM → Users → your user → Security credentials → Create access key. Use case: **Command Line Interface (CLI)**. Tag it something like `wsl-bedrock-dev`. Copy both values — the secret is shown once. |
| **D1** | `aws configure` — key, secret, region (`us-east-1`), press Enter for output format |
| **D2** | `aws sts get-caller-identity` — should print Account, UserId, Arn |
| **D3** | Bedrock → Playgrounds → Chat/Text → select a Claude model → submit the one-time Anthropic use-case form → send a test prompt |
| **D4** | Confirm no `AccessDeniedException` |
| **D5** | Budgets → **Monthly cost budget** → $25, alert at 80% and 100% |
| **D6** | Model catalog → note the exact inference profile ID for the Claude model available to you |

**D0 on a company account:** you will almost certainly use `aws configure sso`
instead of an access key. AWS CLI **v2** is required for that — v1's SSO support
is limited. `setup.sh` checks the version and warns you.

**D3 — the Model access page is retired.** Serverless foundation models are
auto-enabled per account now. Anthropic models still require this one-time
use-case form. On a company account with AWS Organizations, submitting it at the
management account level via API covers child accounts.

**D4 — "your account is currently being verified"** is normal on a new account
and typically clears in under two hours. It is not a configuration error. If it
runs past that, check that a valid payment method is on file.

**D6 — do not assume a model ID.** Availability varies by account and region.
The reference build had Sonnet 4.5 but not Sonnet 5. Whatever you find here goes
into `BEDROCK_MODEL_ID` at the top of `setup.sh` before you run it.

**IAM permissions to request on a company account:**

```
bedrock:InvokeModel
bedrock:InvokeModelWithResponseStream
bedrock:ListFoundationModels
bedrock:ListInferenceProfiles
aws-marketplace:Subscribe
aws-marketplace:ViewSubscriptions
```

Root or admin on a personal account already has these.

---

## Run the script

Covers B (Node + Claude Code), C (system packages + AWS CLI), E1/E1-alt (Bedrock
environment), F1–F3 and F5 (project scaffold), and runs the G2 connectivity test
at the end.

```bash
chmod +x setup.sh
./setup.sh
```

Edit `BEDROCK_MODEL_ID` and `AWS_REGION_DEFAULT` at the top first if D6 gave you
something different. The script is safe to re-run — every step checks before it
acts.

---

## E2 / F4 / F6 — after the script

| ID | Step |
|----|------|
| **E2** | `claude`, then ask it which model and backend it is running on. It should name Bedrock and your model ID — not a subscription or API key. |
| **F4** | `code .` from the project directory. VS Code should show **WSL: Ubuntu** bottom-left. Needs the Microsoft WSL extension on the Windows side. |
| **F6** | Disable Copilot for this workspace: `Ctrl+Shift+P` → Preferences: Open Workspace Settings (JSON) → `{ "github.copilot.enable": { "*": false } }` |

**F6 is a judgment call, not a requirement.** It keeps authorship clear on a
project meant to demonstrate your own design work, and stops Copilot's inline
suggestions from fighting Claude Code's edits in the same file.

**F7 (optional)** — the Copilot *chat* panel is separate from inline completions
and survives F6. Right-click its Activity Bar icon → Hide from Activity Bar.

**F8 (optional)** — there is an official Claude Code VS Code extension if you
prefer a side panel with visual diffs over the terminal. It wraps the same CLI,
so the Bedrock configuration carries over unchanged.

---

## Done-check

| ID | Check |
|----|-------|
| **G1** | `claude` runs and confirms it is on Bedrock |
| **G2** | `python test_bedrock.py` returns a response and a token count |
| **G3** | Billing alarm is set (done in D5) |

---

## Troubleshooting

**`wsl --install` → `ERROR_ALREADY_EXISTS`**
Ubuntu is already installed. Run `wsl -l -v`, then `wsl -d Ubuntu`.

**`wsl -d Ubuntu` → `Wsl/Service/E_UNEXPECTED`**
In order: `wsl --update` → `wsl --shutdown`, wait 10s → reboot Windows → re-enable
the Windows features and reboot:
```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

**`aws: command not found`**
Recent Ubuntu ships AWS CLI v2 in apt: `sudo apt install -y awscli`. Confirm with
`aws --version` that it reports `aws-cli/2.x`. The older curl-and-unzip installer
is only needed if apt gives you v1.

**Claude Code ignores Bedrock (E3)**
An `ANTHROPIC_API_KEY` in the environment outranks the Bedrock provider setting.
`unset ANTHROPIC_API_KEY`.

**`npm install` fails behind a corporate proxy**
```bash
npm config set proxy http://HOST:PORT
npm config set https-proxy http://HOST:PORT
```
pip uses `--proxy`; the AWS CLI reads `HTTP_PROXY` / `HTTPS_PROXY`.

**Keep the project off `/mnt/c/`**
Windows-mounted paths are slower from WSL and unreliable with file-watching
tools. `setup.sh` puts the project under `$HOME` for this reason.

---

## While on a personal AWS account

Synthetic or public documents only. No client data, no work documents, no real
business content — not even for testing retrieval. Re-index against real data
only after moving to the company account.
