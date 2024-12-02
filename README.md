### SystemD Unit

```ini
[Unit]
Description=Minecraft Server
After=network.target

[Service]
User=minecraft
Type=forking
ExecStart=/usr/bin/tmux new-session -d -s minecraft -c /home/minecraft/minecraft /home/minecraft/minecraft/scripts/start.sh
ExecStop=/home/minecraft/minecraft/scripts/stop.sh
NotifyAccess=all
Restart=always

[Install]
WantedBy=multi-user.target
```
