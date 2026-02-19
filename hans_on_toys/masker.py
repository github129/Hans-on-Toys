"""
個人情報（PII）検出・マスキングモジュール

Tesseract OCR でテキスト領域を検出し、正規表現パターンに一致した箇所を
塗りつぶしてマスクする。
"""
import re
from collections import defaultdict
from typing import NamedTuple

from PIL import Image, ImageDraw

# ─── PII パターン定義 ─────────────────────────────────────────────────────────

_BUILTIN_PATTERNS: dict[str, re.Pattern] = {
    "email": re.compile(
        r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
        re.IGNORECASE,
    ),
    "phone_jp": re.compile(
        r"0\d{1,4}[\-\u2010\u2011\s]?\d{1,4}[\-\u2010\u2011\s]?\d{3,4}"
    ),
    "phone_intl": re.compile(
        r"\+\d{1,3}[\-\s]?\(?\d{1,4}\)?[\-\s]?\d{3,4}[\-\s]?\d{3,4}"
    ),
    "postal_code_jp": re.compile(r"〒?\s*\d{3}[\-－]\d{4}"),
    "credit_card": re.compile(
        r"\b\d{4}[\-\s]?\d{4}[\-\s]?\d{4}[\-\s]?\d{4}\b"
    ),
}

# 設定ダイアログで表示するラベル（key の順序が UI に反映される）
PATTERN_LABELS: dict[str, str] = {
    "email":          "メールアドレス  (user@example.com)",
    "phone_jp":       "電話番号（日本）  (090-xxxx-xxxx)",
    "phone_intl":     "電話番号（国際）  (+1-xxx-xxx-xxxx)",
    "postal_code_jp": "郵便番号  (〒123-4567)",
    "credit_card":    "クレジットカード番号  (xxxx-xxxx-xxxx-xxxx)",
}


class MaskResult(NamedTuple):
    image: Image.Image
    count: int          # マスクした PII の件数
    error: str | None   # エラーメッセージ（正常時は None）


# ─── 公開関数 ─────────────────────────────────────────────────────────────────

def mask_pii(image: Image.Image, cfg: dict) -> MaskResult:
    """
    画像内の個人情報を OCR で検出してマスクした画像を返す。

    - Tesseract / pytesseract が利用できない場合は error に理由を設定して返す。
    - アクティブなパターンが 0 件なら元画像のコピーをそのまま返す。
    """
    try:
        import pytesseract
    except ImportError:
        return MaskResult(
            image.copy(), 0,
            "pytesseract がインストールされていません。\n"
            "pip install pytesseract でインストールしてください。",
        )

    tesseract_cmd = cfg.get("tesseract_cmd", "").strip()
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    # アクティブパターンを収集
    active_patterns = _collect_patterns(cfg.get("masking", {}))
    if not active_patterns:
        return MaskResult(image.copy(), 0, None)

    # OCR 実行
    try:
        data = _run_ocr(pytesseract, image)
    except Exception as exc:
        return MaskResult(
            image.copy(), 0,
            f"Tesseract OCR の実行に失敗しました。\n"
            f"Tesseract がインストールされているか確認してください。\n({exc})",
        )

    # マスク描画
    mask_color = cfg.get("mask_color", "#000000")
    result = image.copy()
    draw = ImageDraw.Draw(result)
    count = 0

    for line_words in _group_by_line(data).values():
        count += _mask_line(line_words, active_patterns, draw, mask_color)

    return MaskResult(result, count, None)


# ─── 内部ヘルパー ─────────────────────────────────────────────────────────────

def _collect_patterns(masking_cfg: dict) -> list[re.Pattern]:
    patterns: list[re.Pattern] = []
    for key, pattern in _BUILTIN_PATTERNS.items():
        if masking_cfg.get(key, False):
            patterns.append(pattern)
    for raw in masking_cfg.get("custom_patterns", []):
        try:
            patterns.append(re.compile(raw, re.IGNORECASE))
        except re.error:
            pass
    return patterns


def _run_ocr(pytesseract, image: Image.Image) -> dict:
    """
    eng（標準インストールで常に利用可能）→ jpn+eng（日本語データがある場合）
    の順に OCR を試みる。

    PII パターン（メール・電話番号・クレジットカード番号）はすべて ASCII 文字で
    構成されているため、日本語（jpn）データなしでも正確に検出できる。
    Tesseract の英語のみのインストールで問題なく動作する。
    """
    last_exc: Exception | None = None
    for lang in ("eng", "jpn+eng"):
        try:
            return pytesseract.image_to_data(
                image,
                lang=lang,
                output_type=pytesseract.Output.DICT,
            )
        except Exception as exc:
            last_exc = exc
    raise last_exc  # type: ignore[misc]


def _group_by_line(data: dict) -> dict[tuple, list[dict]]:
    """OCR データを (page, block, par, line) のキーでグループ化する。"""
    lines: dict = defaultdict(list)
    for i in range(len(data["text"])):
        if int(data["conf"][i]) < 0:    # -1 は非テキストブロック
            continue
        word = data["text"][i]
        if not word.strip():
            continue
        key = (
            data["page_num"][i],
            data["block_num"][i],
            data["par_num"][i],
            data["line_num"][i],
        )
        lines[key].append({
            "text":   word,
            "left":   data["left"][i],
            "top":    data["top"][i],
            "right":  data["left"][i] + data["width"][i],
            "bottom": data["top"][i] + data["height"][i],
        })
    return lines


def _mask_line(
    words: list[dict],
    patterns: list[re.Pattern],
    draw: ImageDraw.ImageDraw,
    color: str,
) -> int:
    """
    1 行分の単語リストを受け取り、PII にマッチした部分のバウンディングボックスを
    マスクする。戻り値はマスクした件数。

    単語をスペースで連結して行テキストを復元し、文字インデックスから
    どの単語に対応するかをマップすることで、複数単語にまたがるパターン
    （例: "090 1234 5678"）も正確に検出できる。
    """
    if not words:
        return 0

    line_text = ""
    char_to_word: list[int | None] = []
    for wi, w in enumerate(words):
        if line_text:
            char_to_word.append(None)   # スペース区切り文字
            line_text += " "
        for _ in w["text"]:
            char_to_word.append(wi)
        line_text += w["text"]

    count = 0
    for pattern in patterns:
        for m in pattern.finditer(line_text):
            matched_wi = {
                char_to_word[ci]
                for ci in range(m.start(), min(m.end(), len(char_to_word)))
                if char_to_word[ci] is not None
            }
            if not matched_wi:
                continue
            boxes = [words[wi] for wi in matched_wi]
            x1 = min(b["left"]   for b in boxes) - 2
            y1 = min(b["top"]    for b in boxes) - 2
            x2 = max(b["right"]  for b in boxes) + 2
            y2 = max(b["bottom"] for b in boxes) + 2
            draw.rectangle([x1, y1, x2, y2], fill=color)
            count += 1

    return count
