# Changelog

## 2026-10-27

### Added
- **Org (area) filter**: chips above Projects, shift-click to combine, saved per browser. Also filters Today,
  Waiting, approvals and header counts by each item's `area`. Colours by area position (`--org-1…4`). Optional
  `org_tips` and `cal_org` in status.json.
- **"As of" stamps** on every section, an overall header pill, "—" for missing numbers, and a `LIVE_STALE`
  marker when `live.json` is older than `live_stale_hours` (default 13).
- **Machines panel** (`machines` section): online/asleep/offline, last seen, disk thresholds, services, pinned
  notes, machine classes. `tools/machines_health.py` builds the data from `data/machines_config.json`;
  example files in `examples/machines/`.
- **Command palette** (⌘K / Ctrl+K) across projects, agents, machines and actions.
- **Alerts banner** with snooze (4 hours or until 8 AM tomorrow).
- **Refresh history** inside Routines (last runs and which files each one updated).
- **Approval cards**: Approve / Edit / Decline send `[Desk approval] <id> <answer>` to your bot. Desk never posts.
- **Teammate badges**: how recently each agent logged progress.
- **Optional heartbeat** example for macOS (`heartbeat/`, read-only, launchd every 5 min). See `docs/heartbeat.md`.
- **Safety scan** (`tools/desk_scan.py`): the build stops and writes nothing if it finds secrets, emails, dollar
  amounts, IPs or cross-area leaks. See `docs/safety-scan.md`.
- Icons for the new panels in `icons/` (inlined at build time).
- Tests: `tools/test_features.py` (Playwright, example data) and `tools/test_scan.sh`.

### Changed
- `build.py` inlines `custom/*.css|js` and `icons/*.svg`, adds the machines and run-history data, and runs the scan.
- `layout.default.json` / `layout_lib.py`: new `machines` section.
- `install.sh` copies `custom/`, `icons/`, `examples/machines/` and the scan config.
- `.gitignore`: `data/`, `LIVE_STALE`, `heartbeat/config.json`, `tools/scan_orgs.json`, refresh backups.
