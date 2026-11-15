"""Validate both indexes offline before publication."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
mmrl = json.loads((root / "json/modules.json").read_text(encoding="utf-8"))
ksu = json.loads((root / "ksu/modules.json").read_text(encoding="utf-8"))
assert isinstance(mmrl.get("metadata", {}).get("timestamp"), (int, float))
assert isinstance(mmrl.get("modules"), list) and mmrl["modules"]
assert isinstance(ksu, list)
for module in mmrl["modules"]:
    for key in ("id", "name", "version", "versionCode", "author", "track", "versions"):
        assert key in module, (module.get("id"), key)
    assert isinstance(module["versionCode"], int)
    assert module["track"].get("type") == "GIT"
    assert module["versions"]
    for v in module["versions"]:
        for key in ("version", "versionCode", "timestamp", "zipUrl"):
            assert key in v, (module["id"], key)
        assert v["zipUrl"].startswith("https://github.com/") and v["zipUrl"].endswith(".zip")
        assert isinstance(v["timestamp"], (float, int))
for module in ksu:
    assert all(module.get(k) for k in ("name", "description", "author", "repoUrl"))
    assert module["repoUrl"].startswith("https://github.com/")
print("Validated modules: MMRL", len(mmrl["modules"]), "KernelSU Next", len(ksu))
