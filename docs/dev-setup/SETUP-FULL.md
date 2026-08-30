# SETUP — full manual copy

> **Note:** This documents the original development environment setup (Windows/WSL/VS Code/Claude Code). It is **not required** to run this project. See the root [README.md](../../README.md) for usage instructions.

Every step, in order, no script. Use this when `setup.sh` cannot run — a locked
down machine, a shell that is not bash, or when you want to watch each step land.

`SETUP.md` is the short version: manual steps plus `./setup.sh` for the rest.
This file is the same content expanded. **When something changes, change
`setup.sh` and `SETUP.md` first, then regenerate this file** — it is the copy
most likely to drift.

Verified end to end on: Windows + WSL2, Ubuntu 26, Python 3.14, AWS CLI 2.31.35,
Claude Sonnet 4.5 on Bedrock.

Legend: **PS** = PowerShell as administrator · **UB** = Ubuntu shell ·
**AWS** = AWS Console · **VS** = VS Code

---

## A — WSL

| ID | Where | Step |
|----|-------|------|
| **A1** | PS | `wsl -l -v` |
| **A2** | PS | `wsl --update` |
| **A3** | PS | `wsl --shutdown` — only if A4 fails |
| **A4** | PS | `wsl -d Ubuntu` |
| **A5** | PS | Reboot Windows, retry A4 — only if A3 did not help |
| **A6** | PS | Re-enable Windows features, reboot — only if A5 did not help |

```powershell
# A1
wsl -l -v

# A2
wsl --update

# A4
wsl -d Ubuntu
```

A1 printing `Ubuntu Stopped 2` means Ubuntu is installed already. Do not run
`wsl --install` — it fails with `ERROR_ALREADY_EXISTS`.

A4 first launch prompts for a Linux username and password. These are separate
from your Windows login.

```powershell
# A6 — last resort, reboot afterwards
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

> On the reference build, A4 failed once with `Wsl/Service/E_UNEXPECTED` and
> `wsl --update` alone fixed it. A3, A5 and A6 were never needed.

---

## B — Node and Claude Code

| ID | Where | Step |
|----|-------|------|
| **B1** | UB | Install nvm |
| **B2** | UB | Install Node LTS |
| **B3** | UB | Install Claude Code |

```bash
# B1
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc

# B2
nvm install --lts
node -v

# B3
npm install -g @anthropic-ai/claude-code
```

Behind a corporate proxy, set the registry first:
```bash
npm config set proxy http://HOST:PORT
npm config set https-proxy http://HOST:PORT
```

---

## C — System packages and AWS CLI

| ID | Where | Step |
|----|-------|------|
| **C1** | UB | Base packages |
| **C2-alt** | UB | AWS CLI v2 from apt |

```bash
# C1
sudo apt update && sudo apt install -y unzip python3-pip python3-venv curl

# C2-alt
sudo apt update && sudo apt install -y awscli
aws --version
```

Confirm the output reports `aws-cli/2.x`. **v2 is required** — v1's
`aws configure sso` is limited, and SSO is how you will authenticate to a
company account.

<details>
<summary>C2 — original installer, only if apt gives you v1</summary>

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install
```
</details>

---

## D — AWS account wiring

**Repeat this whole section per AWS account.**

| ID | Where | Step |
|----|-------|------|
| **D0** | AWS | Create an access key |
| **D1** | UB | `aws configure` |
| **D2** | UB | Verify identity resolves |
| **D3** | AWS | One-time Anthropic use-case form |
| **D4** | AWS | Confirm no `AccessDeniedException` |
| **D5** | AWS | Billing alarm |
| **D6** | AWS | Note the exact model inference profile ID |

### D0 — access key
IAM → Users → your user → Security credentials → Create access key.
Use case: **Command Line Interface (CLI)**. Description tag: `wsl-bedrock-dev`.
Copy both values before leaving the page; the secret is shown once.

The use-case field is informational — it does not restrict what the key can do.
AWS will suggest IAM Identity Center instead; acknowledge and continue for a
personal account.

> Company account: use `aws configure sso` instead of an access key.

### D1 / D2
```bash
# D1 — prompts for key, secret, region (us-east-1), output format (Enter)
aws configure

# D2
aws sts get-caller-identity
```
D2 works even before Bedrock is enabled — it is IAM, not Bedrock.

### D3 — Anthropic use-case form
Bedrock → Playgrounds → Chat/Text → select a Claude model → fill the form if
prompted → send a test prompt.

The **Model access page is retired**. Serverless models are auto-enabled per
account; Anthropic models still need this form once. With AWS Organizations,
submitting at the management account level via API covers child accounts.

### D4 — verification wait
A new account may report that it is being verified. Normally clears in under two
hours. Not a configuration error. If it runs longer, confirm a valid payment
method is on file.

### D5 — billing alarm
Budgets → **Monthly cost budget** → $25 → alerts at 80% and 100%.
Avoid "Zero spend budget" — it fires on the first call and stops being a signal.

### D6 — model ID
Model catalog → the card for your model → copy the inference profile ID.
Do not assume one. Availability varies by account and region.

Reference build: Sonnet 4.5 available, Sonnet 5 not.
```
us.anthropic.claude-sonnet-4-5-20250929-v1:0
```

While here, note the Haiku ID too — useful later for high-volume calls
(retrieval filtering, verification passes) with Sonnet reserved for reasoning.

### IAM permissions
```
bedrock:InvokeModel
bedrock:InvokeModelWithResponseStream
bedrock:ListFoundationModels
bedrock:ListInferenceProfiles
aws-marketplace:Subscribe
aws-marketplace:ViewSubscriptions
```

---

## E — Claude Code on Bedrock

| ID | Where | Step |
|----|-------|------|
| **E1** | UB | Backend and region |
| **E1-alt** | UB | Pin the model |
| **E2** | UB | Launch and verify |
| **E3** | UB | Clear a conflicting key — only if E2 falls back |

```bash
# E1
echo 'export CLAUDE_CODE_USE_BEDROCK=1' >> ~/.bashrc
echo 'export AWS_REGION=us-east-1' >> ~/.bashrc

# E1-alt
echo 'export ANTHROPIC_MODEL=us.anthropic.claude-sonnet-4-5-20250929-v1:0' >> ~/.bashrc

source ~/.bashrc

# E2
claude
```

At the E2 prompt, ask which model and backend it is running on. Expected shape:

> I'm Claude Sonnet 4.5 running on AWS Bedrock. The exact model ID is
> us.anthropic.claude-sonnet-4-5-20250929-v1:0.

If it mentions a subscription or an API key instead:
```bash
# E3
unset ANTHROPIC_API_KEY
```
An `ANTHROPIC_API_KEY` in the environment outranks the Bedrock provider setting.

---

## F — Project scaffold

| ID | Where | Step |
|----|-------|------|
| **F1** | UB | Project directory |
| **F2** | UB | Virtual environment |
| **F3** | UB | Dependencies |
| **F4** | UB | Open in VS Code |
| **F5** | UB | `.gitignore` |
| **F6** | VS | Disable Copilot for this workspace |
| **F7** | VS | Hide the Copilot chat panel — optional |
| **F8** | VS | Claude Code VS Code extension — optional |

```bash
# F1
mkdir -p ~/projects/eko-agent && cd ~/projects/eko-agent

# F2
python3 -m venv .venv
source .venv/bin/activate

# F3
pip install boto3 chromadb

# F5
cat > .gitignore << 'EOF'
.venv/
.env
chroma_db/
__pycache__/
*.pyc
EOF

# F4
code .
```

**F1** — keep the project under `$HOME`, not `/mnt/c/`. Windows-mounted paths are
slower from WSL and unreliable with file-watching tools.

**F4** — first run downloads the VS Code server into WSL. Bottom-left should read
**WSL: Ubuntu**. Requires the Microsoft WSL extension on the Windows side. When
VS Code asks which Python interpreter to use, pick `./.venv/bin/python`.

**F6** — `Ctrl+Shift+P` → Preferences: Open Workspace Settings (JSON):
```json
{
  "github.copilot.enable": { "*": false }
}
```
Scoped to this workspace; Copilot stays on elsewhere. Optional, but it keeps
authorship clear on a project meant to demonstrate your own design work, and
avoids Copilot's inline suggestions fighting Claude Code's edits.

**F7** — the Copilot *chat* panel is separate from inline completions and survives
F6. Right-click its Activity Bar icon → Hide from Activity Bar.

**F8** — the official Claude Code VS Code extension gives a side panel with visual
diffs instead of the terminal. It wraps the same CLI, so the Bedrock
configuration carries over unchanged. The terminal version is sufficient.

---

## G — Done-check

| ID | Check |
|----|-------|
| **G1** | `claude` runs and confirms it is on Bedrock |
| **G2** | `python test_bedrock.py` returns a response and a token count |
| **G3** | Billing alarm set — done in D5 |

`test_bedrock.py`:

```python
import boto3

client = boto3.client("bedrock-runtime", region_name="us-east-1")

response = client.converse(
    modelId="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    messages=[{"role": "user", "content": [{"text": "Reply with exactly: connection confirmed."}]}],
    inferenceConfig={"maxTokens": 50},
)

print(response["output"]["message"]["content"][0]["text"])
print("tokens:", response["usage"])
```

```bash
python test_bedrock.py
```

Expected:
```
connection confirmed.
tokens: {'inputTokens': 14, 'outputTokens': 6, 'totalTokens': 20, ...}
```

The token count is worth noting. A trivial call is ~20 tokens; real agent calls
run 2,000–20,000 each once documents are in context, and a multi-agent run fans
that out several times per question.

---

## While on a personal AWS account

Synthetic or public documents only. No client data, no work documents, no real
business content — not even for testing retrieval. Re-index against real data
only after moving to the company account.
