"""stdio MCP server entry point for c2pa-watermark-mcp.

Run with: `python -m c2pa_watermark_mcp.server` or `c2pa-watermark-mcp`.

This is a minimal stdio wrapper. For a full MCP server with the Model
Context Protocol, use the `mcp` package (optional) — falls back to a
plain CLI REPL if mcp is not installed.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

from c2pa_watermark_mcp import sign_asset, status, verify_asset


# Default key from env (32 bytes). Dev only.
SIGNING_KEY = os.environ.get("MEOK_C2PA_KEY", "").encode("utf-8") or b"dev-hmac-key-do-not-use-in-prod-aaaa"


def serve() -> None:
    """Run the stdio MCP server.

    Protocol: one JSON line per request on stdin, one JSON line per
    response on stdout. Error responses use {"error": "..."}.
    """
    print(json.dumps(status()), file=sys.stdout, flush=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"invalid_json: {e}"}), file=sys.stdout, flush=True)
            continue

        try:
            resp = handle(req)
        except Exception as e:
            resp = {"error": str(e)}
        print(json.dumps(resp), file=sys.stdout, flush=True)


def handle(req: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a single request."""
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "tools/list":
        return {
            "tools": [
                {"name": "sign_asset", "description": "Sign an asset with a C2PA manifest"},
                {"name": "verify_asset", "description": "Verify a manifest against asset bytes"},
                {"name": "status", "description": "Server health + native SDK availability"},
            ]
        }

    if method == "status":
        return status()

    if method == "sign_asset":
        return sign_asset(
            asset_bytes=bytes.fromhex(params["asset_hex"]),
            asset_mime=params.get("asset_mime", "application/octet-stream"),
            claim_generator=params.get("claim_generator", "c2pa-watermark-mcp/0.1.0"),
            signing_key=SIGNING_KEY,
            ai_generated=params.get("ai_generated", True),
        )

    if method == "verify_asset":
        return verify_asset(
            asset_bytes=bytes.fromhex(params["asset_hex"]),
            manifest=params["manifest"],
            signing_key=SIGNING_KEY,
        )

    return {"error": f"unknown_method: {method}"}


if __name__ == "__main__":
    serve()
