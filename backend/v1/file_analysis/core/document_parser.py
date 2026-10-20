import os
import re
import json
import shutil
import time
import tempfile
import uuid
import zipfile
import requests
from urllib.parse import quote
from datetime import datetime, timezone
from typing import Dict, Any, Callable, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from config import config
from utils.logger import logger
from utils.rag_tokenizer import RagTokenizer

try:
    from services.chromadb_service import ChromaDBService
    from services.embedding_service import EmbeddingService
    from services.mysql_service import MySQLService
    SERVICES_AVAILABLE = True
except ImportError as e:
    SERVICES_AVAILABLE = False
    logger.warning(f"[Parser-WARNING] 部分服务不可用: {e}")

_tokenizer = RagTokenizer()

LOCAL_STORAGE_ROOT = r"D:\pengpengRAG\backend\v1\file_analysis\uploads"
LOCAL_IMAGE_DIR = os.path.join(LOCAL_STORAGE_ROOT, "image-minIO")
IMAGE_URL_PREFIX = "http://localhost:8000/uploads/image-minIO"

# MinerU API 直接支持的文件格式
_MINERU_API_SUPPORTED_EXTS = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".png", ".jpg", ".jpeg", ".jp2", ".webp", ".gif", ".bmp",
}
_HTML_EXTS = {".html", ".htm"}
# 直接读取文本内容的格式（不走 LibreOffice / MinerU）
_DIRECT_TEXT_EXTS = {".md", ".txt"}

# 支持的解析引擎（供路由层使用）
SUPPORTED_ENGINES = ("pipeline", "vlm")


@dataclass
class DocumentMetadata:
    title: str = ""
    author: str = ""
    pages: int = 0
    word_count: int = 0
    file_type: str = ""
    has_images: bool = False
    has_tables: bool = False
    has_formulas: bool = False
    processing_time: float = 0.0


@dataclass
class ParseResult:
    text: str
    markdown: str
    middle_content: Any
    metadata: DocumentMetadata
    chunks: List[Dict[str, Any]]
    raw_output: Dict[str, Any]


def _generate_uuid() -> str:
    return str(uuid.uuid4())


def _normalize_content(text: str, chunk_type: str) -> str:
    if chunk_type == "text":
        text = re.sub(r"[!#\\$/]", "", text)
    return text.strip()


def _tokenize(text: str) -> str:
    try:
        return _tokenizer.tokenize(text)
    except Exception as e:
        logger.warning(f"[Parser-WARNING] 分词失败，返回原始文本: {e}")
        return text


def _count_tokens(text: str) -> int:
    """统计文本的 token 数（基于分词结果的词数）。"""
    tks = _tokenize(text)
    return len(tks.split()) if tks else 0


def _split_text_by_token(text: str, max_tokens: int = 512) -> List[str]:
    """将超过 max_tokens 的文本按句子边界强制切分为多段。"""
    if _count_tokens(text) <= max_tokens:
        return [text]

    # 按句子边界切分（中英文句号、换行）
    sentences = re.split(r'(?<=[。！？\n.!?])', text)
    segments = []
    current_segment = ""

    for sentence in sentences:
        if not sentence:
            continue
        candidate = current_segment + sentence
        if _count_tokens(candidate) > max_tokens and current_segment:
            segments.append(current_segment.strip())
            current_segment = sentence
        else:
            current_segment = candidate

    # 处理剩余内容
    if current_segment.strip():
        # 如果最后一段仍然超过限制，按字符硬切
        if _count_tokens(current_segment) > max_tokens:
            words = current_segment.split()
            buf = []
            for w in words:
                buf.append(w)
                if _count_tokens(" ".join(buf)) > max_tokens:
                    buf.pop()
                    if buf:
                        segments.append(" ".join(buf))
                    buf = [w]
            if buf:
                segments.append(" ".join(buf))
        else:
            segments.append(current_segment.strip())

    return segments if segments else [text]


def _content_list_to_chunks(
    content_list: List[Dict[str, Any]],
    doc_name: str = "",
    chunk_token_num: int = 512,
) -> List[Dict[str, Any]]:
    title_tks = _tokenize(doc_name) if doc_name else ""
    chunks = []

    for item in content_list:
        chunk_type = item.get("type", "text")

        if chunk_type in ("text", "equation"):
            raw_content = item.get("text", "").strip()
            if not raw_content:
                continue

        elif chunk_type == "table":
            caption_list = item.get("table_caption", [])
            table_body   = item.get("table_body", "").strip()
            if not table_body:
                continue
            if isinstance(caption_list, list):
                caption_str = " ".join(caption_list)
            elif isinstance(caption_list, str):
                caption_str = caption_list
            else:
                caption_str = ""
            raw_content = (caption_str + "\n" + table_body).strip() if caption_str else table_body

        else:
            continue

        content = _normalize_content(raw_content, chunk_type)
        if not content:
            continue

        # 超过 token 限制则强制切分
        segments = _split_text_by_token(content, chunk_token_num)

        for seg in segments:
            content_tks = _tokenize(seg)
            chunks.append({
                "content":         seg,
                "content_ltks":    content_tks,
                "content_sm_ltks": content_tks,
                "title_tks":       title_tks,
                "title_sm_tks":    title_tks,
                "type":            chunk_type,
                "page_idx":        item.get("page_idx", 0),
                "bbox":            item.get("bbox", [0, 0, 0, 0]),
                "img_id":          "",
            })

    logger.info(
        f"[Parser-INFO] content_list → chunks: {len(content_list)} 条 → {len(chunks)} 个 chunks "
        f"(token 上限={chunk_token_num})"
    )
    return chunks


class BaseParser(ABC):
    @abstractmethod
    def parse(
        self,
        file_path: str,
        options: Dict[str, Any] = None,
        progress_callback: Callable[[int], None] = None,
    ) -> ParseResult:
        pass


class DirectTextParser(BaseParser):
    """直接读取 txt/md 文件内容，按段落和 token 上限切分为 chunks。
    不走 LibreOffice / MinerU API，速度快且无外部依赖。"""

    def parse(
        self,
        file_path: str,
        options: Dict[str, Any] = None,
        progress_callback: Callable[[int], None] = None,
    ) -> ParseResult:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        start_time = time.time()
        filename = os.path.basename(file_path)
        doc_name = os.path.splitext(filename)[0]
        ext = os.path.splitext(file_path)[1].lower()

        if progress_callback:
            progress_callback(10)

        # 1. 读取文件内容（自动检测编码）
        text = self._read_text_file(file_path)
        logger.info(f"[DirectTextParser] 读取文件完成: {filename}, 字符数={len(text)}")

        if progress_callback:
            progress_callback(30)

        # 2. 按段落切分文本
        chunk_token_num = (options or {}).get("chunk_token_num", 512)
        paragraphs = self._split_into_paragraphs(text, ext)

        if progress_callback:
            progress_callback(50)

        # 3. 将段落转为 chunks（超长段落会被进一步切分）
        title_tks = _tokenize(doc_name) if doc_name else ""
        chunks = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            # 对每个段落按 token 上限切分
            segments = _split_text_by_token(para, chunk_token_num)
            for seg in segments:
                content_tks = _tokenize(seg)
                chunks.append({
                    "content":         seg,
                    "content_ltks":    content_tks,
                    "content_sm_ltks": content_tks,
                    "title_tks":       title_tks,
                    "title_sm_tks":    title_tks,
                    "type":            "text",
                    "page_idx":        0,
                    "bbox":            [0, 0, 0, 0],
                    "img_id":          "",
                })

        logger.info(
            f"[DirectTextParser] 切分完成: {len(paragraphs)} 段 → {len(chunks)} 个 chunks "
            f"(token 上限={chunk_token_num})"
        )

        if progress_callback:
            progress_callback(80)

        # 4. 构造元数据
        processing_time = time.time() - start_time
        # 提取标题：取第一行非空文本
        title = doc_name
        first_line = text.strip().split("\n")[0].strip() if text.strip() else ""
        if first_line:
            # 去掉 markdown 标题符号
            clean_title = re.sub(r'^#+\s*', '', first_line).strip()
            if clean_title:
                title = clean_title[:80]

        metadata = DocumentMetadata(
            title=title,
            author="",
            pages=1,
            word_count=len(text),
            file_type=ext,
            has_images=False,
            has_tables=False,
            has_formulas=False,
            processing_time=processing_time,
        )

        if progress_callback:
            progress_callback(100)

        # markdown 内容：对 .md 文件直接用原文，对 .txt 文件用原文
        markdown_content = text if ext == ".md" else ""

        return ParseResult(
            text=text,
            markdown=markdown_content,
            middle_content={},
            metadata=metadata,
            chunks=chunks,
            raw_output={
                "content_list": [{"type": "text", "text": p} for p in paragraphs if p.strip()],
                "middle_content": {},
                "temp_image_dir": "",
            },
        )

    def _read_text_file(self, file_path: str) -> str:
        """读取文本文件，尝试多种编码。"""
        encodings = ["utf-8", "utf-8-sig", "gbk", "gb2312", "latin-1"]
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
        # 最后兜底用 latin-1（不会抛异常）
        with open(file_path, "r", encoding="latin-1") as f:
            return f.read()

    def _split_into_paragraphs(self, text: str, ext: str) -> List[str]:
        """按段落切分文本。
        - md 文件：按标题（# ## ###）和双换行切分
        - txt 文件：按双换行或单换行（连续空行）切分
        合并过短的段落，避免产生过多碎片 chunk。
        """
        if ext == ".md":
            # Markdown：按标题行切分，保留标题作为段落开头
            parts = re.split(r'(?=^#{1,6}\s)', text, flags=re.MULTILINE)
            # 对非标题部分再按双换行切分
            paragraphs = []
            for part in parts:
                if not part.strip():
                    continue
                sub_parts = re.split(r'\n\s*\n', part)
                paragraphs.extend(sub_parts)
        else:
            # 纯文本：按双换行切分
            paragraphs = re.split(r'\n\s*\n', text)

        # 合并过短的段落（少于 50 字符的段落与下一段合并）
        merged = []
        buffer = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if buffer:
                buffer = buffer + "\n" + para
            else:
                buffer = para
            # 如果当前 buffer 足够长，输出
            if len(buffer) >= 50:
                merged.append(buffer)
                buffer = ""
        # 剩余内容
        if buffer:
            if merged:
                merged[-1] = merged[-1] + "\n" + buffer
            else:
                merged.append(buffer)

        return merged


class MinerUAPIParser(BaseParser):
    """通过 MinerU 云端 API 进行文档解析，替代本地 MinerU 库调用。"""

    def __init__(self):
        self.api_base_url = config.mineru.API_BASE_URL
        self.api_token = config.mineru.API_TOKEN
        self.file_url_prefix = config.mineru.FILE_URL_PREFIX
        self.poll_interval = config.mineru.POLL_INTERVAL
        self.poll_timeout = config.mineru.POLL_TIMEOUT
        self.direct_text_parser = DirectTextParser()

    def parse(
        self,
        file_path: str,
        options: Dict[str, Any] = None,
        progress_callback: Callable[[int], None] = None,
    ) -> ParseResult:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        # txt/md 文件：直接读取文本内容，不走 LibreOffice / MinerU API
        if ext in _DIRECT_TEXT_EXTS:
            return self.direct_text_parser.parse(file_path, options, progress_callback)

        # MinerU API 直接支持的格式（含未知格式，尝试直接提交）
        if ext in _MINERU_API_SUPPORTED_EXTS or ext in _HTML_EXTS:
            return self._parse_via_api(file_path, ext, options, progress_callback)

        # 未知格式也尝试通过 MinerU API 解析
        logger.warning(f"[Parser-WARNING] 文件格式 {ext} 不在已知列表中，尝试直接提交 MinerU API")
        return self._parse_via_api(file_path, ext, options, progress_callback)

    def _parse_via_api(
        self,
        file_path: str,
        ext: str,
        options: Dict[str, Any] = None,
        progress_callback: Callable[[int], None] = None,
    ) -> ParseResult:
        """通过 MinerU 云端 API 解析文档。"""
        start_time = time.time()
        filename = os.path.basename(file_path)

        if progress_callback:
            progress_callback(10)

        # 1. 构造公网 URL（对文件名进行 URL 编码，处理中文等特殊字符）
        encoded_filename = quote(filename, safe="")
        file_url = f"{self.file_url_prefix}/{encoded_filename}"
        logger.info(f"[Parser-INFO] 文件公网 URL: {file_url}")

        # 2. 确定 model_version
        if ext in _HTML_EXTS:
            model_version = "MinerU-HTML"
        else:
            engine = config.mineru.PARSE_ENGINE or "pipeline"
            model_version = "pipeline" if engine == "pipeline" else "vlm"

        # 3. 创建解析任务
        task_id = self._create_task(file_url, model_version, options)
        logger.info(f"[Parser-INFO] 创建 MinerU API 任务成功: task_id={task_id}, model={model_version}")

        if progress_callback:
            progress_callback(30)

        # 4. 轮询等待任务完成
        result = self._poll_task(task_id, progress_callback)
        logger.info(f"[Parser-INFO] MinerU API 任务完成: task_id={task_id}")

        if progress_callback:
            progress_callback(70)

        # 5. 下载并解压 zip
        zip_url = result.get("full_zip_url", "")
        if not zip_url:
            raise RuntimeError(f"API 返回结果中缺少 full_zip_url: {result}")

        content_list, markdown = self._download_and_extract(zip_url)
        logger.info(f"[Parser-INFO] 下载解压完成，content_list 条目数: {len(content_list)}")

        # 6. 转为 chunks（超过 token 上限的 chunk 会被强制切分）
        doc_name = os.path.splitext(filename)[0]
        chunk_token_num = (options or {}).get("chunk_token_num", 512)
        chunks = _content_list_to_chunks(content_list, doc_name=doc_name, chunk_token_num=chunk_token_num)

        # 7. 构造元数据
        processing_time = time.time() - start_time
        metadata = self._extract_metadata(file_path, content_list, processing_time)

        if progress_callback:
            progress_callback(100)

        return ParseResult(
            text=self._content_list_to_text(content_list),
            markdown=markdown,
            middle_content={},
            metadata=metadata,
            chunks=chunks,
            raw_output={
                "content_list": content_list,
                "middle_content": {},
                "temp_image_dir": "",
            },
        )

    def _create_task(self, file_url: str, model_version: str, options: Dict[str, Any] = None) -> str:
        """调用 MinerU API 创建解析任务。"""
        url = f"{self.api_base_url}/extract/task"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }

        payload = {
            "url": file_url,
            "model_version": model_version,
        }

        # is_ocr / enable_formula / enable_table / language 仅对 pipeline/vlm 有效
        if model_version in ("pipeline", "vlm"):
            payload["is_ocr"] = config.mineru.ENABLE_OCR
            payload["enable_formula"] = True
            payload["enable_table"] = True
            payload["language"] = "ch"

        logger.info(f"[Parser-INFO] 创建任务请求: {url}, payload={payload}")
        resp = requests.post(url, json=payload, headers=headers, timeout=30)

        if resp.status_code != 200:
            raise RuntimeError(
                f"MinerU API 创建任务失败: status={resp.status_code}, body={resp.text}"
            )

        data = resp.json()
        # API 返回格式: {"code": 0, "msg": "ok", "data": {"task_id": "xxx"}}
        if data.get("code") != 0:
            raise RuntimeError(f"MinerU API 创建任务错误: {data}")

        task_id = data.get("data", {}).get("task_id", "")
        if not task_id:
            raise RuntimeError(f"MinerU API 返回中缺少 task_id: {data}")

        return task_id

    def _poll_task(self, task_id: str, progress_callback: Callable[[int], None] = None) -> Dict[str, Any]:
        """轮询任务状态直到完成或超时。"""
        url = f"{self.api_base_url}/extract/task/{task_id}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
        }

        elapsed = 0
        while elapsed < self.poll_timeout:
            time.sleep(self.poll_interval)
            elapsed += self.poll_interval

            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code != 200:
                logger.warning(f"[Parser-WARNING] 轮询请求失败: status={resp.status_code}")
                continue

            data = resp.json()
            task_data = data.get("data", {})
            status = task_data.get("state", "")

            logger.info(f"[Parser-INFO] 任务状态: {status} (elapsed={elapsed}s)")

            if status == "done":
                return task_data
            elif status in ("failed", "error"):
                raise RuntimeError(f"MinerU API 任务失败: {task_data}")

            # 更新进度（30-70 之间线性映射）
            if progress_callback and self.poll_timeout > 0:
                progress = 30 + int((elapsed / self.poll_timeout) * 40)
                progress = min(progress, 69)
                progress_callback(progress)

        raise TimeoutError(
            f"MinerU API 任务超时: task_id={task_id}, timeout={self.poll_timeout}s"
        )

    def _download_and_extract(self, zip_url: str) -> tuple:
        """下载 zip 文件并提取 content_list.json 和 full.md。"""
        temp_dir = tempfile.mkdtemp(prefix="mineru_api_")
        zip_path = os.path.join(temp_dir, "result.zip")

        try:
            # 下载 zip
            logger.info(f"[Parser-INFO] 下载结果 zip: {zip_url}")
            resp = requests.get(zip_url, timeout=120, stream=True)
            resp.raise_for_status()

            with open(zip_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 解压
            extract_dir = os.path.join(temp_dir, "extracted")
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)

            # 查找 *_content_list.json
            content_list = []
            markdown = ""

            for root, dirs, files in os.walk(extract_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    if fname.endswith("_content_list.json") or fname == "content_list.json":
                        with open(fpath, "r", encoding="utf-8") as f:
                            content_list = json.load(f)
                        logger.info(f"[Parser-INFO] 找到 content_list: {fname}")
                    elif fname == "full.md":
                        with open(fpath, "r", encoding="utf-8") as f:
                            markdown = f.read()
                        logger.info(f"[Parser-INFO] 找到 full.md")

            if not content_list:
                # 尝试查找任何 json 文件作为 content_list
                for root, dirs, files in os.walk(extract_dir):
                    for fname in files:
                        if fname.endswith(".json") and "content_list" in fname:
                            fpath = os.path.join(root, fname)
                            with open(fpath, "r", encoding="utf-8") as f:
                                content_list = json.load(f)
                            logger.info(f"[Parser-INFO] 备选 content_list: {fname}")
                            break

            return content_list, markdown

        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _extract_metadata(
        self,
        file_path: str,
        content_list: List[Dict],
        processing_time: float,
    ) -> DocumentMetadata:
        pages = {item["page_idx"] for item in content_list if "page_idx" in item}
        images = {item.get("img_path") for item in content_list if item.get("type") == "image" and item.get("img_path")}

        title = os.path.splitext(os.path.basename(file_path))[0]
        for item in content_list:
            if item.get("type") == "text" and item.get("text", "").strip():
                first_line = item["text"].strip().splitlines()[0]
                if first_line:
                    title = first_line[:80]
                break

        word_count = sum(
            len(item.get("text", "") + item.get("table_body", ""))
            for item in content_list
        )

        return DocumentMetadata(
            title=title,
            author="",
            pages=len(pages),
            word_count=word_count,
            file_type=os.path.splitext(file_path)[1].lower(),
            has_images=bool(images),
            has_tables=any(i.get("type") == "table" for i in content_list),
            has_formulas=any(i.get("type") == "equation" for i in content_list),
            processing_time=processing_time,
        )

    def _content_list_to_text(self, content_list: List[Dict]) -> str:
        """将 content_list 转为纯文本。"""
        lines = []
        for item in content_list:
            text = item.get("text", "").strip()
            if text:
                lines.append(text)
            table_body = item.get("table_body", "").strip()
            if table_body:
                lines.append(table_body)
        return "\n".join(lines)


class DocumentParser:
    def __init__(self):
        self.mineru_parser = MinerUAPIParser()
        self._ensure_image_directory()

    def _ensure_image_directory(self):
        try:
            Path(LOCAL_IMAGE_DIR).mkdir(parents=True, exist_ok=True)
            logger.info(f"[Parser-INFO] 图片存储目录已创建/已存在: {LOCAL_IMAGE_DIR}")
        except Exception as e:
            logger.error(f"[Parser-ERROR] 创建图片目录失败: {e}")

    def _upload_image_local(self, img_path_src: str) -> Optional[Dict[str, str]]:
        if not os.path.exists(img_path_src):
            logger.warning(f"[Parser-WARNING] 图片文件不存在: {img_path_src}")
            return None
        try:
            img_id       = _generate_uuid()
            img_ext      = os.path.splitext(img_path_src)[1]
            img_filename = f"{img_id}{img_ext}"
            img_path_dst = os.path.join(LOCAL_IMAGE_DIR, img_filename)
            shutil.copy2(img_path_src, img_path_dst)
            img_url = f"{IMAGE_URL_PREFIX}/{img_filename}"
            logger.info(f"[Parser-INFO] 图片处理完成 - ID: {img_id}, URL: {img_url}")
            return {"img_id": img_id, "img_url": img_url, "img_path_local": img_path_dst}
        except Exception as e:
            logger.error(f"[Parser-ERROR] 上传图片失败: {e}")
            return None

    def _process_images(
        self,
        content_list: List[Dict[str, Any]],
        temp_image_dir: str,
        chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        image_info_list = []

        for idx, item in enumerate(content_list):
            if item.get("type") != "image":
                continue
            img_path_rel = item.get("img_path") or item.get("img_url", "")
            if not img_path_rel:
                continue
            img_path_abs = os.path.join(temp_image_dir, os.path.basename(img_path_rel))
            info = self._upload_image_local(img_path_abs)
            if info:
                info["position"] = idx
                image_info_list.append(info)

        if image_info_list:
            for chunk_idx, chunk in enumerate(chunks):
                if chunk["type"] not in ("text", "table"):
                    continue
                nearest, min_dist = None, float("inf")
                for img_info in image_info_list:
                    dist = abs(chunk_idx - img_info["position"])
                    if dist < 5 and dist < min_dist:
                        nearest, min_dist = img_info, dist
                if nearest:
                    chunk["img_id"] = nearest["img_id"]
                    logger.info(
                        f"[Parser-INFO] 关联图片到块 {chunk_idx}: "
                        f"img_id={nearest['img_id']}, distance={min_dist}"
                    )

        return image_info_list

    def parse(
        self,
        file_path: str,
        options: Dict[str, Any] = None,
        progress_callback: Callable[[int], None] = None,
    ) -> Dict[str, Any]:
        result = self.mineru_parser.parse(file_path, options, progress_callback)

        temp_image_dir = options.get("temp_image_dir", "") if options else ""
        image_info_list = []
        if temp_image_dir and os.path.isdir(temp_image_dir):
            content_list    = result.raw_output.get("content_list", [])
            image_info_list = self._process_images(content_list, temp_image_dir, result.chunks)

        image_count = len(image_info_list)

        _raw_temp_image_dir = result.raw_output.get('temp_image_dir', '')
        if _raw_temp_image_dir:
            _temp_dir = os.path.dirname(_raw_temp_image_dir)
            if os.path.isdir(_temp_dir):
                shutil.rmtree(_temp_dir, ignore_errors=True)

        # 根据文件类型确定 parser 标识
        ext = os.path.splitext(file_path)[1].lower()
        parser_name = "direct_text" if ext in _DIRECT_TEXT_EXTS else "mineru_api"

        return {
            "text":           result.text,
            "markdown":       result.markdown,
            "middle_content": result.middle_content,
            "chunks":         result.chunks,
            "images":         image_info_list,
            "metadata": {
                "title":           result.metadata.title,
                "author":          result.metadata.author,
                "pages":           result.metadata.pages,
                "word_count":      result.metadata.word_count,
                "file_type":       result.metadata.file_type,
                "has_images":      result.metadata.has_images,
                "has_tables":      result.metadata.has_tables,
                "has_formulas":    result.metadata.has_formulas,
                "processing_time": result.metadata.processing_time,
                "parser":          parser_name,
                "image_count":     image_count,
            },
        }


class DocumentProcessor:
    def __init__(self):
        self.parser    = DocumentParser()
        self.chromadb  = ChromaDBService() if SERVICES_AVAILABLE else None
        self.embedding = EmbeddingService() if SERVICES_AVAILABLE else None
        self.mysql     = MySQLService()     if SERVICES_AVAILABLE else None

    def perform_parse(
        self,
        raw_chunks: List[Dict[str, Any]],
        doc_id: str,
        kb_id: str,
        doc_name: str,
    ) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        current_timestamp = now.timestamp()

        title_tks = _tokenize(doc_name) if doc_name else ""

        enriched_chunks = []
        for chunk in raw_chunks:
            content = chunk.get("content", "")
            page_idx = chunk.get("page_idx", 0)
            bbox = chunk.get("bbox", [0, 0, 0, 0])

            content_ltks = chunk.get("content_ltks", "") or _tokenize(content)
            content_sm_ltks = chunk.get("content_sm_ltks", "") or _tokenize(content)

            position_int = [[page_idx + 1] + list(bbox)] if bbox else [[page_idx + 1, 0, 0, 0, 0]]

            enriched_chunk = {
                "doc_id":              doc_id,
                "kb_id":               kb_id,
                "docnm_kwd":           doc_name,
                "title_tks":           title_tks,
                "title_sm_tks":        title_tks,
                "content_with_weight": content,
                "content_ltks":        content_ltks,
                "content_sm_ltks":     content_sm_ltks,
                "page_num_int":        [page_idx + 1],
                "position_int":        position_int,
                "top_int":             [1],
                "create_time":         current_time,
                "create_timestamp_flt": current_timestamp,
                "img_id":              chunk.get("img_id", ""),
            }
            enriched_chunks.append(enriched_chunk)

        logger.info(
            f"[Parser-INFO] perform_parse 完成: {len(enriched_chunks)} 个 chunks | "
            f"doc_id={doc_id} | doc_name={doc_name}"
        )
        return enriched_chunks

    def process_document(
        self,
        file_path: str,
        file_id: str,
        kb_id: str,
        tenant_id: str = "",
        options: Dict[str, Any] = None,
        progress_callback: Callable[[int], None] = None,
    ) -> Dict[str, Any]:
        if not SERVICES_AVAILABLE:
            raise RuntimeError("服务未正确初始化，请检查依赖")

        parse_result = self.parser.parse(file_path, options, progress_callback)

        raw_chunks = parse_result.get("chunks", [])
        doc_name = os.path.splitext(os.path.basename(file_path))[0]

        chunks = self.perform_parse(raw_chunks, file_id, kb_id, doc_name)

        embeddings = None
        vector_dim = config.embedding.DIMENSIONS

        if chunks and self.embedding:
            texts = [c.get("content_with_weight", "") for c in chunks]
            embeddings = self.embedding.encode(texts)
            if embeddings and embeddings[0]:
                vector_dim = len(embeddings[0])

        if chunks and self.chromadb and file_id and kb_id and tenant_id:
            self.chromadb.add_chunks(
                tenant_id=tenant_id,
                doc_id=file_id,
                kb_id=kb_id,
                chunks=chunks,
                embeddings=embeddings,
                vector_dim=vector_dim,
            )

        if chunks and self.mysql and file_id and kb_id:
            self.mysql.save_chunks(file_id, kb_id, chunks)
            image_info_list = parse_result.get("images", [])
            if image_info_list:
                self.mysql.save_images(file_id, kb_id, image_info_list)

        if self.mysql and file_id:
            meta = parse_result.get("metadata", {})
            self.mysql.update_document_status(
                doc_id=file_id,
                status="completed",
                total_pages=meta.get("pages", 0),
                total_chunks=len(chunks),
                text_length=meta.get("word_count", 0),
                image_count=meta.get("image_count", 0),
                parser=meta.get("parser", "unknown"),
            )

        if self.mysql and kb_id and file_id:
            self.mysql.update_kb_document_status(kb_id, file_id, "completed", 100)

        if self.mysql and kb_id:
            self.mysql.refresh_kb_statistics(kb_id)

        return parse_result
