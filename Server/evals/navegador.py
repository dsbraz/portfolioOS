"""Gives the evaluated agent a browser that is already signed in.

## Why this exists

The skills are browser-first: they navigate the interface with the operator's
own session. An evaluation without a browser can only observe the agent
*refusing* to proceed — which is a real signal, but not the flows the
acceptance script cares about.

It cannot be solved by handing the agent a password. The skills forbid asking
for or typing one, and an evaluation that pushed the agent to break that rule
would be measuring the wrong thing. So the session is planted **before** the
agent starts: log in through the API, write the token into a Playwright
`storageState`, and start the browser from it. The agent opens the app already
authenticated, exactly like a person who left their browser logged in.

## Why it all runs in containers

The browser lives in the e2e stack's Playwright image, which already carries
the matching browsers, and it reaches the app at `http://client:4200` over the
compose network. Nothing is published to the host, nothing is installed on it,
and the evaluation still cannot touch the development database.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PROJETO = RAIZ.parent

#: Inside the compose network. The agent's browser is a container too, so it
#: uses the service name — the host never needs a published port.
APP = "http://client:4200"

OPERADOR = {"username": "e2e", "password": "e2e-password-123"}

_COMPOSE = ["docker", "compose", "-f", "docker-compose.e2e.yml"]


def _token_do_operador() -> str:
    """Signs in through the API, from inside the network."""
    corpo = json.dumps(OPERADOR)
    saida = subprocess.run(
        [
            *_COMPOSE, "exec", "-T", "client", "sh", "-c",
            f"wget -qO- --post-data='{corpo}' "
            "--header='Content-Type: application/json' "
            "http://server:8000/api/auth/login",
        ],
        cwd=PROJETO, capture_output=True, text=True, check=True,
    )
    return json.loads(saida.stdout.strip().splitlines()[-1])["access_token"]


def estado_autenticado(destino: Path) -> Path:
    """Writes a Playwright storageState carrying a live session.

    The key must match `TOKEN_KEY` in `services/auth.service.ts`; a rename there
    silently produces an anonymous browser, and the evaluation would then
    measure the login wall instead of the skill.
    """
    estado = {
        "cookies": [],
        "origins": [
            {
                "origin": APP,
                "localStorage": [
                    {"name": "access_token", "value": _token_do_operador()}
                ],
            }
        ],
    }
    arquivo = destino / "sessao.json"
    arquivo.write_text(json.dumps(estado), encoding="utf-8")
    return arquivo


def configuracao_mcp(destino: Path, sessao_no_container: str) -> Path:
    """MCP config that starts a headless browser from the planted session.

    `--isolated` keeps every run on a fresh profile seeded only by the storage
    state, so one evaluation never inherits another's cookies or history.
    """
    configuracao = {
        "mcpServers": {
            "navegador": {
                "command": "docker",
                "args": [
                    # Absolute path: the MCP server is spawned from the agent's
                    # own cwd (the throwaway workspace), where a relative
                    # compose path resolves to nothing and the server dies
                    # before it registers a single tool. That failure is
                    # silent — the agent just sees no browser.
                    "compose", "-f", str(PROJETO / "docker-compose.e2e.yml"),
                    "run", "--rm", "-T",
                    "-v", f"{destino}:/sessao",
                    "e2e",
                    # Pré-instalado na imagem e fixado à versão dos browsers dela.
                    "npx", "@playwright/mcp",
                    "--headless",
                    # The exact binary baked into the image. Channel names are
                    # a moving target — this MCP's default resolved to branded
                    # Chrome at /opt/google/chrome, then to chrome-for-testing,
                    # depending on what existed. A pinned path cannot be
                    # re-resolved into the wrong browser.
                    "--executable-path",
                    "/ms-playwright/chromium-1232/chrome-linux/chrome",
                    "--isolated",
                    "--storage-state", sessao_no_container,
                ],
            }
        }
    }
    arquivo = destino / "mcp.json"
    arquivo.write_text(json.dumps(configuracao, indent=2), encoding="utf-8")
    return arquivo
