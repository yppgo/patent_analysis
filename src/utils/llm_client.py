"""
LLM 客户端封装
统一的大模型调用接口
"""

import os
import time
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from openai import APIConnectionError, APITimeoutError, RateLimitError

load_dotenv()


class LLMClient:
    """
    LLM 客户端封装类
    支持多种模型和配置
    """
    
    def __init__(
        self,
        model: str = "qwen-max",
        temperature: float = 0.7,  # 提高到 0.7，增加多样性
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        初始化 LLM 客户端
        
        Args:
            model: 模型名称
            temperature: 温度参数（0-1）
            api_key: API 密钥（可选，默认从环境变量读取）
            base_url: API 基础 URL（可选）
        """
        self.model = model
        self.temperature = temperature
        
        # 获取 API 密钥
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量或传入 api_key 参数")
        
        # 获取 base URL
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        # 创建 LLM 实例（带重试配置）
        self.llm = ChatOpenAI(
            model=self.model,
            openai_api_base=self.base_url,
            openai_api_key=self.api_key,
            temperature=self.temperature,
            max_retries=3,  # 自动重试 3 次
            timeout=60.0,   # 超时时间 60 秒
        )
    
    def invoke(self, prompt: str, max_retries: int = 3, **kwargs) -> str:
        """
        调用 LLM（带手动重试机制）
        
        Args:
            prompt: 提示词
            max_retries: 最大重试次数
            **kwargs: 其他参数
            
        Returns:
            LLM 响应文本
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(prompt, **kwargs)
                return response.content
            except (APIConnectionError, APITimeoutError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 指数退避：2s, 4s, 6s
                    print(f"⚠️ 网络错误，{wait_time}秒后重试 ({attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ 达到最大重试次数，放弃")
            except RateLimitError as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 10  # 速率限制，等待更长时间
                    print(f"⚠️ 速率限制，{wait_time}秒后重试 ({attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ 达到最大重试次数，放弃")
            except Exception as e:
                # 其他错误不重试
                raise e
        
        # 所有重试都失败
        raise last_error
    
    def invoke_with_config(self, prompt: str, config: Dict[str, Any]) -> str:
        """
        使用自定义配置调用 LLM
        
        Args:
            prompt: 提示词
            config: 配置字典（如 temperature, max_tokens 等）
            
        Returns:
            LLM 响应文本
        """
        # 创建临时 LLM 实例
        temp_llm = ChatOpenAI(
            model=self.model,
            openai_api_base=self.base_url,
            openai_api_key=self.api_key,
            **config
        )
        response = temp_llm.invoke(prompt)
        return response.content
    
    def get_llm(self) -> ChatOpenAI:
        """
        获取原始 LLM 实例
        用于需要直接访问 LangChain LLM 的场景
        
        Returns:
            ChatOpenAI 实例
        """
        return self.llm
    
    @classmethod
    def from_env(cls, model: str = "qwen-max", temperature: float = 0.3) -> 'LLMClient':
        """
        从环境变量创建 LLM 客户端
        
        Args:
            model: 模型名称
            temperature: 温度参数
            
        Returns:
            LLMClient 实例
        """
        return cls(model=model, temperature=temperature)


def get_llm_client(model: str = None, temperature: float = 0.3):
    """
    获取 LLM 客户端的便捷函数
    
    Args:
        model: 模型名称（可选，默认从环境变量读取）
        temperature: 温度参数
        
    Returns:
        LLM 实例（ChatOpenAI 或 ChatTongyi）
    """
    provider = os.getenv("LLM_PROVIDER", "dashscope")
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        model = model or os.getenv("OPENAI_MODEL", "gpt-4")
        
        if not api_key:
            raise ValueError("请设置 OPENAI_API_KEY 环境变量")
        
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            temperature=temperature
        )
    
    elif provider == "dashscope":
        api_key = os.getenv("DASHSCOPE_API_KEY")
        model = model or os.getenv("DASHSCOPE_MODEL", "qwen3-max")
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        if not api_key:
            raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量")
        
        return ChatOpenAI(
            model=model,
            openai_api_base=base_url,
            openai_api_key=api_key,
            temperature=temperature
        )
    
    else:
        raise ValueError(f"不支持的 LLM 提供商: {provider}")
