# -*- coding: utf-8 -*-
import os
import dashscope
import openai  # 用旧版 SDK 的方式

# === Chinese (Ali DashScope) ===
api_key = ''
base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
dashscope.api_key = api_key

# === English (OpenAI / OpenRouter) ===
llm_api_key = ''  # 可填 openai 或 openrouter 的 API key
llm_base_url = 'https://api.openai.com/v1'  # 可换成 openrouter 地址
vllm_api_key = ''
vllm_base_url = 'https://openrouter.ai/api/v1'

# 配置 openai
openai.api_key = llm_api_key
openai.api_base = llm_base_url

