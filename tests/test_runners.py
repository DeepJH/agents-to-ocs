"""
自动化单元测试套件：验证三大 Agent 驱动、提示词构建与 OCS 匹配算法
"""
import unittest
from runners import get_runner, list_runners
from prompt_builder import clean_html, build_prompt
from ocs_matcher import parse_model_json, normalize_answer_for_ocs
from cache_store import CacheStore

class TestRunners(unittest.TestCase):
    def test_list_runners(self):
        runners = list_runners()
        keys = [r["key"] for r in runners]
        self.assertIn("agy", keys)
        self.assertIn("claude", keys)
        self.assertIn("codex", keys)

    def test_agy_command_builder(self):
        runner = get_runner("agy")
        cmd = runner.build_command("test prompt", "gemini-3.8-flash-low", ["/tmp/img.png"])
        self.assertIn("agy", cmd[0])
        self.assertIn("-p", cmd)
        self.assertIn("test prompt", cmd)
        self.assertIn("--model", cmd)
        self.assertIn("gemini-3.8-flash-low", cmd)
        self.assertIn("--dangerously-skip-permissions", cmd)

    def test_claude_command_builder(self):
        runner = get_runner("claude")
        cmd = runner.build_command("test claude", "haiku", [])
        self.assertIn("claude", cmd[0])
        self.assertIn("-p", cmd)
        self.assertIn("test claude", cmd)
        self.assertIn("--model", cmd)
        self.assertIn("haiku", cmd)
        self.assertIn("--dangerously-skip-permissions", cmd)

    def test_codex_command_builder(self):
        runner = get_runner("codex")
        cmd = runner.build_command("test codex", "o3-mini", ["/tmp/1.png", "/tmp/2.png"])
        self.assertIn("codex", cmd[0])
        self.assertIn("exec", cmd)
        self.assertIn("test codex", cmd)
        self.assertIn("-m", cmd)
        self.assertIn("o3-mini", cmd)
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", cmd)
        self.assertIn("--ephemeral", cmd)
        # 验证图片参数 -i 是否正确追加
        self.assertIn("-i", cmd)
        self.assertIn("/tmp/1.png", cmd)
        self.assertIn("/tmp/2.png", cmd)

class TestPromptAndMatcher(unittest.TestCase):
    def test_clean_html(self):
        raw = "<p>什么是&quot;人工智能&quot;？&nbsp;<span>请选择</span></p>"
        cleaned = clean_html(raw)
        self.assertEqual(cleaned, '什么是"人工智能"？ 请选择')

    def test_build_prompt(self):
        p = build_prompt("single", "1+1=?", "A. 1\nB. 2", ["/tmp/pic.png"])
        self.assertIn("单选题", p)
        self.assertIn("1+1=?", p)
        self.assertIn("1. A. 1", p)
        self.assertIn("/tmp/pic.png", p)

    def test_parse_model_json(self):
        # 纯 JSON
        ans, reason = parse_model_json('{"answer": "B. 2", "reason": "数学常识"}')
        self.assertEqual(ans, "B. 2")
        self.assertEqual(reason, "数学常识")

        # Markdown 围栏 JSON
        ans2, reason2 = parse_model_json('```json\n{"answer": "对", "reason": "正确"}\n```')
        self.assertEqual(ans2, "对")

    def test_normalize_multiple_choice(self):
        # 包含逗号分词的多选，自动转换为 # 分隔且对齐选项原文
        options = "A. 北京\nB. 上海\nC. 广州\nD. 重庆"
        ans = normalize_answer_for_ocs("multiple", "北京, 上海, 重庆", options)
        self.assertEqual(ans, "A. 北京#B. 上海#D. 重庆")

    def test_normalize_judgement(self):
        options = "A. 正确\nB. 错误"
        ans = normalize_answer_for_ocs("judgement", "对", options)
        self.assertEqual(ans, "A. 正确")

if __name__ == "__main__":
    unittest.main()
