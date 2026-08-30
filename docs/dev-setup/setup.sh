#!/usr/bin/env bash
#
# setup.sh — Enterprise Knowledge Ops Agent, local environment
#
# Covers the scriptable steps: B (Node + Claude Code), C (system packages +
# AWS CLI), E (Claude Code on Bedrock), F1-F3/F5 (project scaffold).
#
# NOT covered — these need a human, see SETUP.md:
#   Section A  WSL install/repair          (Windows, admin PowerShell)
#   Section D  AWS account wiring          (AWS Console + aws configure)
#
# Safe to re-run. Every step checks before it acts.
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
#
set -euo pipefail

# ---------------------------------------------------------------- config ----
AWS_REGION_DEFAULT="us-east-1"
BEDROCK_MODEL_ID="us.anthropic.claude-sonnet-4-5-20250929-v1:0"
PROJECT_DIR="$HOME/projects/eko-agent"
NVM_VERSION="v0.40.1"

# ---------------------------------------------------------------- output ----
say()  { printf '\n\033[1m>> %s\033[0m\n' "$*"; }
ok()   { printf '   \033[32m[ok]\033[0m %s\n' "$*"; }
skip() { printf '   \033[90m[--]\033[0m %s\n' "$*"; }
warn() { printf '   \033[33m[!!]\033[0m %s\n' "$*"; }
die()  { printf '\n\033[31m[fail]\033[0m %s\n\n' "$*" >&2; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

# ------------------------------------------------------------ preflight -----
say "Preflight"

if ! grep -qi microsoft /proc/version 2>/dev/null; then
  warn "Not detected as WSL. Continuing, but this script targets WSL Ubuntu."
else
  ok "Running under WSL"
fi

if [[ "$PWD" == /mnt/[a-z]/* ]]; then
  warn "You are on a Windows-mounted path ($PWD)."
  warn "The project will still be created under \$HOME, which is correct."
fi

# ------------------------------------------- C1: base system packages -------
say "C1  Base system packages"
NEEDED=(unzip python3-pip python3-venv curl)
MISSING=()
for p in "${NEEDED[@]}"; do
  dpkg -s "$p" >/dev/null 2>&1 || MISSING+=("$p")
done
if [ ${#MISSING[@]} -eq 0 ]; then
  skip "already installed: ${NEEDED[*]}"
else
  sudo apt-get update -qq
  sudo apt-get install -y "${MISSING[@]}"
  ok "installed: ${MISSING[*]}"
fi

# ------------------------------------------------ C2-alt: AWS CLI v2 --------
say "C2-alt  AWS CLI v2"
if have aws; then
  AWSV="$(aws --version 2>&1 || true)"
  case "$AWSV" in
    *aws-cli/2*) skip "already present — $AWSV" ;;
    *) warn "found v1 — $AWSV"
       warn "v1 has limited 'aws configure sso'. Install v2 manually:"
       warn "  curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o awscliv2.zip"
       warn "  unzip awscliv2.zip && sudo ./aws/install" ;;
  esac
else
  sudo apt-get install -y awscli
  ok "$(aws --version 2>&1)"
fi

# ----------------------------------------------------- B1/B2: Node LTS ------
say "B1/B2  nvm + Node LTS"
export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
  skip "nvm already installed"
else
  curl -fsSL "https://raw.githubusercontent.com/nvm-sh/nvm/${NVM_VERSION}/install.sh" | bash
  ok "nvm installed"
fi
# shellcheck disable=SC1091
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

if have node; then
  skip "node already present — $(node -v)"
else
  nvm install --lts
  ok "node $(node -v)"
fi

# ------------------------------------------------- B3: Claude Code CLI ------
say "B3  Claude Code CLI"
if have claude; then
  skip "claude already installed"
else
  npm install -g @anthropic-ai/claude-code
  ok "claude installed"
fi

# --------------------------------------- E1/E1-alt: Bedrock environment -----
say "E1/E1-alt  Bedrock environment variables"
BASHRC="$HOME/.bashrc"
add_export() {          # add_export VAR value
  local var="$1" val="$2"
  if grep -q "^export ${var}=" "$BASHRC" 2>/dev/null; then
    skip "${var} already set in .bashrc"
  else
    printf "export %s=%s\n" "$var" "$val" >> "$BASHRC"
    ok "${var} added to .bashrc"
  fi
  export "${var}=${val}"
}
add_export CLAUDE_CODE_USE_BEDROCK 1
add_export AWS_REGION "${AWS_REGION:-$AWS_REGION_DEFAULT}"
add_export ANTHROPIC_MODEL "$BEDROCK_MODEL_ID"

if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  warn "ANTHROPIC_API_KEY is set — it outranks Bedrock in Claude Code."
  warn "Run 'unset ANTHROPIC_API_KEY' (step E3) if Claude Code ignores Bedrock."
fi

# --------------------------------------------- F1/F2/F3: project scaffold ---
say "F1  Project directory"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"
ok "$PROJECT_DIR"

say "F2  Virtual environment"
if [ -d "$PROJECT_DIR/.venv" ]; then
  skip ".venv already exists"
else
  python3 -m venv .venv
  ok ".venv created"
fi
# shellcheck disable=SC1091
. "$PROJECT_DIR/.venv/bin/activate"
ok "activated — $(python --version)"

say "F3  Python dependencies"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
ok "Dependencies installed (streamlit, boto3, chromadb)"

# --------------------------------------------------------- F5: gitignore ----
say "F5  .gitignore"
if [ -f "$PROJECT_DIR/.gitignore" ]; then
  skip ".gitignore already exists"
else
  cat > "$PROJECT_DIR/.gitignore" <<'EOF'
.venv/
.env
chroma_db/
__pycache__/
*.pyc
EOF
  ok ".gitignore written"
fi

# ------------------------------------------------ G2: connectivity test -----
say "G2  Bedrock connectivity test"
if [ ! -f "$PROJECT_DIR/test_bedrock.py" ]; then
  cat > "$PROJECT_DIR/test_bedrock.py" <<EOF
import boto3

client = boto3.client("bedrock-runtime", region_name="${AWS_REGION:-$AWS_REGION_DEFAULT}")

response = client.converse(
    modelId="${BEDROCK_MODEL_ID}",
    messages=[{"role": "user", "content": [{"text": "Reply with exactly: connection confirmed."}]}],
    inferenceConfig={"maxTokens": 50},
)

print(response["output"]["message"]["content"][0]["text"])
print("tokens:", response["usage"])
EOF
  ok "test_bedrock.py written"
else
  skip "test_bedrock.py already exists"
fi

if aws sts get-caller-identity >/dev/null 2>&1; then
  ok "AWS credentials resolve"
  if python "$PROJECT_DIR/test_bedrock.py"; then
    ok "Bedrock reachable"
  else
    warn "Bedrock call failed. Check Section D in SETUP.md:"
    warn "  - one-time Anthropic use-case form submitted? (D3)"
    warn "  - account still verifying? (D4, clears in under 2h)"
    warn "  - model available in \$AWS_REGION? (D6)"
  fi
else
  warn "AWS credentials not configured — do Section D in SETUP.md, then re-run."
fi

# ------------------------------------------------------------- summary ------
say "Done"
cat <<EOF

  Project      $PROJECT_DIR
  Region       ${AWS_REGION:-$AWS_REGION_DEFAULT}
  Model        $BEDROCK_MODEL_ID

  Next:
    cd $PROJECT_DIR
    source .venv/bin/activate
    claude          # ask it which model and backend it is running on (E2/G1)

  Open a new shell, or run 'source ~/.bashrc', so the exports apply.

EOF
