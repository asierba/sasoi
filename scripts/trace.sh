#!/usr/bin/env bash
set -euo pipefail

trace_file="${1:-$(ls -t traces/*.jsonl | head -1)}"
echo "Following $trace_file" >&2

tail -n +1 -f "$trace_file" | jq --unbuffered -r '
  def block:
    if .type == "text" then .text | gsub("\n"; "\n     ")
    elif .type == "tool_use" then .name
    elif .type == "thinking" then "💭"
    else .type
    end;

  if .type == "session" then
    "● session model=\(.model) max_tokens=\(.max_tokens)"
  elif .type == "tool_call" then
    "• 🔧 \(.name) \(.input | tojson) → \(.result) [\(.duration_ms | round)ms]"
  else
    (.messages[-1] | if .role == "user" and (.content | type) == "string" then "\n→ 🧑 \(.content)\n" else "" end) +
    if .error then
      "← 🤖 ✗ \(.error) [\(.duration_ms | round)ms]"
    else
      "← 🤖 \(.stop_reason) [\(.duration_ms | round)ms]: " + (.content | map(block) | join(" | "))
    end
  end'
