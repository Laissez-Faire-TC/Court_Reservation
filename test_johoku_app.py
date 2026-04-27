"""
johoku_app.py のユニットテスト
UIやSeleniumに依存しない純粋なロジックをテストします。
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import pandas as pd


# ─── モック設定 ────────────────────────────────────────────
# QThread を実クラスとしてスタブ化しないと WorkerThread の class定義が
# MagicMock に吸収されてしまうため、最低限のスタブを用意する。
class _FakeQThread:
    def __init__(self, *a, **kw):
        pass
    def start(self):
        pass
    def wait(self):
        pass

_fake_qtcore = MagicMock()
_fake_qtcore.QThread = _FakeQThread

_MOCK_MODULES = {
    "PyQt5":                                   MagicMock(),
    "PyQt5.QtWidgets":                         MagicMock(),
    "PyQt5.QtCore":                            _fake_qtcore,
    "PyQt5.QtGui":                             MagicMock(),
    "selenium":                                MagicMock(),
    "selenium.webdriver":                      MagicMock(),
    "selenium.webdriver.chrome":               MagicMock(),
    "selenium.webdriver.chrome.service":       MagicMock(),
    "selenium.webdriver.common.by":            MagicMock(),
    "selenium.webdriver.support":              MagicMock(),
    "selenium.webdriver.support.ui":           MagicMock(),
    "selenium.webdriver.support.expected_conditions": MagicMock(),
    "selenium.webdriver.common.keys":          MagicMock(),
    "selenium.webdriver.common.alert":         MagicMock(),
    "selenium.webdriver.common.action_chains": MagicMock(),
    "selenium.common.exceptions":              MagicMock(),
    "webdriver_manager":                       MagicMock(),
    "webdriver_manager.chrome":                MagicMock(),
}

with patch.dict("sys.modules", _MOCK_MODULES):
    import johoku_app
    from johoku_app import (
        check_server_down_message,
        check_penalty_period,
        setup_chrome_options,
    )
    _distribute_dates_fn = johoku_app.WorkerThread.distribute_dates


# distribute_dates をスタブ経由で呼べるヘルパー
class _StubWorker:
    def __init__(self):
        self.update_signal = MagicMock()
        self.update_signal.emit = MagicMock()

    def distribute_dates(self, base_df, booking_dates, time_code):
        return _distribute_dates_fn(self, base_df, booking_dates, time_code)


# ─────────────────────────────────────────────────────────
# check_server_down_message
# ─────────────────────────────────────────────────────────
class TestCheckServerDownMessage(unittest.TestCase):

    def _driver(self, src):
        d = MagicMock()
        d.page_source = src
        return d

    def test_keyword_page_not_accessible(self):
        self.assertTrue(check_server_down_message(
            self._driver("現在、ご指定のページはアクセスできません")))

    def test_keyword_system_notice(self):
        self.assertTrue(check_server_down_message(
            self._driver("施設予約システムからのお知らせ")))

    def test_keyword_try_later(self):
        self.assertTrue(check_server_down_message(
            self._driver("しばらく経ってから、アクセスしてください")))

    def test_keyword_sorry(self):
        self.assertTrue(check_server_down_message(
            self._driver("ご迷惑をおかけしております")))

    def test_normal_page_returns_false(self):
        self.assertFalse(check_server_down_message(
            self._driver("<html><body>城北中央公園テニスコート予約</body></html>")))

    def test_empty_page_returns_false(self):
        self.assertFalse(check_server_down_message(self._driver("")))

    def test_exception_returns_false(self):
        d = MagicMock()
        type(d).page_source = PropertyMock(side_effect=Exception("接続エラー"))
        self.assertFalse(check_server_down_message(d))


# ─────────────────────────────────────────────────────────
# check_penalty_period
# ─────────────────────────────────────────────────────────
class TestCheckPenaltyPeriod(unittest.TestCase):

    def test_detects_penalty(self):
        driver = MagicMock()
        elem = MagicMock()
        elem.text = "一時停止期間中です。利用再開は〇〇日以降となります。"
        driver.find_element.return_value = elem
        self.assertTrue(check_penalty_period(driver))

    def test_different_text_returns_false(self):
        driver = MagicMock()
        elem = MagicMock()
        elem.text = "通常の利用が可能です。"
        driver.find_element.return_value = elem
        self.assertFalse(check_penalty_period(driver))

    def test_element_not_found_returns_false(self):
        driver = MagicMock()
        driver.find_element.side_effect = Exception("element not found")
        self.assertFalse(check_penalty_period(driver))


# ─────────────────────────────────────────────────────────
# setup_chrome_options
# webdriver.ChromeOptions はモックなので add_argument の呼び出し履歴を検査する。
# モックは使い回されると履歴が蓄積するため、各テストで ChromeOptions() が
# 新しいインスタンスを返すようにパッチする。
# ─────────────────────────────────────────────────────────
class TestSetupChromeOptions(unittest.TestCase):

    def _run(self, headless):
        """独立した MagicMock を ChromeOptions() の戻り値に差し込んで実行"""
        fresh = MagicMock()
        with patch.object(johoku_app.webdriver, "ChromeOptions", return_value=fresh):
            setup_chrome_options(headless=headless)
        args = [c.args[0] if c.args else "" for c in fresh.add_argument.call_args_list]
        return fresh, args

    def test_returns_object(self):
        fresh, _ = self._run(headless=True)
        self.assertIsNotNone(fresh)

    def test_headless_true_adds_headless(self):
        _, args = self._run(headless=True)
        self.assertIn("--headless", args)

    def test_headless_true_adds_window_size(self):
        _, args = self._run(headless=True)
        self.assertIn("--window-size=1920,1080", args)

    def test_headless_true_adds_no_sandbox(self):
        _, args = self._run(headless=True)
        self.assertIn("--no-sandbox", args)

    def test_headless_false_no_headless_arg(self):
        _, args = self._run(headless=False)
        self.assertNotIn("--headless", args)

    def test_headless_false_no_window_size(self):
        _, args = self._run(headless=False)
        self.assertNotIn("--window-size=1920,1080", args)

    def test_disable_extensions_always_set(self):
        for h in (True, False):
            with self.subTest(headless=h):
                _, args = self._run(headless=h)
                self.assertIn("--disable-extensions", args)

    def test_disable_popup_blocking_always_set(self):
        for h in (True, False):
            with self.subTest(headless=h):
                _, args = self._run(headless=h)
                self.assertIn("--disable-popup-blocking", args)

    def test_experimental_options_set(self):
        fresh, _ = self._run(headless=True)
        calls_str = [str(c) for c in fresh.add_experimental_option.call_args_list]
        self.assertTrue(any("excludeSwitches" in c for c in calls_str))
        self.assertTrue(any("useAutomationExtension" in c for c in calls_str))


# ─────────────────────────────────────────────────────────
# WorkerThread.distribute_dates
# ─────────────────────────────────────────────────────────
class TestDistributeDates(unittest.TestCase):

    def _df(self, n):
        return pd.DataFrame({
            "user_number": [f"U{i:03d}" for i in range(n)],
            "password":    ["pass"] * n,
        })

    def test_output_row_count_is_double_input(self):
        result = _StubWorker().distribute_dates(self._df(4), ["2025-06-01", "2025-06-08"], "1")
        self.assertEqual(len(result), 8)

    def test_booking_date_column_created(self):
        result = _StubWorker().distribute_dates(self._df(4), ["2025-06-01", "2025-06-08"], "1")
        self.assertIn("booking_date", result.columns)

    def test_time_code_column_uniform(self):
        result = _StubWorker().distribute_dates(self._df(4), ["2025-06-01", "2025-06-08"], "3")
        self.assertTrue((result["time_code"] == "3").all())

    def test_all_dates_appear(self):
        dates = ["2025-06-01", "2025-06-08", "2025-06-15"]
        result = _StubWorker().distribute_dates(self._df(6), dates, "1")
        for d in dates:
            self.assertIn(d, result["booking_date"].values)

    def test_even_distribution(self):
        # 3人 → 6行、2日 → 各3件
        result = _StubWorker().distribute_dates(self._df(3), ["2025-06-01", "2025-06-08"], "1")
        counts = result["booking_date"].value_counts()
        self.assertEqual(counts["2025-06-01"], 3)
        self.assertEqual(counts["2025-06-08"], 3)

    def test_uneven_remainder_to_first_dates(self):
        # 2人 → 4行、3日 → 2,1,1
        result = _StubWorker().distribute_dates(
            self._df(2), ["2025-06-01", "2025-06-08", "2025-06-15"], "1")
        counts = result["booking_date"].value_counts()
        self.assertEqual(counts.sum(), 4)
        self.assertGreaterEqual(counts.get("2025-06-01", 0), counts.get("2025-06-15", 0))

    def test_single_date_all_rows(self):
        result = _StubWorker().distribute_dates(self._df(5), ["2025-07-01"], "2")
        self.assertTrue((result["booking_date"] == "2025-07-01").all())
        self.assertEqual(len(result), 10)

    def test_original_df_columns_unchanged(self):
        df = self._df(4)
        original_cols = list(df.columns)
        _StubWorker().distribute_dates(df, ["2025-06-01"], "1")
        self.assertEqual(list(df.columns), original_cols)

    def test_returns_new_dataframe(self):
        df = self._df(3)
        result = _StubWorker().distribute_dates(df, ["2025-06-01"], "1")
        self.assertIsNot(result, df)


if __name__ == "__main__":
    unittest.main(verbosity=2)
