"""Read and validate configuration only when a tool needs a connection."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import Literal

from dotenv.parser import parse_stream


class ConfigurationError(ValueError):
    """A sanitized, actionable configuration failure."""


def load_environment(env_file: Path | None = None) -> None:
    """Load one local file at startup, without searching or replacing exported values."""
    path = Path.cwd() / ".env" if env_file is None else env_file
    try:
        with path.open(encoding="utf-8") as source:
            content = source.read()
    except FileNotFoundError:
        if env_file is None:
            return
        raise ConfigurationError(
            "The requested --env-file does not exist. Create it or correct the path."
        ) from None
    except (OSError, UnicodeError, ValueError):
        raise ConfigurationError(
            "Cannot read the environment file. Check file permissions and UTF-8 encoding."
        ) from None

    # Validate before loading: dotenv otherwise skips malformed lines with a warning,
    # and environment assignment could fail after partially applying the file.
    values: dict[str, str | None] = {}
    for binding in parse_stream(StringIO(content)):
        if (
            binding.error
            or (binding.key is not None and ("\x00" in binding.key or "=" in binding.key))
            or (binding.value is not None and "\x00" in binding.value)
        ):
            raise ConfigurationError(
                "Invalid environment file syntax. Check KEY=value entries and balanced quotes."
            )
        if binding.key is not None:
            values[binding.key] = binding.value
    for key, value in values.items():
        if value is not None:
            os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    host: str
    database: str
    user: str
    password: str = field(repr=False)
    port: int = 5439
    timeout: int = 10
    auth_mode: Literal["password", "iam"] = "password"
    region: str | None = None
    cluster_identifier: str | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        """Validate environment values without echoing them in errors."""
        values = os.environ if env is None else env
        mode = values.get("REDSHIFT_AUTH_MODE", "password").strip()
        if mode not in ("password", "iam"):
            raise ConfigurationError("REDSHIFT_AUTH_MODE must be password or iam.")
        required = ["REDSHIFT_HOST", "REDSHIFT_DATABASE", "REDSHIFT_USER"]
        required += (
            ["AWS_REGION", "REDSHIFT_CLUSTER_IDENTIFIER"]
            if mode == "iam"
            else ["REDSHIFT_PASSWORD"]
        )
        missing = [name for name in required if not values.get(name, "").strip()]
        if missing:
            raise ConfigurationError(
                "Missing environment settings: "
                + ", ".join(missing)
                + ". Set them in the server's local .env and restart, or export them into "
                "the server process; see README Configuration. "
                "For IAM, set REDSHIFT_AUTH_MODE=iam and use the AWS credential provider chain."
            )
        host = values["REDSHIFT_HOST"].strip()
        if (
            len(host) > 253
            or any(
                char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-"
                for char in host
            )
            or host.startswith((".", "-"))
            or host.endswith((".", "-"))
        ):
            raise ConfigurationError("REDSHIFT_HOST must be a DNS hostname, not a URL.")
        return cls(
            host=host,
            database=values["REDSHIFT_DATABASE"].strip(),
            user=values["REDSHIFT_USER"].strip(),
            password=values.get("REDSHIFT_PASSWORD", "") if mode == "password" else "",
            port=_integer(values, "REDSHIFT_PORT", 5439, 1, 65535),
            timeout=_integer(values, "REDSHIFT_CONNECT_TIMEOUT", 10, 1, 60),
            auth_mode=mode,
            region=values.get("AWS_REGION") if mode == "iam" else None,
            cluster_identifier=values.get("REDSHIFT_CLUSTER_IDENTIFIER") if mode == "iam" else None,
        )


def _integer(values: Mapping[str, str], name: str, default: int, low: int, high: int) -> int:
    try:
        result = int(values.get(name, str(default)))
    except ValueError:
        raise ConfigurationError(f"{name} must be an integer between {low} and {high}.") from None
    if not low <= result <= high:
        raise ConfigurationError(f"{name} must be between {low} and {high}.")
    return result
