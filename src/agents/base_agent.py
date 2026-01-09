"""
基础 Agent 类
所有智能体的抽象基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging


class BaseAgent(ABC):
    """
    所有 Agent 的基类
    
    提供统一的接口和共享功能：
    - 日志记录
    - 错误处理
    - 记忆管理
    """
    
    def __init__(
        self,
        name: str,
        llm_client: Any,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化 Agent
        
        Args:
            name: Agent 名称
            llm_client: LLM 客户端
            logger: 日志记录器（可选）
        """
        self.name = name
        self.llm = llm_client
        self.logger = logger or logging.getLogger(name)
        self.memory: List[Dict] = []  # 记忆列表
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入数据
        
        每个 Agent 必须实现此方法
        
        Args:
            input_data: 输入数据
            
        Returns:
            处理结果
        """
        pass
    
    def log(self, message: str, level: str = "info"):
        """
        记录日志
        
        Args:
            message: 日志消息
            level: 日志级别（info, warning, error）
        """
        log_message = f"[{self.name}] {message}"
        
        if level == "info":
            self.logger.info(log_message)
        elif level == "warning":
            self.logger.warning(log_message)
        elif level == "error":
            self.logger.error(log_message)
        
        # 同时打印到控制台（带颜色）
        # ANSI 颜色代码
        colors = {
            'info': '\033[36m',      # 青色（浅色）
            'warning': '\033[33m',   # 黄色
            'error': '\033[31m',     # 红色
            'reset': '\033[0m'       # 重置
        }
        
        color = colors.get(level, colors['info'])
        colored_message = f"{color}{log_message}{colors['reset']}"
        
        try:
            print(colored_message, flush=True)
        except UnicodeEncodeError:
            # 如果遇到编码错误，使用 ASCII 替换不可打印字符
            print(log_message.encode('ascii', 'replace').decode('ascii'), flush=True)
    
    def add_to_memory(self, item: Dict[str, Any]):
        """
        添加到记忆
        
        Args:
            item: 要记忆的项目
        """
        self.memory.append(item)
    
    def get_memory(self, limit: int = None) -> List[Dict]:
        """
        获取记忆
        
        Args:
            limit: 返回数量限制
            
        Returns:
            记忆列表
        """
        if limit:
            return self.memory[-limit:]
        return self.memory
    
    def clear_memory(self):
        """清空记忆"""
        self.memory = []
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
