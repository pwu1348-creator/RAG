from .document_parser import DocumentParser, MinerUAPIParser, BaseParser, ParseResult, DocumentMetadata

# 保持向后兼容
MinerUParser = MinerUAPIParser

__all__ = ['DocumentParser', 'MinerUAPIParser', 'MinerUParser', 'BaseParser', 'ParseResult', 'DocumentMetadata']
