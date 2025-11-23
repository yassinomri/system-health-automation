#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import shutil

CONFIG_FILE = "config.env"

# Default fallback values if config.env is missing or incomplete
DEFAULT_CONFIG = {
    "LOG_DIR": "./logs",
    "LOG_RETENTION_DAYS": "7",
    "TOP_PROCESSES_COUNT": "5",
}


def load_config(config_path: str) -> dict:
    """
    Load simple KEY=VALUE pairs from config.env.
    If the file is missing or contains invalid entries, defaults are used.
    """
    config = DEFAULT_CONFIG.copy()

    if not os.path.exists(config_path):
        print("[WARN] config.env not found, using default settings.")
        return cast_config_types(config)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if key in config:
                    config[key] = value
    except Exception as e:
        print(f"[WARN] Could not read config.env: {e}. Using defaults.")

    return cast_config_types(config)


def cast_config_types(config: dict) -> dict:
    """
    Convert config values from strings to the appropriate Python types.
    """
    cfg = config.copy()

    try:
        cfg["LOG_RETENTION_DAYS"] = int(cfg.get("LOG_RETENTION_DAYS", "7"))
    except ValueError:
        cfg["LOG_RETENTION_DAYS"] = 7

    try:
        cfg["TOP_PROCESSES_COUNT"] = int(cfg.get("TOP_PROCESSES_COUNT", "5"))
    except ValueError:
        cfg["TOP_PROCESSES_COUNT"] = 5

    return cfg


def safe_run_shell(command: str) -> str:
    """
    Run a command using bash -lc and return its output.
    This never raises an exception; errors are returned as text.
    """
    try:
        result = subprocess.run(
            ["bash", "-lc", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        out = (result.stdout or "").strip()
        if out:
            return out

        err = (result.stderr or "").strip()
        return err if err else ""

    except Exception as e:
        return f"[ERROR running '{command}']: {e}"


def safe_run(cmd_list: list[str]) -> str:
    """
    Run a command without using the shell and return its output safely.
    """
    try:
        result = subprocess.run(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        out = (result.stdout or "").strip()
        if out:
            return out

        err = (result.stderr or "").strip()
        return err if err else ""

    except Exception as e:
        return f"[ERROR running '{' '.join(cmd_list)}']: {e}"


def log_section(f, title: str) -> None:
    f.write(f"\n==================== {title} ====================\n\n")


def write_header(f) -> None:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f.write(f"System Health Report - {now_str}\n")
    f.write("----------------------------------------\n")


def collect_system_info(f) -> None:
    log_section(f, "System Information")

    hostname = safe_run(["hostname"])
    uptime = safe_run(["uptime", "-p"])
    kernel = safe_run(["uname", "-r"])

    # Try to detect OS name
    os_pretty = ""
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as osr:
            for line in osr:
                if line.startswith("PRETTY_NAME="):
                    os_pretty = line.split("=", 1)[1].strip().strip('"')
                    break
    except FileNotFoundError:
        os_pretty = "Unknown OS"

    f.write(f"Hostname: {hostname}\n")
    f.write(f"Uptime:   {uptime}\n")
    f.write(f"Kernel:   {kernel}\n")
    f.write(f"OS:       {os_pretty}\n")


def collect_cpu_load(f, top_processes_count: int) -> None:
    log_section(f, "CPU & Load")

    # /proc/loadavg contains load averages
    try:
        with open("/proc/loadavg", "r", encoding="utf-8") as lp:
            loadavg = " ".join(lp.read().split()[:3])
    except Exception as e:
        loadavg = f"[ERROR reading /proc/loadavg: {e}]"

    f.write(f"Load average (1, 5, 15 min): {loadavg}\n\n")
    f.write(f"Top {top_processes_count} processes by CPU:\n")

    cmd = f"ps -eo pid,comm,%cpu,%mem --sort=-%cpu | head -n {top_processes_count + 1}"
    f.write(safe_run_shell(cmd) + "\n")


def collect_memory(f) -> None:
    log_section(f, "Memory")
    f.write(safe_run(["free", "-h"]) + "\n")


def collect_disk_usage(f) -> None:
    log_section(f, "Disk Usage")
    f.write(safe_run(["df", "-h"]) + "\n")


def collect_top_memory_processes(f, top_processes_count: int) -> None:
    log_section(f, "Top Processes by Memory")

    cmd = f"ps -eo pid,comm,%cpu,%mem --sort=-%mem | head -n {top_processes_count + 1}"
    f.write(safe_run_shell(cmd) + "\n")


def collect_systemd_failed_services(f) -> None:
    # Skip this part if systemctl isn't available
    if shutil.which("systemctl") is None:
        return

    log_section(f, "Failed Systemd Services")
    f.write(safe_run(["systemctl", "--failed"]) + "\n")


def collect_network_info(f) -> None:
    log_section(f, "Network")

    # Basic interface info
    if shutil.which("ip"):
        f.write("Interfaces:\n")
        f.write(safe_run(["ip", "-brief", "address"]) + "\n\n")
    else:
        f.write("Command 'ip' not available.\n\n")

    f.write("Active connections:\n")
    if shutil.which("ss"):
        cmd = "ss -tulpn 2>/dev/null | head -n 20"
        f.write(safe_run_shell(cmd) + "\n")
    else:
        f.write("Command 'ss' not available.\n")


def cleanup_old_logs(f, log_dir: Path, retention_days: int) -> None:
    log_section(f, "Log Cleanup")

    f.write(f"Log retention: {retention_days} days\n")
    f.write("Old files removed:\n")

    if retention_days < 0:
        f.write("Invalid retention period. Skipping.\n")
        return

    cutoff = datetime.now() - timedelta(days=retention_days)
    deleted_any = False

    try:
        for file in log_dir.glob("system_report_*.log"):
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            if mtime < cutoff:
                f.write(f" - {file}\n")
                try:
                    file.unlink()
                except Exception as e:
                    f.write(f"   Could not delete {file}: {e}\n")
                deleted_any = True
    except Exception as e:
        f.write(f"Cleanup error: {e}\n")
        return

    if not deleted_any:
        f.write(" - None\n")


def main():
    config = load_config(CONFIG_FILE)

    log_dir = Path(config["LOG_DIR"])
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = log_dir / f"system_report_{timestamp}.log"

    print(f"[INFO] Generating system health report: {report_file}")

    try:
        with open(report_file, "w", encoding="utf-8") as f:
            write_header(f)

            # Each section is wrapped to avoid breaking the whole report
            try:
                collect_system_info(f)
            except Exception as e:
                f.write(f"[ERROR in System Information]: {e}\n")

            try:
                collect_cpu_load(f, config["TOP_PROCESSES_COUNT"])
            except Exception as e:
                f.write(f"[ERROR in CPU & Load]: {e}\n")

            try:
                collect_memory(f)
            except Exception as e:
                f.write(f"[ERROR in Memory]: {e}\n")

            try:
                collect_disk_usage(f)
            except Exception as e:
                f.write(f"[ERROR in Disk Usage]: {e}\n")

            try:
                collect_top_memory_processes(f, config["TOP_PROCESSES_COUNT"])
            except Exception as e:
                f.write(f"[ERROR in Top Processes by Memory]: {e}\n")

            try:
                collect_systemd_failed_services(f)
            except Exception as e:
                f.write(f"[ERROR in Failed Systemd Services]: {e}\n")

            try:
                collect_network_info(f)
            except Exception as e:
                f.write(f"[ERROR in Network]: {e}\n")

            try:
                cleanup_old_logs(f, log_dir, config["LOG_RETENTION_DAYS"])
            except Exception as e:
                f.write(f"[ERROR in Log Cleanup]: {e}\n")

        print(f"[INFO] Report generation finished: {report_file}")

    except Exception as e:
        print(f"[FATAL] Could not write report file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
