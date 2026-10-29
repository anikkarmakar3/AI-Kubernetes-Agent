from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

from loguru import logger

from core.config import settings


@dataclass
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    @property
    def error(self) -> str | None:
        if self.ok:
            return None
        message = self.stderr.strip() or self.stdout.strip() or "kubectl command failed"
        return message[-1000:]

    def json(self) -> dict | list | None:
        if not self.ok:
            return None
        try:
            return json.loads(self.stdout)
        except json.JSONDecodeError:
            return None


class KubectlExecutor:
    def __init__(self, context: str | None = None):
        self.context = context

    def run(self, args: list[str], timeout: float | None = None) -> CommandResult:
        command = ["kubectl"]
        if self.context:
            command.extend(["--context", self.context])
        if settings.kubeconfig_path:
            command.extend(["--kubeconfig", settings.kubeconfig_path])
        if settings.kubeconfig_server_host:
            server = self._server_address()
            if server:
                parsed = urlsplit(server)
                port = f":{parsed.port}" if parsed.port else ""
                command.append(f"--server={urlunsplit((parsed.scheme, f'{settings.kubeconfig_server_host}{port}', parsed.path, parsed.query, parsed.fragment))}")
                if settings.kubectl_insecure_skip_tls_verify:
                    command.append("--insecure-skip-tls-verify=true")
        command.extend(args)
        logger.debug("Running kubectl command: {}", " ".join(command[:4] + (["..."] if len(command) > 4 else [])))
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout or settings.kubectl_timeout_seconds, check=False)
            result = CommandResult(command, completed.returncode, completed.stdout, completed.stderr)
        except FileNotFoundError:
            result = CommandResult(command, 127, stderr="kubectl is not installed or is not on PATH")
        except subprocess.TimeoutExpired:
            result = CommandResult(command, 124, stderr="kubectl command timed out")
        except OSError as exc:
            result = CommandResult(command, 1, stderr=str(exc))
        if not result.ok:
            logger.warning("kubectl failed: {}", result.error)
        return result

    def _server_address(self) -> str | None:
        command = ["kubectl"]
        if self.context:
            command.extend(["--context", self.context])
        if settings.kubeconfig_path:
            command.extend(["--kubeconfig", settings.kubeconfig_path])
        command.extend(["config", "view", "--raw", "--minify", "-o", "jsonpath={.clusters[0].cluster.server}"])
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=5, check=False)
        except OSError:
            return None
        return result.stdout.strip() if result.returncode == 0 else None

    def json(self, args: list[str]) -> tuple[dict | list | None, str | None]:
        result = self.run([*args, "-o", "json"])
        return result.json(), result.error


def list_contexts() -> tuple[list[dict[str, object]], str | None]:
    executor = KubectlExecutor()
    result = executor.run(["config", "get-contexts", "-o", "name"])
    if not result.ok:
        return [], result.error
    current_result = executor.run(["config", "current-context"])
    current = current_result.stdout.strip()
    contexts = [{"name": name.strip(), "current": name.strip() == current} for name in result.stdout.splitlines() if name.strip()]
    return contexts, None
