import requests
import json
from typing import Dict, Any
import re

# 配置参数
XINFERENCE_ENDPOINT = "http://192.168.2.29:9997"  # 实际地址
MODEL_UID = "mec-coder-14b"  # 实际模型ID/名称
# 如果需要认证（通常不需要，但可添加）
HEADERS = {"Content-Type": "application/json"}
# HEADERS = {"Authorization": "Bearer any_key_here"}  # 如果需要认证

def generate_with_xinference(prompt: str, model_uid: str, config: Dict[str, Any] = None) -> str:
    """使用提示词获取 Xinference 模型响应"""
    # 构建请求 URL
    url = f"{XINFERENCE_ENDPOINT}/v1/completions"  # 对于生成式模型
    # url = XINFERENCE_ENDPOINT
    # 如果是聊天模型，使用 chat/completions 端点
    # url = f"{XINFERENCE_ENDPOINT}/v1/chat/completions"
    
    # 默认配置
    default_config = {
        "model": model_uid,
        "prompt": prompt,
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.9,
        # "stop": ["\n\n", "</s>"],
        "stop": [],
        "stream": False
    }
    
    # 合并配置参数
    payload = {**default_config, **(config or {})}
    
    try:
        # 发送 POST 请求
        response = requests.post(
            url,
            headers=HEADERS,
            json=payload,
            timeout=30  # 30秒超时
        )
        
        # 检查HTTP错误
        response.raise_for_status()
        
        # 解析响应
        response_data = response.json()
        
        # 从响应中提取生成的文本
        return response_data['choices'][0]['text']
        # return response_data
        
    except requests.exceptions.RequestException as e:
        return f"请求错误: {str(e)}"
    except KeyError:
        return "错误: 未能从响应中提取文本"
    except json.JSONDecodeError:
        return "错误: 无效的JSON响应"



# 封装  
def raw_test_code(lang_which, lib_which):
    """
    分析:输入是语言选择、包选择
    输出是程序源码
    """
    language = lang_which
    library = lib_which
    # 示例提示词
    test_prompt = f"""
    作为资深{language}开发专家，请严格遵守以下要求编写基础代码：

    **核心要求**
    1. 编写针对`{library}`库所有函数方法中任意一个函数的使用确保多样性。
    
    2. 仅输出可直接执行的{language}源代码，且要符合{language}的语法规范
    3. 严格禁止包含任何形式的：
    - Markdown代码块(```)
    - 注释或解释性文字
    - 被测试函数的实现代码
    """

    # ，要求按照方法的使用频率进行挑选，即高频使用方法优先被挑选，但要
    #  2. 只使用`{library}`库
    # 获取模型响应
    result = generate_with_xinference(
        prompt=test_prompt,
        model_uid=MODEL_UID,
        config={
            "max_tokens": 99999,  # 自定义参数
            "temperature": 0.9
        }
    )
    
    # print("模型响应：")
    # print("-" * 40)
    # print(result)
    # print("-" * 40)
    return result


def advanced_clean_markdown_code(code_block: str) -> str:
    """
    Markdown 代码块清理函数
    - 处理混合空格缩进
    """
    # 移除代码块标记
    cleaned = re.sub(r'^\s*```([a-zA-Z+]*)\s*', '', code_block, flags=re.MULTILINE)
    cleaned = re.sub(r'\s*```\s*$', '', cleaned, flags=re.MULTILINE)
    
    # 分割代码行
    lines = cleaned.splitlines()
    
    # 移除缩进
    processed_lines = []
    for line in lines:
        # 如果行以四个空格开头，则移除这四个空格
        if line.startswith('    '):
            processed_lines.append(line[4:])
        # 否则保留原行
        else:
            processed_lines.append(line)
    
    return '\n'.join(processed_lines)


if __name__ == "__main__":
    language = "java"  # python c java
    library = "gson"  # numpy re math libgflags-dev gson
    result = raw_test_code(language, library)
    result = advanced_clean_markdown_code(result)  # 清除代码块格式
    print(result)
    with open('output.txt', 'w', encoding='utf-8') as file:  # 写出保存测试
        file.write(result)
