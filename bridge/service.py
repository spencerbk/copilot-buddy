"""Service manager for the copilot-buddy bridge daemon.

Installs/uninstalls the bridge as an OS-managed background service
that starts automatically at user login.

Usage::

    python -m bridge.service install [--port COM3] [-v] ...
    python -m bridge.service uninstall
    python -m bridge.service status
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
import textwrap

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SERVICE_NAME = "copilot-buddy-bridge"
_LOG_DIR = pathlib.Path.home() / ".copilot-buddy"
_DEFAULT_LOG_FILE = _LOG_DIR / "bridge.log"


def _repo_root() -> pathlib.Path:
    """Return the repository root (parent of bridge/)."""
    return pathlib.Path(__file__).resolve().parent.parent


def _launcher_cmd() -> pathlib.Path:
    """Return the path to the Windows .cmd launcher script."""
    return _repo_root() / "scripts" / "copilot-buddy-bridge.cmd"


def _launcher_sh() -> pathlib.Path:
    """Return the path to the Unix .sh launcher script."""
    return _repo_root() / "scripts" / "copilot-buddy-bridge.sh"


# ===================================================================
# Windows — Task Scheduler
# ===================================================================


def _windows_install(daemon_args: list[str]) -> bool:
    args_str = " ".join(daemon_args)
    launcher = _launcher_cmd()
    if not launcher.exists():
        print(f"ERROR: Launcher script not found: {launcher}", file=sys.stderr)
        return False

    # Ensure log directory exists
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    cmd_line = f'"{launcher}" --log-file "{_DEFAULT_LOG_FILE}" {args_str}'.strip()

    # Create a scheduled task that runs at user logon, hidden
    result = subprocess.run(
        [
            "schtasks", "/Create",
            "/TN", _SERVICE_NAME,
            "/TR", cmd_line,
            "/SC", "ONLOGON",
            "/RL", "LIMITED",
            "/F",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: schtasks /Create failed:\n{result.stderr}", file=sys.stderr)
        return False
    print(f"Scheduled task '{_SERVICE_NAME}' created (runs at logon).")

    # Start immediately
    run_result = subprocess.run(
        ["schtasks", "/Run", "/TN", _SERVICE_NAME],
        capture_output=True,
        text=True,
    )
    if run_result.returncode == 0:
        print("Bridge daemon started.")
    else:
        print(f"Note: Could not start immediately: {run_result.stderr.strip()}")

    print(f"Log file: {_DEFAULT_LOG_FILE}")
    return True


def _windows_uninstall() -> bool:
    # End the task first (best-effort)
    subprocess.run(
        ["schtasks", "/End", "/TN", _SERVICE_NAME],
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        ["schtasks", "/Delete", "/TN", _SERVICE_NAME, "/F"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: schtasks /Delete failed:\n{result.stderr}", file=sys.stderr)
        return False
    print(f"Scheduled task '{_SERVICE_NAME}' removed.")
    return True


def _windows_status() -> None:
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", _SERVICE_NAME, "/FO", "LIST", "/V"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Service '{_SERVICE_NAME}' is not installed.")
        return
    # Extract key fields
    for line in result.stdout.splitlines():
        line_stripped = line.strip()
        if any(
            line_stripped.startswith(prefix)
            for prefix in ("Task Name:", "Status:", "Last Run Time:", "Last Result:", "Task To Run:")
        ):
            print(line_stripped)
    print(f"Log file: {_DEFAULT_LOG_FILE}")


# ===================================================================
# macOS — launchd
# ===================================================================

_PLIST_LABEL = "com.copilot-buddy.bridge"
_PLIST_DIR = pathlib.Path.home() / "Library" / "LaunchAgents"


def _macos_install(daemon_args: list[str]) -> bool:
    launcher = _launcher_sh()
    if not launcher.exists():
        print(f"ERROR: Launcher script not found: {launcher}", file=sys.stderr)
        return False

    # Ensure launcher is executable
    launcher.chmod(0o755)

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    _PLIST_DIR.mkdir(parents=True, exist_ok=True)

    program_args = [str(launcher), "--log-file", str(_DEFAULT_LOG_FILE)] + daemon_args

    # Build plist XML
    args_xml = "\n".join(f"        <string>{a}</string>" for a in program_args)
    plist_content = textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
          "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>{_PLIST_LABEL}</string>
            <key>ProgramArguments</key>
            <array>
        {args_xml}
            </array>
            <key>WorkingDirectory</key>
            <string>{_repo_root()}</string>
            <key>RunAtLoad</key>
            <true/>
            <key>KeepAlive</key>
            <true/>
            <key>StandardOutPath</key>
            <string>{_DEFAULT_LOG_FILE}</string>
            <key>StandardErrorPath</key>
            <string>{_DEFAULT_LOG_FILE}</string>
        </dict>
        </plist>
    """)

    plist_path = _PLIST_DIR / f"{_PLIST_LABEL}.plist"
    plist_path.write_text(plist_content, encoding="utf-8")

    # Load the agent
    subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
    result = subprocess.run(
        ["launchctl", "load", str(plist_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: launchctl load failed:\n{result.stderr}", file=sys.stderr)
        return False

    print(f"Launch agent '{_PLIST_LABEL}' installed and started.")
    print(f"Log file: {_DEFAULT_LOG_FILE}")
    return True


def _macos_uninstall() -> bool:
    plist_path = _PLIST_DIR / f"{_PLIST_LABEL}.plist"
    if plist_path.exists():
        subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
        plist_path.unlink()
    print(f"Launch agent '{_PLIST_LABEL}' removed.")
    return True


def _macos_status() -> None:
    plist_path = _PLIST_DIR / f"{_PLIST_LABEL}.plist"
    if not plist_path.exists():
        print(f"Service '{_PLIST_LABEL}' is not installed.")
        return
    result = subprocess.run(
        ["launchctl", "list", _PLIST_LABEL],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"Service '{_PLIST_LABEL}' is installed and running.")
        print(result.stdout.strip())
    else:
        print(f"Service '{_PLIST_LABEL}' is installed but not currently running.")
    print(f"Log file: {_DEFAULT_LOG_FILE}")


# ===================================================================
# Linux — systemd user service
# ===================================================================

_SYSTEMD_UNIT = "copilot-buddy-bridge.service"
_SYSTEMD_DIR = pathlib.Path.home() / ".config" / "systemd" / "user"


def _linux_install(daemon_args: list[str]) -> bool:
    launcher = _launcher_sh()
    if not launcher.exists():
        print(f"ERROR: Launcher script not found: {launcher}", file=sys.stderr)
        return False

    # Ensure launcher is executable
    launcher.chmod(0o755)

    if not shutil.which("systemctl"):
        print("ERROR: systemctl not found — systemd is required", file=sys.stderr)
        return False

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    _SYSTEMD_DIR.mkdir(parents=True, exist_ok=True)

    extra_args = " ".join(
        ["--log-file", str(_DEFAULT_LOG_FILE)] + daemon_args
    )
    unit_content = textwrap.dedent(f"""\
        [Unit]
        Description=copilot-buddy bridge daemon
        After=default.target

        [Service]
        Type=simple
        ExecStart={launcher} {extra_args}
        WorkingDirectory={_repo_root()}
        Restart=on-failure
        RestartSec=10

        [Install]
        WantedBy=default.target
    """)

    unit_path = _SYSTEMD_DIR / _SYSTEMD_UNIT
    unit_path.write_text(unit_content, encoding="utf-8")

    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    result = subprocess.run(
        ["systemctl", "--user", "enable", "--now", _SYSTEMD_UNIT],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: systemctl enable failed:\n{result.stderr}", file=sys.stderr)
        return False

    print(f"Systemd user service '{_SYSTEMD_UNIT}' installed and started.")
    print(f"Log file: {_DEFAULT_LOG_FILE}")
    return True


def _linux_uninstall() -> bool:
    unit_path = _SYSTEMD_DIR / _SYSTEMD_UNIT
    subprocess.run(
        ["systemctl", "--user", "disable", "--now", _SYSTEMD_UNIT],
        capture_output=True,
    )
    if unit_path.exists():
        unit_path.unlink()
    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    print(f"Systemd user service '{_SYSTEMD_UNIT}' removed.")
    return True


def _linux_status() -> None:
    unit_path = _SYSTEMD_DIR / _SYSTEMD_UNIT
    if not unit_path.exists():
        print(f"Service '{_SYSTEMD_UNIT}' is not installed.")
        return
    result = subprocess.run(
        ["systemctl", "--user", "status", _SYSTEMD_UNIT],
        capture_output=True,
        text=True,
    )
    print(result.stdout.strip() if result.stdout else "Service status unavailable.")
    print(f"Log file: {_DEFAULT_LOG_FILE}")


# ===================================================================
# Dispatcher
# ===================================================================


def _detect_platform() -> str:
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m bridge.service",
        description="Install/uninstall the copilot-buddy bridge as an auto-start service.",
    )
    parser.add_argument(
        "action",
        choices=["install", "uninstall", "status"],
        help="Action to perform",
    )
    # Capture remaining args as daemon passthrough
    args, daemon_args = parser.parse_known_args(argv)

    platform = _detect_platform()

    if args.action == "install":
        print(f"Installing for {platform}...")
        dispatch = {
            "windows": _windows_install,
            "macos": _macos_install,
            "linux": _linux_install,
        }
        ok = dispatch[platform](daemon_args)
        sys.exit(0 if ok else 1)

    elif args.action == "uninstall":
        dispatch_u = {
            "windows": _windows_uninstall,
            "macos": _macos_uninstall,
            "linux": _linux_uninstall,
        }
        ok = dispatch_u[platform]()
        sys.exit(0 if ok else 1)

    elif args.action == "status":
        dispatch_s = {
            "windows": _windows_status,
            "macos": _macos_status,
            "linux": _linux_status,
        }
        dispatch_s[platform]()


if __name__ == "__main__":
    main()
