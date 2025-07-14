import requests
from langdetect import detect_langs, DetectorFactory
import logging
import re
import tempfile
import os
from typing import Optional

# 设置随机种子以保证一致性
DetectorFactory.seed = 0

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Xinference 配置
XINFERENCE_URL = "http://192.168.2.29:9997/v1/completions"
MODEL_ID = "mec-coder-14b"
API_KEY = "EMPTY"

# 支持的语言及其常用库
SUPPORTED_LANGUAGES = {
    'python': ['numpy', 're', 'math'],
    'java': ['gson'],
    'c': ['libflag']
}

def call_model(prompt: str) -> str:
    """
    调用 Xinference 平台的大模型 API。
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    data = {
        "model": MODEL_ID,
        "prompt": prompt,
        "max_tokens": 512,
        "temperature": 0.7
    }

    try:
        response = requests.post(XINFERENCE_URL, json=data, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['text'].strip()
    except Exception as e:
        logging.error(f"调用大模型失败: {e}")
        return ""

def detect_language(code: str) -> Optional[str]:
    """
    检测给定代码的语言类型。

    :param code: 原始代码字符串
    :return: 检测到的语言类型（'python', 'java', 'c') 或 None
    """

    # 简单关键字匹配作为初步判断
    if any(keyword in code for keyword in ["import numpy", "import re", "import math"]):
        return 'python'
    elif "import com.google.gson" in code:
        return 'java'
    elif "#include <gflags/gflags.h>" in code:
        return 'c'

    # 使用 langdetect 进行更详细的检测
    try:
        detected_languages = detect_langs(code)
        for detected in detected_languages:
            if detected.lang == 'en':
                # 英文主导，可能是 Python
                if any(keyword in code for keyword in ["def ", "class "]):
                    return 'python'
                else:
                    # 可能是 Java 或 C，继续用语法结构判断
                    if "public class" in code or "private String" in code:
                        return 'java'
                    elif "#include" in code and ("int main(" in code or re.search(r"main\s*$$int", code)):
                        return 'c'
    except Exception as e:
        logging.warning(f"无法检测语言: {e}")

    # 最终兜底：完全基于语法结构判断
    if "def " in code or "class " in code:
        return 'python'
    elif "public class" in code or "private String" in code:
        return 'java'
    elif "#include" in code and ("int main(" in code or re.search(r"main\s*$$int", code)):
        return 'c'

    logging.warning("未能识别代码语言。")
    return None


# ————————————————————————
# 合法性校验函数（宽松结构检查）
# ————————————————————————

def is_basic_structure_valid_python(code: str) -> bool:
    """检查 Python 代码的基本结构是否合法"""
    lines = code.splitlines()

    has_def_or_class = False
    brace_count = 0

    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("def ") or stripped_line.startswith("class "):
            has_def_or_class = True
        if stripped_line.endswith(":"):
            brace_count += 1
        if stripped_line == "":
            continue

    # 如果有 def 或 class 定义且至少有一个冒号，则认为结构合法
    if has_def_or_class and brace_count >= 1:
        return True

    # 对于没有 def 或 class 的简单脚本，只要没有明显的错误即可
    if not has_def_or_class and all(line.count('{') == line.count('}') for line in lines):
        return True

    logging.warning("Python 代码基本结构不合法")
    return False


def is_basic_structure_valid_c(code: str) -> bool:
    """检查 C 代码的基本结构是否合法"""
    has_main = 'main' in code
    has_return_zero = 'return 0' in code

    if has_main and has_return_zero:
        return True
    else:
        print("C 代码结构不合法：缺少 'main' 或 'return 0'")
        return False



def is_basic_structure_valid_java(code: str) -> bool:
    """检查 Java 代码的基本结构是否合法"""
    """
    非常宽松的 Java 代码结构检查：
    只要包含 'public class' 和 'main' 就认为合法
    """
    has_public_class = 'public class' in code
    has_main_method = 'public static void main' in code

    if has_public_class and has_main_method:
        return True
    else:
        print("Java 代码结构不合法：缺少 'public class' 或 'main' 方法")
        return False


# ————————————————————————
# 清理代码函数
# ————————————————————————

def clean_code(code: str) -> str:
    """
    清理生成的代码，移除多余的 '}' 符号、Markdown 代码块标记和其他非法字符。
    """
    # 移除 Markdown 代码块标记
    code = re.sub(r"(```\w*\n|\n```\s*)", "", code)

    # 移除多余的 '}' 符号
    code = re.sub(r"(?<!\})}", "", code)

    # 移除多余的反引号
    code = re.sub(r"(`{3})", "", code)

    return code.strip()


# ————————————————————————
# 主要处理函数
# ————————————————————————

def mutate_test_case(code: str) -> Optional[str]:
    """
    对输入代码进行变异处理，并进行语法合法性校验。
    """

    detected_lang = detect_language(code)
    if not detected_lang:
        return None

    detected_lang = detected_lang.lower()
    if detected_lang not in SUPPORTED_LANGUAGES:
        logging.error(f"不支持的语言类型: {detected_lang}")
        return None

    libraries = ", ".join(SUPPORTED_LANGUAGES[detected_lang])
    prompt = f"""
你是一个智能代码变异助手，请将以下{detected_lang}代码进行语义不变但结构变化的修改。
请确保使用相同的库（如 {libraries}），主要对方法进行测试，可以随机改变调用方法中（）里面的参数，一定要引入合理的变种。
原始代码如下:

{code}

请只返回变异后的代码，不要任何解释或格式标记。
"""

    logging.info(f"正在对 {detected_lang} 代码进行变异...")
    mutated_code = call_model(prompt)

    if not mutated_code:
        logging.warning("变异结果为空，可能模型未正确响应。")
        return None

    # 清理生成的代码
    mutated_code = clean_code(mutated_code)

    # 变异后语法合法性校验
    is_valid = False
    if detected_lang == 'python':
        is_valid = is_basic_structure_valid_python(mutated_code)
    elif detected_lang == 'c':
        is_valid = is_basic_structure_valid_c(mutated_code)
    elif detected_lang == 'java':
        is_valid = is_basic_structure_valid_java(mutated_code)

    if not is_valid:
        logging.warning(f"变异后的 {detected_lang} 代码语法不合法，跳过。")
        return None

    logging.info("语法合法性校验通过。")
    return mutated_code.strip()


# ————————————————————————
# 示例主程序入口
# ————————————————————————

if __name__ == "__main__":
    python_code = """
    import re

    text = "The rain in Spain falls mainly in the plain."
    pattern = r"\bin\b"

    matches = re.findall(pattern, text)
    print(matches)
"""

    print("——— 原始代码 ———")
    print(python_code)
    print("\n——— 变异后代码 ———")
    result = mutate_test_case(python_code)
    if result:
        print(result)
    else:
        print("变异失败或生成代码非法。")