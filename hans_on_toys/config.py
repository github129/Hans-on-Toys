"""設定管理モジュール — ~/.hans_on_toys/config.json に保存"""
import copy
import json
from pathlib import Path
from typing import Any

_CONFIG_DIR = Path.home() / ".hans_on_toys"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

# デフォルト設定
_DEFAULTS: dict[str, Any] = {
    "masking": {
        "email": True,
        "phone_jp": True,
        "phone_intl": False,
        "postal_code_jp": False,
        "credit_card": True,
        "custom_patterns": [],
    },
    "mask_color": "#000000",
    "tesseract_cmd": "",  # 空文字 = PATH から自動検索
}


def load() -> dict[str, Any]:
    """設定を読み込む。ファイルがなければデフォルト値を返す。"""
    if not _CONFIG_FILE.exists():
        return copy.deepcopy(_DEFAULTS)
    try:
        with _CONFIG_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
        merged = copy.deepcopy(_DEFAULTS)
        _deep_merge(merged, data)
        return merged
    except (json.JSONDecodeError, OSError):
        return copy.deepcopy(_DEFAULTS)


def save(cfg: dict[str, Any]) -> None:
    """設定をファイルに書き込む。"""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with _CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def _deep_merge(base: dict, override: dict) -> None:
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
