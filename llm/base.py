"""LLM整形エンジンの基底クラス

すべてのLLM整形エンジンはこのインターフェースを実装する。
モジュール設計により、プロバイダーの差し替えが可能。
"""

from abc import ABC, abstractmethod


class LLMFormatter(ABC):
    """LLM整形エンジンの抽象基底クラス"""

    @abstractmethod
    def format_text(self, raw_text: str, prompt_template: str) -> str:
        """生テキストをLLMで整形する

        Args:
            raw_text: STTから得た生テキスト
            prompt_template: 整形プロンプトテンプレート（{raw_text}プレースホルダー含む）

        Returns:
            整形済みテキスト
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """エンジン名を返す"""
        pass
