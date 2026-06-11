"""Tests for c2pa-watermark-mcp — sign/verify + tamper + EU AI Act assertion."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from c2pa_watermark_mcp import sign_asset, verify_asset, status


KEY = b"test-signing-key-32-bytes-long-aaaaaa"


def fake_image(seed: int = 0) -> bytes:
    return (f"fake-png-bytes-{seed}").encode() * 100  # ~2KB


def test_status_reports_no_native_by_default():
    s = status()
    assert s["server"] == "c2pa-watermark-mcp"
    assert s["eu_ai_act_article_50_ready"] is True
    assert "sign_asset" in s["tools"]
    print(f"  ✓ status(): c2pa_python_available={s['c2pa_python_available']}")


def test_sign_asset_emits_manifest_id():
    asset = fake_image(1)
    r = sign_asset(asset, "image/png", "MEOK-SDXL/1.0", KEY)
    assert r["manifest_id"].startswith("MEOK-C2PA-")
    assert r["asset_hash"]  # 64 hex chars
    assert r["manifest"]["asset"]["hash"] == r["asset_hash"]
    print(f"  ✓ manifest_id={r['manifest_id']}")


def test_sign_includes_ai_generated_assertion_by_default():
    asset = fake_image(2)
    r = sign_asset(asset, "image/png", "MEOK/1.0", KEY)
    assertions = r["manifest"]["assertions"]
    ai_gen = [a for a in assertions if a.get("label") == "c2pa.ai_generated"]
    assert len(ai_gen) == 1
    assert ai_gen[0]["value"]["type"] == "trainedAlgorithmicMedia"
    print("  ✓ c2pa.ai_generated assertion auto-injected")


def test_sign_respects_explicit_ai_generated_false():
    asset = fake_image(3)
    r = sign_asset(asset, "image/png", "MEOK/1.0", KEY, ai_generated=False)
    ai_gen = [a for a in r["manifest"]["assertions"] if a.get("label") == "c2pa.ai_generated"]
    assert len(ai_gen) == 0
    print("  ✓ ai_generated=False skips assertion")


def test_sign_respects_explicit_assertion_override():
    asset = fake_image(4)
    r = sign_asset(
        asset, "image/png", "MEOK/1.0", KEY,
        assertions=[{"label": "c2pa.ai_generated", "value": {"type": "humanEdited", "confidence": 1.0}}],
    )
    ai_gen = [a for a in r["manifest"]["assertions"] if a.get("label") == "c2pa.ai_generated"]
    assert len(ai_gen) == 1  # not duplicated
    assert ai_gen[0]["value"]["type"] == "humanEdited"  # user's value preserved
    print("  ✓ explicit assertion preserved, no duplicate")


def test_sign_includes_custom_assertions():
    asset = fake_image(5)
    r = sign_asset(
        asset, "image/png", "MEOK/1.0", KEY,
        assertions=[
            {"label": "c2pa.training", "value": {"model": "sdxl-1.0"}},
            {"label": "stds.iptc", "value": {"creator": "test"}},
        ],
    )
    labels = [a["label"] for a in r["manifest"]["assertions"]]
    assert "c2pa.training" in labels
    assert "stds.iptc" in labels
    # ai_generated also added
    assert "c2pa.ai_generated" in labels
    print("  ✓ custom assertions preserved + ai_generated added")


def test_verify_valid_asset():
    asset = fake_image(6)
    r = sign_asset(asset, "image/png", "MEOK/1.0", KEY)
    verdict = verify_asset(asset, r["manifest"], KEY)
    assert verdict["valid"] is True
    assert verdict["reasons"] == []
    print("  ✓ valid asset verifies clean")


def test_verify_detects_tampered_asset():
    asset = fake_image(7)
    r = sign_asset(asset, "image/png", "MEOK/1.0", KEY)
    # Tamper with the asset
    tampered = asset + b"extra-bytes"
    verdict = verify_asset(tampered, r["manifest"], KEY)
    assert verdict["valid"] is False
    assert any("hash mismatch" in reason for reason in verdict["reasons"])
    print("  ✓ tampered asset detected")


def test_verify_detects_tampered_manifest():
    asset = fake_image(8)
    r = sign_asset(asset, "image/png", "MEOK/1.0", KEY)
    # Tamper with a claim in the manifest
    r["manifest"]["claim_generator"] = "EVIL-FORGE/9.9"
    verdict = verify_asset(asset, r["manifest"], KEY)
    assert verdict["valid"] is False
    assert any("tampered" in reason or "mismatch" in reason for reason in verdict["reasons"])
    print("  ✓ tampered manifest detected")


def test_verify_wrong_signing_key():
    asset = fake_image(9)
    r = sign_asset(asset, "image/png", "MEOK/1.0", KEY)
    verdict = verify_asset(asset, r["manifest"], b"different-key")
    assert verdict["valid"] is False
    print("  ✓ wrong signing key rejected")


def test_verify_missing_ai_generated_assertion():
    """Article 50 compliance check."""
    asset = fake_image(10)
    r = sign_asset(asset, "image/png", "MEOK/1.0", KEY, ai_generated=False)
    # Remove any other assertions too
    r["manifest"]["assertions"] = []
    verdict = verify_asset(asset, r["manifest"], KEY)
    assert verdict["valid"] is False
    assert any("Article 50" in reason for reason in verdict["reasons"])
    print("  ✓ missing Article 50 assertion flagged")


def test_verify_manifest_without_signature():
    asset = fake_image(11)
    manifest = {
        "@context": "https://c2pa.org/specifications/v2.0/context.jsonld",
        "claim_generator": "MEOK/1.0",
        "created_at": "2026-06-11T16:00:00+00:00",
        "asset": {"mime": "image/png", "hash": "abc", "alg": "sha256"},
        "assertions": [{"label": "c2pa.ai_generated", "value": {"type": "trainedAlgorithmicMedia"}}],
    }
    verdict = verify_asset(asset, manifest, KEY)
    assert verdict["valid"] is False
    assert any("no signature" in reason for reason in verdict["reasons"])
    print("  ✓ unsigned manifest rejected")


def test_full_workflow_with_ingredients():
    asset = fake_image(12)
    r = sign_asset(
        asset, "image/png", "MEOK/1.0", KEY,
        ingredients=[{"url": "training-data-v1", "hash": "deadbeef" * 8, "alg": "sha256"}],
    )
    assert len(r["manifest"]["ingredients"]) == 1
    verdict = verify_asset(asset, r["manifest"], KEY)
    assert verdict["valid"] is True
    print("  ✓ full workflow with ingredients passes")


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"✓ {t.__name__}")
        except AssertionError as e:
            print(f"✗ {t.__name__}: {e}")
            failed += 1
    if failed:
        print(f"\n{failed} test(s) FAILED")
        sys.exit(1)
    print(f"\n✅ All {len(tests)} tests passed")
