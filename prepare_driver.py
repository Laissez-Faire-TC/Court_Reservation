"""配布用に「パッチ済み chromedriver」をこのフォルダに用意するスクリプト。

ビルド(PyInstaller)の前に、ビルドするPCで一度だけ実行してください:

    python prepare_driver.py

やること:
  1. インストール済み Chrome のバージョンに合う chromedriver を取得
  2. undetected-chromedriver でパッチ（検出回避用の書き換え）
  3. このフォルダに chromedriver(.exe) としてコピー

これで build_windows.spec が同梱し、配布先では uc が DL もパッチもせず
同梱ドライバをそのまま使うため、ネットワークDL失敗や署名/改変の問題を避けられます。
※ Chrome を更新したら、再度このスクリプトを実行してドライバを更新してください。
"""
import os
import sys
import shutil
import undetected_chromedriver as uc
from undetected_chromedriver.patcher import Patcher


def main():
    exe_name = "chromedriver.exe" if sys.platform.startswith("win") else "chromedriver"
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), exe_name)

    print("chromedriver を取得・パッチしています...")
    # Patcher.auto() が DL → パッチまで行う（パッチ済みなら何もしない）
    patcher = Patcher()
    patcher.auto()
    patched_path = patcher.executable_path

    if not os.path.exists(patched_path):
        print(f"エラー: パッチ済みドライバが見つかりません: {patched_path}")
        sys.exit(1)

    # パッチ済みか念のため確認
    with open(patched_path, "rb") as f:
        is_patched = f.read().find(b"undetected chromedriver") != -1
    if not is_patched:
        print("警告: ドライバがパッチ済みとして認識されませんでした。")

    shutil.copy2(patched_path, dest)
    print("=" * 60)
    print(f"完了: {dest}")
    print(f"パッチ済み: {'はい' if is_patched else 'いいえ'}")
    print("この状態で build_windows.spec をビルドしてください。")
    print("=" * 60)


if __name__ == "__main__":
    main()
