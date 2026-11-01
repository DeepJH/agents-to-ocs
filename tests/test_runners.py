"""
自动化单元测试套件：验证三大 Agent 驱动、提示词构建与 OCS 匹配算法
"""
import unittest
from runners import get_runner, list_runners
from prompt_builder import clean_html, build_prompt
from ocs_matcher import parse_model_json, normalize_answer_for_ocs, clean_option_prefix
import tempfile
import os
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

        # 验证带图片时自动添加 --add-dir 授权临时目录
        cmd_with_img = runner.build_command("test img", "sonnet", ["/tmp/test_dir/img1.png", "/tmp/test_dir/img2.png"])
        self.assertIn("--add-dir", cmd_with_img)
        self.assertIn("/tmp/test_dir", cmd_with_img)

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

    def test_clean_option_prefix(self):
        cases = [
            ("A. 选项内容", "选项内容"),
            ("A、 选项内容", "选项内容"),
            ("(A) 选项内容", "选项内容"),
            ("（A）选项内容", "选项内容"),
            ("【B】 选项内容", "选项内容"),
            ("[1] 选项内容", "选项内容"),
            ("① 选项内容", "选项内容"),
            ("一、 选项内容", "选项内容"),
            ("9. 选项内容", "选项内容"),
        ]
        for raw, expected in cases:
            self.assertEqual(clean_option_prefix(raw), expected)

    def test_parse_model_json_non_greedy(self):
        # 模拟模型输出内部思考过程大括号干扰的情况
        mixed_text = (
            "Thinking process: {\"step\": 1, \"info\": \"calculate\"}\n"
            "Now answer in json:\n"
            "{\"answer\": \"C. 答案\", \"reason\": \"推导完成\"}\n"
            "Hope this helps!"
        )
        ans, reason = parse_model_json(mixed_text)
        self.assertEqual(ans, "C. 答案")
        self.assertEqual(reason, "推导完成")

    def test_normalize_completion(self):
        # 1. 换行带序号的多空
        raw1 = "1. 北京\n2. 上海\n3. 广州"
        self.assertEqual(normalize_answer_for_ocs("completion", raw1, ""), "北京#上海#广州")

        # 2. 单行以分号或序号分隔的多空
        raw2 = "(1) 北京；(2) 上海"
        self.assertEqual(normalize_answer_for_ocs("completion", raw2, ""), "北京#上海")

        # 3. 第X空格式
        raw3 = "第1空：北京\n第2空：上海"
        self.assertEqual(normalize_answer_for_ocs("completion", raw3, ""), "北京#上海")

        # 4. 原生带 # 格式
        raw4 = "北京 # 上海"
        self.assertEqual(normalize_answer_for_ocs("completion", raw4, ""), "北京#上海")

        # 5. 单空题去除前缀
        raw5 = "1. 北京"
        self.assertEqual(normalize_answer_for_ocs("completion", raw5, ""), "北京")

class TestCacheStore(unittest.TestCase):
    def test_cache_clear(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db = f.name

        try:
            store = CacheStore(db_path=temp_db)
            self.assertEqual(store.count(), 0)

            # 插入两条测试记录
            store.set("q1", "single", "A", "理由1")
            store.set("q2", "multiple", "A#B", "理由2")
            self.assertEqual(store.count(), 2)

            # 执行清空
            deleted = store.clear()
            self.assertEqual(deleted, 2)
            self.assertEqual(store.count(), 0)
        finally:
            if os.path.exists(temp_db):
                os.remove(temp_db)

if __name__ == "__main__":
    unittest.main()
