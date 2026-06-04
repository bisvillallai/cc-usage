#!/usr/bin/env bash
input=$(cat)

# Persist state for the Claude Code menu bar widget
echo "$input" > ~/.claude/.menubar-state.json

# Silent mode: if this flag file exists, only feed the menu bar (no terminal status line)
if [ -f ~/.claude/.cc-usage-silent ]; then
  exit 0
fi

cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
model=$(echo "$input" | jq -r '.model.display_name // ""')
used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

# Directory: basename of cwd
dir=$(basename "$cwd")

# Git branch (skip lock to avoid interference)
branch=""
if git -C "$cwd" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  branch=$(git -C "$cwd" symbolic-ref --short HEAD 2>/dev/null || git -C "$cwd" rev-parse --short HEAD 2>/dev/null)
fi

# Context usage
ctx_part=""
if [ -n "$used" ]; then
  ctx_part=" ctx:$(printf '%.0f' "$used")%"
fi

# Rate limits
five=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
rate_part=""
if [ -n "$five" ]; then
  rate_part=" 5h:$(printf '%.0f' "$five")%"
fi

# Assemble
dir_part="\033[38;5;67m${dir}\033[0m"
if [ -n "$branch" ]; then
  vcs_part=" \033[38;5;144m${branch}\033[0m"
else
  vcs_part=""
fi
model_part="\033[38;5;180m${model}\033[0m"

printf '%b' "${dir_part}${vcs_part}  ${model_part}\033[38;5;223m${ctx_part}${rate_part}\033[0m"
