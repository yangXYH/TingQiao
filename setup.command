#!/bin/bash
cd -- "$(dirname "$0")" || exit 1
bash ./setup.sh
result=$?
if [[ $result -ne 0 ]]; then
  echo "Setup failed. See the message above and README.md."
  read -r -p "Press Enter to close..." _
fi
exit "$result"
