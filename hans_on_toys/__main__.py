"""ハンズオン資料作成用スクリーンショットツール - CLIエントリポイント"""
import argparse
import platform
import sys
from pathlib import Path


def _setup_dpi() -> None:
    """
    Windows 向け DPI 設定。
    高解像度ディスプレイ（HiDPI/Retina）でtkinterと mss の座標を一致させる。
    """
    if platform.system() != "Windows":
        return
    import ctypes

    try:
        # Windows 8.1+ : Per-Monitor DPI Aware
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except OSError:
        try:
            # Windows Vista+
            ctypes.windll.user32.SetProcessDPIAware()
        except OSError:
            pass


def main() -> None:
    _setup_dpi()

    parser = argparse.ArgumentParser(
        prog="shot",
        description="ハンズオン資料作成用スクリーンショットツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  shot                                 画面上でドラッグして範囲を選択
  shot --region 100 200 900 700        座標を指定して撮影
  shot --output capture.png            クリップボードに加えてファイルにも保存
  shot --region 0 0 1920 1080 -o full.png
        """,
    )
    parser.add_argument(
        "--region",
        nargs=4,
        type=int,
        metavar=("X1", "Y1", "X2", "Y2"),
        help="撮影範囲を座標で指定（左上・右下のピクセル座標）",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        metavar="FILE",
        help="ファイルにも保存する（PNG 推奨）",
    )

    args = parser.parse_args()

    from hans_on_toys.clipboard import copy_to_clipboard
    from hans_on_toys.screenshot import capture_fullscreen, capture_region

    if args.region:
        x1, y1, x2, y2 = args.region
        print(f"範囲 ({x1}, {y1}) - ({x2}, {y2}) を撮影中...")
        image = capture_region(x1, y1, x2, y2)
    else:
        print("画面を取得中...")
        background = capture_fullscreen()

        print("範囲を選択してください（ESC でキャンセル）")
        from hans_on_toys.selector import RegionSelector

        selector = RegionSelector(background)
        region = selector.select()

        if region is None:
            print("キャンセルされました。")
            sys.exit(0)

        x1, y1, x2, y2 = region
        image = background.crop((x1, y1, x2, y2))
        print(
            f"選択範囲: ({x1}, {y1}) - ({x2}, {y2})  "
            f"サイズ: {image.width} x {image.height} px"
        )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        image.save(args.output)
        print(f"ファイルに保存しました: {args.output}")

    copy_to_clipboard(image)
    print("クリップボードにコピーしました。")


if __name__ == "__main__":
    main()
