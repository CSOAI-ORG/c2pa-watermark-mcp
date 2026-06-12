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

## Features

- **3 MCP tools** — `sign_asset`, `verify_asset`, `status`
- **EU AI Act Article 50 ready** — auto-injects `c2pa.ai_generated` assertion
- **Pure-stdlib fallback** — works without c2pa-python's native deps
- **HMAC-SHA256 signatures** — tamper-evident manifests
- **Optional X.509 chain** — via `c2pa-python[evm]` extra
- **Vercel-deployable** — see `c2pa-watermark-vercel` sibling repo

## Tools

| Tool | Purpose | Tier |
|------|---------|------|
| `sign_asset` | Embed a C2PA manifest into an asset, HMAC-signed | Pro |
| `verify_asset` | Verify a manifest against its asset bytes | Free |
| `status` | Report server health + native SDK availability | Free |

## install

```bash
# Core (HMAC fallback, no native deps)
pip install c2pa-watermark-mcp

# With full c2pa-python (X.509 chain)
pip install 'c2pa-watermark-mcp[c2pa]'

# For local development
git clone https://github.com/CSOAI-ORG/c2pa-watermark-mcp
cd c2pa-watermark-mcp
pip install -e .[dev]
```

## usage

### Sign an asset (Pro tier)

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

### Run as MCP server (stdio)

```bash
c2pa-watermark-mcp
# or with full c2pa-python
pip install 'c2pa-watermark-mcp[c2pa]'
c2pa-watermark-mcp
```

### Run via Docker

```bash
docker build -t c2pa-watermark-mcp .
docker compose up -d
# status endpoint on http://localhost:8000
```

## Deployment to Vercel

See the companion repo [c2pa-watermark-vercel](https://github.com/CSOAI-ORG/c2pa-watermark-vercel)
for a serverless wrapper exposing `/sign`, `/verify`, `/status` routes.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                c2pa-watermark-mcp                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ sign_asset  │  │verify_asset │  │   status    │         │
│  │  (HMAC +    │  │  (HMAC +    │  │ (health +   │         │
│  │   c2pa.io)  │  │   tamper)   │  │  capability)│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                  │
│         └────────────────┴────────────────┘                  │
│                          │                                   │
│                   ┌──────┴──────┐                           │
│                   │ HMAC-SHA256 │  (always available)       │
│                   │ + c2pa.io  │   (if c2pa-python installed)│
│                   └──────┬──────┘                           │
│                          │                                   │
│  ┌─────────────┐  ┌──────┴──────┐  ┌─────────────┐         │
│  │  manifest   │  │  signing   │  │  AI-Act     │         │
│  │  generator  │  │   keys     │  │ assertions  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Why we auto-inject `c2pa.ai_generated`

The C2PA spec defines this as the standard way to disclose AI-generated
content. EU AI Act Article 50 says AI content must be "machine-readable
and detectable as AI-generated" — the spec's answer is exactly this
assertion. Skipping the auto-inject would be a compliance violation waiting
to happen.

## FAQ

**Q: Does this need c2pa-python?**
A: No. The pure-stdlib HMAC-SHA256 fallback is fully functional for
tamper-evident manifests. Install c2pa-python only if you need the full
X.509 chain.

**Q: Can I sign an asset that's not a PNG/JPEG?**
A: Yes. The `asset_mime` parameter is just metadata; the HMAC is over
the bytes themselves. Works for video, audio, PDFs, etc.

**Q: How do I rotate the signing key?**
A: Generate a new key, deploy with both `OLD_KEY` and `NEW_KEY`, re-sign
all manifests with `NEW_KEY`, then drop `OLD_KEY` after expiry. This
package supports key rotation via the `signing_key` constructor arg.

**Q: Is this production-ready?**
A: Yes for tamper-evidence (HMAC). For full X.509 C2PA chain + cryptographic
non-repudiation, install c2pa-python ≥ 0.9.0.

## License

MIT © MEOK AI Labs / CSOAI-ORG
