#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/coledepasquale/myAI.git"
BRANCH="foundation-v0.1"
TARGET="${MYAI_HOME:-$HOME/Projects/myAI}"

say() {
  printf '\n==> %s\n' "$*"
}

if ! xcode-select -p >/dev/null 2>&1; then
  say "Apple Command Line Tools are required for git."
  xcode-select --install >/dev/null 2>&1 || true
  printf '%s\n' "A macOS installer dialog should appear. Click Install." \
    "When installation finishes, rerun the same bootstrap command."
  exit 2
fi

if [ -d "$TARGET/.git" ]; then
  say "Using existing checkout at $TARGET"
  cd "$TARGET"
  if [ -n "$(git status --porcelain)" ]; then
    printf '%s\n' "Refusing to modify a checkout with uncommitted changes: $TARGET"
    exit 1
  fi
  git fetch origin
  git switch "$BRANCH" 2>/dev/null || git switch -c "$BRANCH" --track "origin/$BRANCH"
  git pull --ff-only origin "$BRANCH"
else
  say "Cloning myAI into $TARGET"
  mkdir -p "$(dirname "$TARGET")"
  git clone --branch "$BRANCH" "$REPO_URL" "$TARGET"
  cd "$TARGET"
fi

if ! command -v uv >/dev/null 2>&1; then
  say "Installing uv Python tooling"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if ! command -v uv >/dev/null 2>&1; then
  printf '%s\n' "uv installed but is not available on PATH yet. Open a new Terminal and rerun this command."
  exit 1
fi

say "Installing Python 3.12 and project dependencies"
uv python install 3.12
uv venv --python 3.12 .venv
uv pip install -e '.[dev]'

if [ ! -f .env ] || ! grep -q '^ANTHROPIC_API_KEY=' .env; then
  printf '\nPaste your Anthropic API key (input is hidden): '
  IFS= read -r -s ANTHROPIC_API_KEY
  printf '\n'
  if [ -z "$ANTHROPIC_API_KEY" ]; then
    printf '%s\n' "No key entered; setup stopped without writing .env."
    exit 1
  fi
  umask 077
  printf 'ANTHROPIC_API_KEY=%s\n' "$ANTHROPIC_API_KEY" > .env
  unset ANTHROPIC_API_KEY
  chmod 600 .env
fi

if ! git check-ignore -q .env; then
  printf '%s\n' "Safety check failed: .env is not ignored by git. Remove it before continuing."
  exit 1
fi

say "Verifying local installation"
uv run myai inspect northstar

printf '\nSetup complete.\n'
printf 'Project: %s\n' "$TARGET"
printf 'Branch:  %s\n' "$BRANCH"
printf '%s\n' "Anthropic key: stored locally in .env with restricted permissions; not committed to git."
printf '\nNext time: cd "%s"\n' "$TARGET"
