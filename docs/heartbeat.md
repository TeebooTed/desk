# Optional heartbeat (macOS example)

`heartbeat/desk-heartbeat.py` is a tiny, read-only reporter for one Mac. Every 5 minutes it writes
`~/Desk/heartbeat.json` with the time, uptime, disk use, load, power source, which local ports are listening,
the status of launchd jobs you list, and the last line of logs you name. It runs no commands that change anything,
opens no network ports and sends nothing anywhere.

You do not need it: without a heartbeat the Machines panel still shows online state from your bot's machine list.

## Set up

1. Copy `heartbeat/` to `~/Desk/heartbeat/` and `config.example.json` to `config.json`. Edit the device name,
   ports, job labels and log paths.
2. Edit `com.example.desk-heartbeat.plist`: replace `YOU` with your macOS user name (and the label if you like).
3. Install it:

```sh
cp heartbeat/com.example.desk-heartbeat.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.desk-heartbeat.plist
```

4. Get `heartbeat.json` to where Desk is built (`data/heartbeat_<name>.json`), for example by asking your bot to copy
   it during its refresh, and set `"heartbeat": "data/heartbeat_<name>.json"` on that machine in
   `data/machines_config.json`. The card then shows "Heartbeat 2 min ago · up 6 d · load 1.2".

Remove: `launchctl bootout gui/$(id -u)/com.example.desk-heartbeat` and delete the plist.
