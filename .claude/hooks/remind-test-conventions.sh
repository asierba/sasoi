#!/usr/bin/env bash
set -euo pipefail

changed_paths=$(jq -r '
  .tool_input.file_path?,
  .tool_response.filePath?,
  (.tool_response | .. | .changedFiles? // empty | .[])
  | strings
')

if ! grep -q '/tests/' <<<"$changed_paths"; then
  exit 0
fi

conventions=$(awk '
  FNR == 1 { sub(/^# Testing: /, ""); title = $0 }
  /^## / { in_convention = ($0 == "## Convention"); next }
  in_convention && NF { print "- " title ": " $0 }
' "$CLAUDE_PROJECT_DIR"/docs/testing/*.md)

jq -n --arg conventions "$conventions" '{
  hookSpecificOutput: {
    hookEventName: "PostToolUse",
    additionalContext: ("You changed a test. Check it follows these conventions and fix it before moving on (full examples in docs/testing/):\n" + $conventions)
  }
}'
