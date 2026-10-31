#!/bin/bash
cd -- "$(dirname "$0")" || exit 1
if [[ ! -x .venv/bin/python ]]; then
  echo "Run setup.command or bash setup.sh first."
  read -r -p "Press Enter to close..." _
  exit 1
fi
.venv/bin/python app/launch.pyw
result=$?
if [[ $result -ne 0 ]]; then
  echo "TingQiao could not start. See logs/server-error.log."
  read -r -p "Press Enter to close..." _
fi
exit "$result"
