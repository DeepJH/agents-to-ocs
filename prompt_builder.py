"""
提示词工程模块：针对 OCS 各题型规范构造精准提示词，严格限定输出结构为 JSON
"""
import html
import re
from typing import List, Optional

TYPE_MAP = {
    "single": "单选题",
    "multiple": "多选题",
    "judgement": "判断题",
    "completion": "填空题",
}

def clean_html(text: str) -> str:
    """清理题干和选项中的 HTML 标签与实体编码（如 <p>, &nbsp; 等）"""
    if not text:
        return ""
    # 解码 HTML 实体并将不换行空格 \xa0 替换为标准空格
    unescaped = html.unescape(text).replace("\xa0", " ").replace("\u3000", " ")
    # 去除 HTML 标签
    cleaned = re.sub(r"<[^>]+>", " ", unescaped)
    # 合并连续多余空格
    return re.sub(r"[ \t]+", " ", cleaned).strip()

def build_prompt(
    q_type: str,
    title: str,
    options: str,
    image_paths: Optional[List[str]] = None,
) -> str:
    """
    构造统一的提问 Prompt
    """
    title_clean = clean_html(title)
    options_clean = clean_html(options)
    type_cn = TYPE_MAP.get(str(q_type).lower(), "选择/判断题")
    
    prompt_lines = [
        "你是一个极其专业的网课题目解答助手。请仔细阅读以下题目信息，并给出正确答案。",
        "",
        "【严格输出格式要求】",
        "你必须且只能输出一个合法的 JSON 对象，不要附加任何 Markdown 围栏或额外的解说文字：",
        '{"answer": "答案内容", "reason": "一句话理由"}',
        "严禁调用任何搜索、修改或探索工具；若有附带图片，仅读取指定图片后立即输出 JSON 结果。",
        "",
        "【answer 字段填写规范（遵循 OCS 匹配标准，必须严格遵守）】",
        "1. 单选题：answer 必须是【正确选项的原文字符串】。请直接填入选项内容，不要自作主张添加 'A.' 或 'A、' 等序号（除非题目选项原文自带）。",
        "2. 多选题：answer 必须是所有正确选项的原文字符串，按顺序用半角井号 '#' 连接。例如：'第一项原文#第二项原文'。",
        "3. 判断题：answer 必须是【正确选项原文】。如果选项中是'正确'/'错误'则填写'正确'/'错误'；若是'对'/'错'则填'对'/'错'。",
        "4. 填空题：answer 必须是每个空的填空答案，多个空之间用半角井号 '#' 连接。",
        "5. 无法确定时：若完全无法推断，answer 请直接填空字符串 ''，宁可空出也绝对不要胡乱猜测。",
        "",
        "【待解答题目详情】",
        f"题型：{type_cn}",
        f"题干：{title.strip() if title else '（空）'}",
    ]

    opts = [o.strip() for o in (options or "").split("\n") if o.strip()]
    if opts:
        prompt_lines.append("选项列表：")
        for i, opt in enumerate(opts, 1):
            prompt_lines.append(f"  {i}. {opt}")
    else:
        prompt_lines.append("选项列表：无")

    if image_paths and len(image_paths) > 0:
        prompt_lines.append("")
        prompt_lines.append(f"【注意：本题附带 {len(image_paths)} 张图片】")
        for i, p in enumerate(image_paths, 1):
            prompt_lines.append(f"  图片 {i} 路径：{p}")
        prompt_lines.append("请结合图片中的题干、公式或图表内容进行推理并作答。")

    return "\n".join(prompt_lines)
