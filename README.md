# 🛠️ System Health & Maintenance Script (Python)

A lightweight Python tool that generates detailed system health reports on Linux machines.  
It gathers useful metrics such as CPU load, memory usage, disk utilization, running processes, network info, and failed systemd services.  
Reports are automatically saved inside a `logs/` directory and old ones can be cleaned up automatically based on your configuration.

This project is a simple example of Linux automation + Python scripting and can be scheduled with cron for periodic reports.

---

## 🚀 Features

- Collects key system information:
  - Hostname, OS, kernel version, uptime  
  - CPU load + top CPU-intensive processes  
  - Memory usage  
  - Disk usage  
  - Top memory-hungry processes  
  - Network interfaces + active connections  
  - Failed systemd services (if available)

- Generates timestamped log files  
- Automatically removes older reports based on retention settings  
- Configurable through `config.env`  
- Works with cron for automated scheduling  

---

## 📁 Project Structure

```

system-health-automation/
├── system_health.py
├── config.env
├── logs/
└── README.md

````

---

## ⚡ Quick Start

```bash
# Clone and setup
git clone https://github.com/yassinomri/system-health-automation.git
cd system-health-automation

# Run once
python3 system_health.py

# Check the generated report
cat logs/system_health_*.log
```

## ⚙️ Configuration

The script reads settings from **config.env**:

```bash
LOG_DIR="./logs"
LOG_RETENTION_DAYS=7
TOP_PROCESSES_COUNT=5
````

* **LOG_DIR** – Where generated reports will be saved
* **LOG_RETENTION_DAYS** – Number of days to keep old logs
* **TOP_PROCESSES_COUNT** – Number of top CPU/memory processes to include

---

## ▶️ How to Run

Make the script executable:

```bash
chmod +x system_health.py
```

Run it manually:

```bash
./system_health.py
```

or:

```bash
python3 system_health.py
```

---

## 📋 Sample Output

```
=== SYSTEM HEALTH REPORT ===
Generated: 2026-05-10 14:23:45

🖥️  SYSTEM INFO
Hostname: server-01
OS: Ubuntu 22.04 LTS
Kernel: 5.15.0-105-generic
Uptime: 45 days, 3 hours

💻 CPU
Load Average: 0.45, 0.38, 0.42
Top Processes:
  - python3 (12.5%)
  - node (8.3%)
  ...
```

## 🛡️ Error Handling

- Script gracefully handles missing systemd on systems that don't have it
- Logs are created even if some metrics fail to collect
- Configuration file is optional (uses defaults if missing)

## 🕒 Optional: Automate with Cron

To run the script automatically (e.g., every hour):

```bash
crontab -e
```

Add this line:

```bash
0 * * * * /usr/bin/python3 /full/path/to/system_health.py >> /full/path/to/cron.log 2>&1
```

This will generate a new report every hour.

---

## 🧹 Log Cleanup

Old log files are automatically deleted based on the number of retention days set in `config.env`.

Example:
Set `LOG_RETENTION_DAYS=3` → only keep the last 3 days of reports.

---

## 💡 Use Cases

- **Server Monitoring**: Run hourly on production servers
- **Troubleshooting**: Quick health snapshot when performance degrades
- **Capacity Planning**: Track trends over time
- **Automation Learning**: Study how to work with system calls in Python


## 📦 Requirements

This script uses only Python’s standard library.
No external packages are required.

---

## 📝 Notes

* Built for Linux systems
* Works on both systemd and non-systemd environments
* Ideal for learning Linux automation, system monitoring, and Python scripting
