#!/usr/bin/env python3
import os
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime
from scipy.ndimage import gaussian_filter1d

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Connect to the SQLite database
conn = sqlite3.connect(os.path.join(base_dir, "scripts/stats.db"))
cursor = conn.cursor()
cursor.execute(f"""
    SELECT timestamp, player_count
    FROM stats
    WHERE timestamp > {datetime.now().timestamp() - 60 * 60 * 24 * 7}
    ORDER BY timestamp
""")
data = cursor.fetchall()
conn.close()

# Prepare data for plotting
timestamps = [datetime.fromtimestamp(ts) for ts, _ in data]
player_counts = [count for _, count in data]

# Convert to pandas DataFrame for easier handling
df = pd.DataFrame({"Timestamp": timestamps, "Player Count": player_counts})

# Calculate moving average
window_size = 60  # Adjust as needed
df["Moving Average"] = df["Player Count"].rolling(window=window_size).mean()

# Calculate quartiles without smoothing
df["Min"] = df["Player Count"].rolling(window=window_size).min()
df["Max"] = df["Player Count"].rolling(window=window_size).max()

# Trim DataFrame to remove NaN values
df = df.dropna()

# Apply Gaussian smoothing to quartiles
sigma = 50  # Adjust the sigma value for desired smoothness
df["Smoothed Min"] = gaussian_filter1d(df["Min"], sigma=sigma)
df["Smoothed Max"] = gaussian_filter1d(df["Max"], sigma=sigma)

# Create a plot
plt.style.use("ggplot")
plt.rcParams.update({"font.size": 18})  # Adjust the number to your preference
plt.figure(figsize=(12, 7))
plt.fill_between(df["Timestamp"], df["Smoothed Min"], df["Smoothed Max"], color="blue", alpha=0.5, label="Hourly Range")

# Formatting the plot
plt.ylabel("Player Count")
plt.legend()
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
plt.grid(False)
plt.gcf().autofmt_xdate()  # Rotate date labels

# Save the plot
plt.savefig(os.path.join(base_dir, "plugins/dynmap/web/player_count.png"), transparent=True)
