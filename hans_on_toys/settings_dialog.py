"""
個人情報マスク設定ダイアログ

使い方:
    # 親ウィンドウありでモーダル表示（watcher から呼ぶ場合）
    dlg = SettingsDialog(parent=tk_root)
    dlg.show()

    # スタンドアロン（単体テスト用）
    dlg = SettingsDialog()
    dlg.show_standalone()
"""
import re
import tkinter as tk
from tkinter import colorchooser, messagebox, ttk

from . import config as cfg
from .masker import PATTERN_LABELS


class SettingsDialog:
    """個人情報マスクの設定を変更するダイアログ。"""

    def __init__(self, parent: tk.Tk | None = None) -> None:
        self._cfg = cfg.load()
        self._standalone = parent is None
        if self._standalone:
            self._root: tk.Misc = tk.Tk()
        else:
            self._root = tk.Toplevel(parent)
        self._root.title("個人情報マスク設定")
        self._root.resizable(False, False)
        self._build_ui()

    # ─── UI 構築 ──────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = self._root
        root.configure(padx=16, pady=12)  # type: ignore[call-arg]

        # ── PII 種別チェックボックス ──────────────────────────────────────
        frame_pii = ttk.LabelFrame(root, text="マスクする個人情報の種類", padding=10)
        frame_pii.pack(fill="x", pady=(0, 10))

        self._pii_vars: dict[str, tk.BooleanVar] = {}
        masking_cfg = self._cfg["masking"]
        for key, label in PATTERN_LABELS.items():
            var = tk.BooleanVar(value=bool(masking_cfg.get(key, False)))
            self._pii_vars[key] = var
            ttk.Checkbutton(frame_pii, text=label, variable=var).pack(
                anchor="w", pady=2
            )

        # ── マスクの色 ────────────────────────────────────────────────────
        frame_color = ttk.LabelFrame(root, text="マスクの色", padding=10)
        frame_color.pack(fill="x", pady=(0, 10))

        self._mask_color: str = self._cfg.get("mask_color", "#000000")
        row_color = ttk.Frame(frame_color)
        row_color.pack(anchor="w")
        self._color_swatch = tk.Label(
            row_color, width=3, relief="sunken", bg=self._mask_color
        )
        self._color_swatch.pack(side="left", padx=(0, 8), ipady=4)
        ttk.Button(
            row_color, text="色を選択...", command=self._pick_color
        ).pack(side="left")

        # ── カスタム正規表現 ──────────────────────────────────────────────
        frame_custom = ttk.LabelFrame(
            root, text="カスタム正規表現パターン", padding=10
        )
        frame_custom.pack(fill="x", pady=(0, 10))

        ttk.Label(
            frame_custom,
            text="追加したいパターンを正規表現で記述してください",
            foreground="#666666",
        ).pack(anchor="w", pady=(0, 4))

        list_row = ttk.Frame(frame_custom)
        list_row.pack(fill="x")
        self._pattern_lb = tk.Listbox(list_row, height=4, selectmode="single")
        self._pattern_lb.pack(side="left", fill="x", expand=True)
        sb = ttk.Scrollbar(list_row, command=self._pattern_lb.yview)
        sb.pack(side="left", fill="y")
        self._pattern_lb.configure(yscrollcommand=sb.set)

        for p in masking_cfg.get("custom_patterns", []):
            self._pattern_lb.insert("end", p)

        entry_row = ttk.Frame(frame_custom)
        entry_row.pack(fill="x", pady=(4, 0))
        self._pattern_entry = ttk.Entry(entry_row)
        self._pattern_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._pattern_entry.bind("<Return>", lambda _: self._add_pattern())
        ttk.Button(
            entry_row, text="追加", command=self._add_pattern
        ).pack(side="left", padx=(0, 4))
        ttk.Button(
            entry_row, text="削除", command=self._remove_pattern
        ).pack(side="left")

        # ── Tesseract パス ────────────────────────────────────────────────
        frame_tess = ttk.LabelFrame(
            root,
            text="Tesseract OCR パス（省略時は PATH から自動検索）",
            padding=10,
        )
        frame_tess.pack(fill="x", pady=(0, 10))

        self._tesseract_var = tk.StringVar(
            value=self._cfg.get("tesseract_cmd", "")
        )
        ttk.Entry(
            frame_tess, textvariable=self._tesseract_var, width=52
        ).pack(fill="x")
        ttk.Label(
            frame_tess,
            text="例: C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
            foreground="#666666",
        ).pack(anchor="w", pady=(2, 0))

        # ── 保存 / キャンセル ─────────────────────────────────────────────
        btn_row = ttk.Frame(root)
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="保存", command=self._save).pack(
            side="right", padx=(4, 0)
        )
        ttk.Button(btn_row, text="キャンセル", command=self._root.destroy).pack(
            side="right"
        )

    # ─── イベントハンドラ ────────────────────────────────────────────────────

    def _pick_color(self) -> None:
        result = colorchooser.askcolor(
            color=self._mask_color,
            parent=self._root,
            title="マスクの色を選択",
        )
        if result and result[1]:
            self._mask_color = result[1]
            self._color_swatch.configure(bg=self._mask_color)

    def _add_pattern(self) -> None:
        raw = self._pattern_entry.get().strip()
        if not raw:
            return
        try:
            re.compile(raw)
        except re.error as exc:
            messagebox.showerror(
                "正規表現エラー",
                f"無効なパターンです:\n{exc}",
                parent=self._root,
            )
            return
        self._pattern_lb.insert("end", raw)
        self._pattern_entry.delete(0, "end")

    def _remove_pattern(self) -> None:
        sel = self._pattern_lb.curselection()
        if sel:
            self._pattern_lb.delete(sel[0])

    def _save(self) -> None:
        masking_cfg = self._cfg["masking"]
        for key, var in self._pii_vars.items():
            masking_cfg[key] = var.get()
        masking_cfg["custom_patterns"] = list(self._pattern_lb.get(0, "end"))
        self._cfg["mask_color"] = self._mask_color
        self._cfg["tesseract_cmd"] = self._tesseract_var.get().strip()
        cfg.save(self._cfg)
        self._root.destroy()

    # ─── 表示 ────────────────────────────────────────────────────────────────

    def show(self) -> None:
        """親ウィンドウありのモーダル表示。"""
        self._root.grab_set()
        self._root.wait_window()

    def show_standalone(self) -> None:
        """スタンドアロン表示（単体テスト・デバッグ用）。"""
        self._root.mainloop()  # type: ignore[attr-defined]
