# c2pa-watermark-mcp

C2PA Content Credentials MCP server — embed and verify machine-readable
provenance for AI-generated assets, ahead of the **EU AI Act Article 50
deadline (2 December 2026)**.

## Why this exists

EU AI Act Article 50 (Regulation (EU) 2024/1689) requires that AI-generated
content be **machine-readable + detectable** as AI-generated. The
`c2pa.ai_generated` assertion is the C2PA spec's mandated way to do that.

The deadline is **2 December 2026** — about 6 months out. Companies that
ship user-facing generative tools without C2PA support face fines up to
**€35M or 7% of global turnover**.

This MCP wraps the official [`c2pa-python`](https://github.com/contentauth/c2pa-python)
SDK (≥0.9.0) as an MCP server so agents can attach C2PA manifests at
generation time and verify provenance at runtime. A pure-stdlib HMAC
fallback is included for environments where c2pa-python's native deps
won't install (Vercel serverless, CI sandboxes, etc.).

## Tools

| Tool | Purpose |
|------|---------|
| `sign_asset` | Embed a C2PA manifest into an asset, HMAC-signed |
| `verify_asset` | Verify a manifest against its asset bytes |
| `status` | Report server health + native SDK availability |

## Install

```bash
# Core (HMAC fallback)
pip install c2pa-watermark-mcp

# For full X.509 C2PA chain
pip install c2pa-python>=0.9.0
```

## Usage

```python
from c2pa_watermark_mcp import sign_asset, verify_asset, status

# Server health
print(status())
# → {'server': 'c2pa-watermark-mcp', 'c2pa_python_available': False, ...}

# Sign an asset
with open("output.png", "rb") as f:
    asset = f.read()
key = b"my-hmac-key-32-bytes-long-aaaaaa"
result = sign_asset(
    asset_bytes=asset,
    asset_mime="image/png",
    claim_generator="MEOK-SDXL/1.0",
    signing_key=key,
    ai_generated=True,
    assertions=[
        {"label": "c2pa.training", "value": {"model": "sdxl-1.0", "dataset": "internal"}},
    ],
)
print(result["manifest_id"])

# Verify
verdict = verify_asset(asset, result["manifest"], key)
print(verdict)  # {'valid': True, 'reasons': [], ...}
```

## MCP Server

```bash
# stdio
c2pa-watermark-mcp

# With full c2pa-python
pip install 'c2pa-watermark-mcp[c2pa]'
c2pa-watermark-mcp
```

## License

MIT © MEOK AI Labs / CSOAI-ORG
