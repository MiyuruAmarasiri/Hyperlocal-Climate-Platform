"""Utility to launch API, dashboard, and web servers on available ports."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]


def _maybe_reexec_with_venv() -> None:
    if os.environ.get("VIRTUAL_ENV") or os.environ.get("RUN_DEV_STACK_BOOTSTRAPPED"):
        return

    venv_path = ROOT / ".venv"
    if not venv_path.exists():
        return

    candidate = venv_path / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
    if candidate.exists():
        env = os.environ.copy()
        env["RUN_DEV_STACK_BOOTSTRAPPED"] = "1"
        subprocess.check_call([str(candidate), str(Path(__file__).resolve())], env=env)
        sys.exit(0)


def _augment_env(extra: Dict[str, str] | None = None) -> Dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{ROOT}{os.pathsep}{existing}" if existing else str(ROOT)
    if extra:
        env.update(extra)
    return env


def _port_available(port: int, host: str = "127.0.0.1") -> bool:
    addresses = []
    if host in {"0.0.0.0", "::", ""}:
        addresses.extend([(socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")])
    else:
        family = socket.AF_INET6 if ":" in host else socket.AF_INET
        addresses.append((family, host))

    for family, addr in addresses:
        with socket.socket(family, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.25)
            try:
                result = sock.connect_ex((addr, port))
            except OSError:
                continue
            if result == 0:
                return False
    return True


def _find_free_port(start_port: int, host: str = "127.0.0.1", span: int = 100) -> int:
    for offset in range(span):
        candidate = start_port + offset
        if _port_available(candidate, host):
            return candidate
    raise RuntimeError(f"No free port found in range {start_port}-{start_port + span}")




def _resolve_access_hosts(host: str) -> List[str]:
    if host not in {"0.0.0.0", "::", ""}:
        return [host]
    hosts = ["127.0.0.1"]
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            hosts.append(s.getsockname()[0])
    except OSError:
        pass
    return list(dict.fromkeys(hosts))


def _format_access_urls(host: str, port: int, protocol: str = "http") -> List[str]:
    return [f"{protocol}://{resolved}:{port}" for resolved in _resolve_access_hosts(host)]

def _launch_process(cmd: Iterable[str], env: Dict[str, str], cwd: Path | None = None) -> subprocess.Popen[str]:
    return subprocess.Popen(list(cmd), env=env, cwd=str(cwd) if cwd else None)


def _launch_next_dev(host: str, port: int) -> subprocess.Popen[str]:
    env = _augment_env({"PORT": str(port), "HOST": host})
    bin_dir = ROOT / "web" / "node_modules" / ".bin"
    if os.name == "nt":
        candidate = bin_dir / "next.cmd"
    else:
        candidate = bin_dir / "next"

    if candidate.exists():
        cmd = [str(candidate), "dev", "--hostname", host, "--port", str(port)]
    else:
        if os.name == "nt":
            cmd = ["cmd", "/c", "npx", "next", "dev", "--hostname", host, "--port", str(port)]
        else:
            cmd = ["npx", "next", "dev", "--hostname", host, "--port", str(port)]

    return _launch_process(cmd, env=env, cwd=ROOT / "web")


def main() -> None:
    _maybe_reexec_with_venv()

    api_host = os.getenv("API_HOST", "0.0.0.0")
    dash_host = os.getenv("DASH_HOST", api_host)
    mobile_host = os.getenv("MOBILE_HOST", api_host)
    web_host = os.getenv("WEB_HOST", api_host)
    desired_api_port = int(os.getenv("API_PORT", "8000"))
    desired_dash_port = int(os.getenv("DASH_PORT", "8050"))
    desired_mobile_port = int(os.getenv("MOBILE_PORT", "8100"))
    desired_web_port = int(os.getenv("WEB_PORT", "3000"))
    enable_mobile = os.getenv("ENABLE_MOBILE", "true").lower() != "false"
    enable_web = os.getenv("ENABLE_WEB", "true").lower() != "false"

    api_port = _find_free_port(desired_api_port, host=api_host)
    dash_port = _find_free_port(desired_dash_port, host=dash_host)

    print(f"Starting API on http://{api_host}:{api_port}")
    for url in _format_access_urls(api_host, api_port):
        print(f"  -> {url}")
    api_proc = _launch_process(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "api.main:app",
            "--reload",
            "--host",
            api_host,
            "--port",
            str(api_port),
        ],
        env=_augment_env({"API_PORT": str(api_port), "API_HOST": api_host}),
        cwd=ROOT,
    )

    print(f"Starting dashboard on http://{dash_host}:{dash_port}")
    for url in _format_access_urls(dash_host, dash_port):
        print(f"  -> {url}")
    dash_proc = _launch_process(
        [sys.executable, "-m", "dashboard.app"],
        env=_augment_env({"DASH_PORT": str(dash_port), "DASH_HOST": dash_host}),
        cwd=ROOT,
    )

    processes: List[Tuple[str, subprocess.Popen[str]]] = [
        ("API", api_proc),
        ("Dashboard", dash_proc),
    ]

    if enable_mobile:
        mobile_port = (
            _find_free_port(desired_mobile_port, host=mobile_host)
        )
        print(f"Starting mobile PWA server on http://{mobile_host}:{mobile_port}")
        for url in _format_access_urls(mobile_host, mobile_port):
            print(f"  -> {url}")
        mobile_proc = _launch_process(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "mobile_app.main:app",
                "--reload",
                "--host",
                mobile_host,
                "--port",
                str(mobile_port),
            ],
            env=_augment_env({"MOBILE_HOST": mobile_host, "MOBILE_PORT": str(mobile_port)}),
            cwd=ROOT,
        )
        processes.append(("Mobile", mobile_proc))

    if enable_web:
        web_port = _find_free_port(desired_web_port, host=web_host)
        attempts = 0
        while attempts < 5:
            print(f"Starting Next.js web app on http://{web_host}:{web_port}")
            for url in _format_access_urls(web_host, web_port):
                print(f"  -> {url}")
            web_proc = _launch_next_dev(web_host, web_port)
            processes.append(("Next.js", web_proc))
            time.sleep(5)
            if web_proc.poll() is None and not _port_available(web_port, web_host):
                break
            print(f"Next.js failed to start on port {web_port}, trying another port...")
            processes.pop()
            attempts += 1
            web_port = _find_free_port(web_port + 1, host=web_host)
        else:
            raise RuntimeError("Next.js process failed to start after multiple attempts")

    try:
        while True:
            time.sleep(1)
            for name, proc in processes:
                if proc.poll() is not None:
                    raise RuntimeError(f"{name} process exited with code {proc.returncode}")
    except KeyboardInterrupt:
        print("Shutting down development stack...")
    finally:
        for name, proc in processes:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"Forcing {name} process to close")
                    proc.kill()


if __name__ == "__main__":
    main()
