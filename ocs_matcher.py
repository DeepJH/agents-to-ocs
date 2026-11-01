"""
OCS 答案清洗与校验模块：解析模型输出，对齐 OCS 选项匹配规范
"""
import json
import re
from typing import Tuple, List

def parse_model_json(content: str) -> Tuple[str, str]:
    """
    从模型返回的文本中提取 answer 与 reason
    """
    if not content or not content.strip():
        return "", "模型返回为空"

    raw = content.strip()

    # 1. 尝试直接解析 JSON
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            ans = obj.get("answer") or obj.get("答案") or ""
            reason = obj.get("reason") or obj.get("理由") or ""
            return str(ans).strip(), str(reason).strip()
    except Exception:
        pass

    # 2. 尝试提取 Markdown 代码块中的 JSON
    fenced_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, re.IGNORECASE)
    if fenced_match:
        try:
            obj = json.loads(fenced_match.group(1))
            if isinstance(obj, dict):
                ans = obj.get("answer") or obj.get("答案") or ""
                reason = obj.get("reason") or obj.get("理由") or ""
                return str(ans).strip(), str(reason).strip()
        except Exception:
            pass

    # 3. 尝试非贪婪提取最精确的包含 answer 键名的 {...} 结构（防思考过程干扰）
    for match in re.finditer(r"(\{[\s\S]*?\})", raw):
        try:
            obj = json.loads(match.group(1))
            if isinstance(obj, dict) and ("answer" in obj or "答案" in obj):
                ans = obj.get("answer") or obj.get("答案") or ""
                reason = obj.get("reason") or obj.get("理由") or ""
                return str(ans).strip(), str(reason).strip()
        except Exception:
            continue

    # 4. 尝试提取最外层大括号兜底
    brace_match = re.search(r"(\{[\s\S]*\})", raw)
    if brace_match:
        try:
            obj = json.loads(brace_match.group(1))
            if isinstance(obj, dict):
                ans = obj.get("answer") or obj.get("答案") or ""
                reason = obj.get("reason") or obj.get("理由") or ""
                return str(ans).strip(), str(reason).strip()
        except Exception:
            pass

    # 5. 退化：取第一行有效文本
    first_line = [line.strip() for line in raw.split("\n") if line.strip()]
    ans = first_line[0] if first_line else ""
    return ans, "JSON 解析失败，降级提取首行"

def clean_option_prefix(text: str) -> str:
    """
    去除各种网课复杂的选项前缀：
    例如：'A. ', 'A、', '(A) ', '（A）', '[1] ', '【A】', '① ', '一、 ' 等
    """
    if not text:
        return ""
    pattern = r"^[\(\（\[\【]?[A-Za-z0-9①-⑩一二三四五六七八九十][\)\）\]\】\.\、\:\：\s\-]+\s*"
    return re.sub(pattern, "", text.strip()).strip()

def normalize_answer_for_ocs(q_type: str, answer: str, options_str: str) -> str:
    """
    根据题目类型与选项列表，对答案进行规范化，确保 OCS 脚本能精准选中
    """
    if not answer:
        return ""

    q_type = str(q_type).lower()
    raw_options = [o.strip() for o in (options_str or "").split("\n") if o.strip()]

    # 判断题规范化
    if q_type == "judgement":
        ans_raw = answer.strip()
        is_true = any(k in ans_raw for k in ("对", "正确", "T", "True", "true", "√", "✓", "是"))
        is_false = any(k in ans_raw for k in ("错", "错误", "F", "False", "false", "×", "否", "不"))

        if raw_options:
            if is_true and not is_false:
                for opt in raw_options:
                    if any(k in opt for k in ("对", "正确", "T", "True", "true", "√", "✓", "是")):
                        return opt
            elif is_false and not is_true:
                for opt in raw_options:
                    if any(k in opt for k in ("错", "错误", "F", "False", "false", "×", "否", "不")):
                        return opt
            for opt in raw_options:
                if ans_raw in opt or opt in ans_raw:
                    return opt
        return ans_raw

    # 单选题规范化
    if q_type == "single" and raw_options:
        ans_clean = answer.strip()
        ans_without_prefix = clean_option_prefix(ans_clean)

        # 1. 尝试完全匹配
        for opt in raw_options:
            if ans_clean == opt:
                return opt

        # 2. 尝试无前缀匹配 (如果模型只输出了内容，而选项自带 'A. xxx'，则返回选项原文)
        for opt in raw_options:
            opt_without_prefix = clean_option_prefix(opt)
            if ans_without_prefix == opt_without_prefix or ans_clean == opt_without_prefix:
                return opt

        # 3. 包含匹配
        for opt in raw_options:
            if ans_without_prefix in opt or opt in ans_without_prefix:
                return opt

        return ans_clean

    # 多选题规范化：必须使用 '#' 连接
    if q_type == "multiple":
        # 兼容模型用逗号、换行或顿号分隔的情况，统一拆分
        parts = [p.strip() for p in re.split(r"[#\n,，;；]+", answer) if p.strip()]
        if not raw_options:
            return "#".join(parts)

        matched_options: List[str] = []
        for part in parts:
            part_clean = clean_option_prefix(part)
            matched = None
            for opt in raw_options:
                opt_clean = clean_option_prefix(opt)
                if part == opt or part_clean == opt_clean or part_clean in opt:
                    matched = opt
                    break
            if matched and matched not in matched_options:
                matched_options.append(matched)
            elif part and part not in matched_options:
                matched_options.append(part)

        return "#".join(matched_options)

    # 填空题规范化：多空答案使用 '#' 分隔连接
    if q_type == "completion":
        raw_ans = answer.strip()
        # 如果已经存在 '#' 分隔符，按 '#' 拆分并清洗
        if "#" in raw_ans:
            parts = [p.strip() for p in raw_ans.split("#") if p.strip()]
            return "#".join(clean_option_prefix(p) for p in parts)

        # 检查是否按换行分为多空
        lines = [line.strip() for line in raw_ans.split("\n") if line.strip()]
        if len(lines) > 1:
            clean_parts = []
            for line in lines:
                cleaned = re.sub(r"^(?:第[一二三四五六七八九十\d]+空[\:\：\s]*|[\(\（\[\【]?\d+[\)\）\]\】\.\、\:\：\s\-]+\s*)", "", line).strip()
                if cleaned:
                    clean_parts.append(cleaned)
            if clean_parts:
                return "#".join(clean_parts)

        # 检查单行中是否有形如 "1. xxx 2. yyy" 或 "（1）xxx；（2）yyy" 或以分号隔开的多空
        split_pattern = r"(?:[;；]+|(?<=\S)\s+(?=(?:第[一二三四五六七八九十\d]+空|[\(\（\[\【]?\d+[\)\）\]\】\.\、\:\：])))"
        inline_parts = [p.strip() for p in re.split(split_pattern, raw_ans) if p.strip()]
        if len(inline_parts) > 1:
            clean_parts = []
            for part in inline_parts:
                cleaned = re.sub(r"^(?:第[一二三四五六七八九十\d]+空[\:\：\s]*|[\(\（\[\【]?\d+[\)\）\]\】\.\、\:\：\s\-]+\s*)", "", part).strip()
                if cleaned:
                    clean_parts.append(cleaned)
            if clean_parts:
                return "#".join(clean_parts)

        # 单空填空题，去除可能存在的序号或前缀
        cleaned_single = re.sub(r"^(?:第[一二三四五六七八九十\d]+空[\:\：\s]*|[\(\（\[\【]?\d+[\)\）\]\】\.\、\:\：\s\-]+\s*)", "", raw_ans).strip()
        return cleaned_single if cleaned_single else raw_ans

    return answer.strip()
