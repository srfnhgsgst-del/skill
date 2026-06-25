import sys
from unittest.mock import patch

import pytest

from ecommerce_ops_skill.cli import main, _parse_platform, _demo_items
from ecommerce_ops_skill.platform import Platform
from ecommerce_ops_skill.models import DataSource


class TestParsePlatform:
    def test_by_value(self):
        assert _parse_platform("amazon") == Platform.AMAZON

    def test_by_name(self):
        assert _parse_platform("XIAOHONGSHU") == Platform.XIAOHONGSHU

    def test_by_display(self):
        assert _parse_platform("小红书") == Platform.XIAOHONGSHU

    def test_invalid(self):
        assert _parse_platform("invalid") is None


class TestDemoItems:
    def test_create_items(self):
        items = _demo_items(Platform.JD, "手机", 2)
        assert len(items) == 2
        assert items[0].platform == Platform.JD
        assert items[0].rank == 1
        assert "手机" in items[0].title
        assert items[0].data_source == DataSource.MODEL_ESTIMATION

    def test_bestseller_flag(self):
        items = _demo_items(Platform.TAOBAO, "test", 3)
        assert items[0].is_bestseller is True
        assert items[1].is_bestseller is False


class TestCliCommands:
    def test_list_platforms(self, capsys):
        testargs = ["ecommerce-ops", "list-platforms"]
        with patch.object(sys, "argv", testargs):
            main()
        captured = capsys.readouterr()
        assert "amazon" in captured.out
        assert "xiaohongshu" in captured.out

    def test_strategy_amazon(self, capsys):
        testargs = ["ecommerce-ops", "strategy", "amazon"]
        with patch.object(sys, "argv", testargs):
            main()
        captured = capsys.readouterr()
        assert "amazon" in captured.out.lower()
        assert "steps" in captured.out.lower() or "步骤" in captured.out

    def test_strategy_xiaohongshu(self, capsys):
        testargs = ["ecommerce-ops", "strategy", "xiaohongshu"]
        with patch.object(sys, "argv", testargs):
            main()
        captured = capsys.readouterr()
        assert "xiaohongshu" in captured.out

    def test_strategy_with_budget(self, capsys):
        testargs = ["ecommerce-ops", "strategy", "pinduoduo", "--budget", "low"]
        with patch.object(sys, "argv", testargs):
            main()
        captured = capsys.readouterr()
        assert "pinduoduo" in captured.out

    def test_export_csv(self, capsys):
        testargs = ["ecommerce-ops", "export", "csv", "测试"]
        with patch.object(sys, "argv", testargs):
            main()
        captured = capsys.readouterr()
        assert "Rank" in captured.out
        assert "Platform" in captured.out

    def test_export_json(self, capsys):
        testargs = ["ecommerce-ops", "export", "json", "测试"]
        with patch.object(sys, "argv", testargs):
            main()
        captured = capsys.readouterr()
        assert '"platform"' in captured.out

    def test_report(self, capsys):
        testargs = ["ecommerce-ops", "report", "手机"]
        with patch.object(sys, "argv", testargs):
            main()
        captured = capsys.readouterr()
        assert "TAOBAO" in captured.out

    def test_dashboard(self, capsys):
        testargs = ["ecommerce-ops", "dashboard"]
        with patch.object(sys, "argv", testargs):
            main()
        captured = capsys.readouterr()
        assert "GMV" in captured.out

    def test_compare(self, capsys):
        testargs = ["ecommerce-ops", "compare", "taobao", "jd", "耳机"]
        with patch.object(sys, "argv", testargs):
            main()
        captured = capsys.readouterr()
        assert "taobao" in captured.out
        assert "jd" in captured.out

    def test_xhs_note(self, capsys):
        testargs = ["ecommerce-ops", "xhs-note", "10000", "500", "300", "100", "50"]
        with patch.object(sys, "argv", testargs):
            main()
        captured = capsys.readouterr()
        assert "小红书" in captured.out or "互动率" in captured.out

    def test_unknown_platform(self, capsys):
        testargs = ["ecommerce-ops", "strategy", "unknown"]
        with pytest.raises(SystemExit):
            with patch.object(sys, "argv", testargs):
                main()

    def test_unknown_format(self, capsys):
        testargs = ["ecommerce-ops", "export", "xml", "test"]
        with pytest.raises(SystemExit):
            with patch.object(sys, "argv", testargs):
                main()
