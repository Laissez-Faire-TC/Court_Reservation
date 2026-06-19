"""配布用に「パッチ済み chromedriver」をこのフォルダに用意するスクリプト。

ビルド(PyInstaller)の前に、ビルドするPCで一度だけ実行してください:

    python prepare_driver.py

やること:
  1. インストール済み Chrome のバージョンを検出
  2. そのバージョンに「正確に一致する」chromedriver を取得
     （Selenium Manager がChrome本体のフルバージョンに合わせて取得する）
  3. undetected-chromedriver でパッチ（検出回避用の書き換え）
  4. このフォルダに chromedriver(.exe) としてコピー

これで build_windows.spec が同梱し、配布先では uc が DL もパッチもせず
同梱ドライバをそのまま使うため、ネットワークDL失敗や署名/改変の問題を避けられます。

※ Chrome を更新したら、必ず再度このスクリプトを実行してドライバを
  作り直してください（バージョン不一致だと「cannot connect to chrome」
  エラーで起動できません）。
"""
import os
import sys
import shutil


def get_chrome_version():
    """インストール済み Chrome のバージョン文字列（例 149.0.7827.114）を返す。"""
    import subprocess
    import re

    candidates = []
    if sys.platform.startswith("win"):
        # レジストリ or 既定パスから取得
        import winreg
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                key = winreg.OpenKey(hive, r"SOFTWARE\Google\Chrome\BLBeacon")
                ver, _ = winreg.QueryValueEx(key, "version")
                if ver:
                    return ver
            except Exception:
                pass
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
    elif sys.platform == "darwin":
        candidates = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    else:
        candidates = ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]

    for path in candidates:
        try:
            out = subprocess.run([path, "--version"], capture_output=True, text=True)
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)", out.stdout)
            if m:
                return m.group(1)
        except Exception:
            continue
    return None


def fetch_matching_driver(chrome_version):
    """Chrome バージョンに一致する chromedriver を取得し、そのパスを返す。

    Selenium Manager（selenium 4.6+ 内蔵）が Chrome のフルバージョンに
    合わせてドライバを取得・キャッシュする。
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service

    print(f"Chrome {chrome_version} に一致する chromedriver を取得しています...")
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    # ここで起動すると Selenium Manager が一致するドライバを取得する
    driver = webdriver.Chrome(options=opts)
    # 取得されたドライバの実パスを得る
    driver_path = driver.service.path
    driver.quit()
    return driver_path


def main():
    exe_name = "chromedriver.exe" if sys.platform.startswith("win") else "chromedriver"
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), exe_name)

    chrome_version = get_chrome_version()
    if not chrome_version:
        print("警告: Chrome のバージョンを検出できませんでした。")
        print("Chrome がインストールされているか確認してください。")
        sys.exit(1)
    print(f"検出した Chrome バージョン: {chrome_version}")
    chrome_major = chrome_version.split(".")[0]

    # 1. Chrome に一致する素の chromedriver を取得
    try:
        raw_driver = fetch_matching_driver(chrome_version)
    except Exception as e:
        print(f"エラー: chromedriver の取得に失敗しました: {e}")
        sys.exit(1)
    print(f"取得した chromedriver: {raw_driver}")

    # 2. uc の Patcher でパッチ（Chrome のメジャーバージョンを明示）
    from undetected_chromedriver.patcher import Patcher
    print("undetected-chromedriver でパッチしています...")
    patcher = Patcher(executable_path=raw_driver, version_main=int(chrome_major))
    patcher.auto()
    patched_path = patcher.executable_path

    if not os.path.exists(patched_path):
        print(f"エラー: パッチ済みドライバが見つかりません: {patched_path}")
        sys.exit(1)

    # 3. パッチ済みか確認
    with open(patched_path, "rb") as f:
        is_patched = f.read().find(b"undetected chromedriver") != -1
    if not is_patched:
        print("警告: ドライバがパッチ済みとして認識されませんでした。")

    # 4. このフォルダにコピー
    shutil.copy2(patched_path, dest)

    # コピー後のバージョン確認
    import subprocess
    try:
        out = subprocess.run([dest, "--version"], capture_output=True, text=True)
        driver_ver = out.stdout.strip()
    except Exception:
        driver_ver = "(確認できず)"

    print("=" * 60)
    print(f"完了: {dest}")
    print(f"Chrome  : {chrome_version}")
    print(f"Driver  : {driver_ver}")
    print(f"パッチ済み: {'はい' if is_patched else 'いいえ'}")
    print("この状態で build_windows.spec をビルドしてください。")
    print("=" * 60)


if __name__ == "__main__":
    main()
