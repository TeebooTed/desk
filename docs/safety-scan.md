# Safety scan

`build.py` runs `tools/desk_scan.py` on every build. If anything blocks, `index.html` is **not written** (exit 2).

Blocks: API keys and tokens (GitHub, OpenAI-style, Slack, AWS, private keys, bearer tokens, webhook URLs with keys),
email addresses, dollar amounts, non-loopback IPv4 addresses, and (optional) cross-area leaks.
Warnings only: area names showing up in another area's cards.

- `tools/scan_allow.json`: values that are fine to show (keep it short; only things already public).
- `tools/scan_orgs.json` (optional, git-ignored; start from `scan_orgs.example.json`): per-area markers. `hard`
  (domains, server names, mailboxes) blocks when it appears in a different area; `soft` (names) warns.

Run it by hand on any file: `python3 tools/desk_scan.py index.html`.
`sh tools/test_scan.sh` checks that planted fake secrets stop a build.
