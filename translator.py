#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ======================================================================
#
# translator_openai.py - openai命令行翻译
#
# Created by twinblade on 2025/05/14
#
# ======================================================================

import sys
import os
import json
import platform
import configparser
import openai
import argparse
from openai import OpenAI

# ----------------------------------------------------------------------
# Windows utf-8兼容
# ----------------------------------------------------------------------
if sys.stdout.encoding != "utf-8":
    # 仅针对windows，注意输出utf-8需要windows上的goldendict客户端支持utf-8，可以使用GoldenDict-ng
    sys.stdout.reconfigure(encoding="utf-8")

# ----------------------------------------------------------------------
# 配置文件地址，兼容windows、linux
# ----------------------------------------------------------------------
os_name = platform.system()
if os_name == "Windows":
    initialization_file = (
        "D:\\GoldenDict-ng\\goldendict-openai-translator\\config.ini"  # windows
    )
elif os_name == "Linux":
    initialization_file = "~/.config/goldendict-openai-translator/config.ini"  # linux


# ----------------------------------------------------------------------
# load config.ini
# ----------------------------------------------------------------------
def load_config(config_path):
    config_path = os.path.expanduser(config_path)
    if not os.path.exists(config_path):
        print(f"!! Error: Config file not found at {config_path}")
        return {}
    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")
    cfg = {}
    if "OpenAI" in config:
        section = config["OpenAI"]
        cfg["OPENAI_API_KEY"] = section.get("OPENAI_API_KEY", "")
        cfg["OPENAI_BASE_URL"] = section.get("OPENAI_BASE_URL", "")
        cfg["OPENAI_REQUEST_TIMEOUT"] = section.getint("OPENAI_REQUEST_TIMEOUT", 15)
        cfg["OPENAI_MODEL"] = section.get("OPENAI_MODEL", "gpt-3.5-turbo")
        cfg["OPENAI_TEMPERATURE"] = section.getfloat("OPENAI_TEMPERATURE", 0.3)
        cfg["OPENAI_MAX_TOKENS"] = section.getint("OPENAI_MAX_TOKENS", 1500)
        cfg["LANGUAGE_RELATED"] = [
            x.strip()
            for x in section.get("LANGUAGE_RELATED", "English,Chinese").split(",")
        ]
    return cfg


# ----------------------------------------------------------------------
# OpenAI Translator
# ----------------------------------------------------------------------
def translate(text_to_translate, config):
    if not text_to_translate or not text_to_translate.strip():
        return "!! Error: Input text is empty."

    client = OpenAI(
        api_key=config["OPENAI_API_KEY"],
        base_url=config["OPENAI_BASE_URL"],
        timeout=config["OPENAI_REQUEST_TIMEOUT"],
    )

    user_prompt = f'Text to translate: "{text_to_translate}"'

    if len(config["LANGUAGE_RELATED"]) == 2:
        language_related_0 = config["LANGUAGE_RELATED"][0]
        language_related_1 = config["LANGUAGE_RELATED"][1]
        message_content = f"Translate the input text from {language_related_0} to {language_related_1} or from {language_related_1} to {language_related_0}. Only output the translated text result without other words."
    elif len(config["LANGUAGE_RELATED"]) == 1:
        language_related_0 = config["LANGUAGE_RELATED"][0]
        message_content = f"Translate the input text to {language_related_0}. Only output the translated text result without other words."
    else:
        return "!! Error: Invalid language configuration in config.ini."

    try:
        response = client.chat.completions.create(
            model=config["OPENAI_MODEL"],
            messages=[
                {
                    "role": "system",
                    "content": message_content,
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=config[
                "OPENAI_TEMPERATURE"
            ],  # temperature越低翻译结果更稳定和准确
            max_tokens=config["OPENAI_MAX_TOKENS"],  # 根据需要调整，确保翻译结果完整
        )

        translated_text = response.choices[0].message.content.strip()

        if not translated_text:
            return "!Warning: No translation returned or input was short/empty"

        return translated_text

    except openai.APIConnectionError as e:
        return f"!! Error: Failed to connect to OpenAI API: {str(e)}"
    except openai.RateLimitError as e:
        return f"!! Error: OpenAI API request exceeded rate limit: {str(e)}"
    except openai.APIStatusError as e:
        return f"!! Error: OpenAI API returned an API Error: Status {e.status_code}, Response: {str(e.response)}"
    except openai.OpenAIError as e:  # other OpenAI errors
        return f"!! Error: An OpenAI error occurred: {str(e)}"
    except Exception as e:
        return f"!! Error: An unexpected error occurred: {str(e)}"


def main():
    if len(sys.argv) < 1:
        print("!! Error: No input text provided.")
        return

    # 读取配置文件
    config = load_config(initialization_file)
    if not config:
        print("!! Error: Failed to load configuration.")
        return

    parser = argparse.ArgumentParser(description="OpenAI Translator for GoldenDict")
    parser.add_argument(
        "--LANGUAGE_RELATED",
        nargs="?",
        type=str,
        help='1 or 2 kinds of languages, seperated by comma。 e.g."English, Chinese" or "Chinese"',
    )
    parser.add_argument("text", nargs="+", help="Text to translate")
    args = parser.parse_args()
    if args.LANGUAGE_RELATED:
        config["LANGUAGE_RELATED"] = [
            x.strip() for x in args.LANGUAGE_RELATED.split(",")
        ]

    # print(config)
    # print(args)

    # Goldendict 通过命令行参数传递要翻译的文本
    if args.text:
        text_to_translate = " ".join(args.text)
    else:
        print("!! Error: No input text provided.")
        return

    translation_result = translate(text_to_translate, config)

    print(text_to_translate)
    print(" \n")
    print(translation_result)


if __name__ == "__main__":
    main()
