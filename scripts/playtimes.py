import os
import gzip
import re
import json
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta

def log_file_lines(directory):
    sorted_files = sorted(os.listdir(directory))
    for filename in sorted_files:
        if filename == 'latest.log':
            date_str = datetime.now().strftime('%Y-%m-%d')
            with open(os.path.join(directory, filename), 'r', encoding='utf-8') as f:
                for line in f.readlines():
                    yield date_str, line
        elif filename.endswith('.log.gz'):
            date_str = filename.split('-')[0:3]
            date_str = '-'.join(date_str)
            with gzip.open(os.path.join(directory, filename), 'rt', encoding='utf-8') as f:
                for line in f.readlines():
                    yield date_str, line

JOIN_LEAVE_PATTERN = re.compile(r'\[(\d{2}:\d{2}:\d{2})\] \[Server thread/INFO\]: (.+) (joined|left) the game')

def extract_events_from_logs(lines):    
    for date_str, line in lines:
        join_leave_match = JOIN_LEAVE_PATTERN.search(line)
        if not join_leave_match:
            continue

        time_str = join_leave_match.group(1)
        player = join_leave_match.group(2)
        action = join_leave_match.group(3)

        event_time = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M:%S')

        yield event_time, player, action

def calculate_play_time(events):
    play_time = defaultdict(timedelta)
    active_sessions = {}
    
    for event_time, player, action in events:
        if action == 'joined':
            active_sessions[player] = event_time
        elif action == 'left' and player in active_sessions:
            join_time = active_sessions.pop(player)
            delta = event_time - join_time
            play_time[player] += delta
    
    return play_time

def format_uuid(uuid):
    return f"{uuid[0:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:32]}"

def fetch_uuid(username, uuid_cache):
    if username.startswith("."):
        return None

    if username in uuid_cache:
        return uuid_cache[username]

    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    time.sleep(0.5)
    try:
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                return None

            data = json.loads(response.read().decode())
            unformatted_uuid = data.get("id")
            if not unformatted_uuid:
                return None

            formatted_uuid = format_uuid(unformatted_uuid)
            uuid_cache[username] = formatted_uuid
            return formatted_uuid

    except Exception as e:
        print(f"Error fetching UUID for {username}: {e}")
    return None

def load_hexnicks(base_dir):
    hexnicks_path = os.path.join(base_dir, 'plugins/HexNicks/nicknames.json')
    if os.path.exists(hexnicks_path):
        with open(hexnicks_path, 'r') as file:
            return json.load(file)
    return {}

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lines = log_file_lines(os.path.join(base_dir, 'logs'))
    events = extract_events_from_logs(lines)

    hexnicks = load_hexnicks(base_dir)
    uuid_cache = {}

    play_time = defaultdict(timedelta)
    active_sessions = {}

    for event_time, player, action in events:
        uuid = fetch_uuid(player, uuid_cache)
        nickname_info = hexnicks.get(uuid, None)
        name = nickname_info.get("text", player) if nickname_info else player

        if action == 'joined':
            active_sessions[name] = event_time
        elif action == 'left' and name in active_sessions:
            join_time = active_sessions.pop(name)
            delta = event_time - join_time
            play_time[name] += delta

    sorted_play_time = sorted(play_time.items(), key=lambda x: x[1], reverse=True)
    
    with open(os.path.join(base_dir, 'plugins/dynmap/web/playtimes.html'), 'w') as f:
        print("""
            <!doctype html>
            <html>
                <head>
                    <title>Playtimes</title>
                    <style>
                        body {
                            font-family: sans-serif;
                            font-size: 2rem;
                            background-color: #f3f4f6;
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                        }
                        img {
                            width: 100%;
                            max-width: 50rem;
                            margin: 3rem auto;
                            padding: 2rem 0;
                            background-color: white;
                            border-radius: 0.5rem;
                            box-shadow: rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0.1) 0px 4px 6px -1px, rgba(0, 0, 0, 0.1) 0px 2px 4px -2px;
                        }
                        table {
                            border-collapse: collapse;
                            width: 100%;
                            max-width: 50rem;
                            margin: 3rem auto;
                            overflow: hidden;
                            border-radius: 0.5rem;
                            background-color: white;
                            box-shadow: rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0.1) 0px 4px 6px -1px, rgba(0, 0, 0, 0.1) 0px 2px 4px -2px;
                        }
                        th {
                            background-color: #3b82f6;
                            color: white;
                            padding: 1rem 2rem;
                            text-align: left;
                        }
                        td {
                            border-bottom: 1px solid #e2e4e8;
                            padding: 1rem 2rem;
                        }
                        span.duration {
                            color: #586069;
                            font-family: monospace;
                        }
                        div.footer {
                            max-width: 50rem;
                            width: 100%;
                            margin: 3rem auto;
                            text-align: center;
                        }
                    </style>
                    <link rel="icon" type="image/png" sizes="16x16" href="images/icons/favicon-16x16.png" />
                    <link rel="icon" type="image/png" sizes="32x32" href="images/icons/favicon-32x32.png" />
                    <link rel="apple-touch-icon" sizes="180x180" href="images/icons/apple-touch-icon.png" />
                </head>
                <body>
                    <img src="player_count.png" />
                    <table>
                        <thead>
                            <tr>
                                <th>Player</th>
                                <th>Playtime (Last 30 Days)</th>
                            </tr>
                        </thead>
                        <tbody>""", file=f)
        for player, time in sorted_play_time:
            print(f"""
                            <tr>
                                <td>{player}</td>
                                <td><span class="duration">{time}</span></td>
                            </tr>""", file=f)
        print(f"""
                        </tbody>
                    </table>
                    <div class="footer">
                        Last updated: {datetime.now().strftime('%Y/%m/%d %H:%M:%S EST')}
                    </div>
                </body>
            </html>""", file=f)

if __name__ == '__main__':
    main()
