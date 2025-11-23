# System Health & Maintenance Script (Python)

A simple **Linux system health report** and maintenance script written in Python.

It collects CPU, memory, disk, processes, network, and failed service information
and writes everything into timestamped log files in `logs/`. It can also
automatically clean up older reports.

## Usage

```bash
./system_health.py

## Automation (Optional)
You can automate this script using cron:

```bash
crontab -e
0 * * * * /usr/bin/python3 /path/to/system_health.py