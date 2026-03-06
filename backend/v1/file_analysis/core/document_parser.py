import os
import re
import json
import time
import subprocess
import tempfile
import uuid
from typing import Dict, Any, Callable, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

os.environ["TEMP"] = r"D:\pengpengRAG\backend/v1/file_analysis\temp"
os.environ["TMP"] = r"D:\pengpengRAG\backend/v1/file_analysis\temp"

os.environ['MINERU_TOOLS_CONFIG_JSON'] = r'D:\pengpengRAG\backend\v1\file_analysis\mineru.json'
os.environ['MINERU_MODEL_SOURCE'] = 'local'
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

PLAIN_CHUNK_SIZE   = 500
PLAIN_OVERLAP_SIZE = 50

_PLAIN_TEXT_EXTS = {".md"}
_OFFICE_EXTS = {".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt"}

# 本地文件存储路径配置（暂时替代MinIO）
LOCAL_STORAGE_ROOT = r"D:\pengpengRAG\backend\v1\file_analysis\uploads"
LOCAL_IMAGE_DIR = os.path.join(LOCAL_STORAGE_ROOT, "image-minIO")
IMAGE_URL_PREFIX = "http://localhost:8000/uploads/image-minIO"


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
    middle_content: Any          # str（PlainText）或 dict（MinerU）
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


def _content_list_to_chunks(
    content_list: List[Dict[str, Any]],
    doc_name: str = "",
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

        content_tks = _tokenize(content)
        chunks.append({
            "content":         content,
            "content_ltks":    content_tks,
            "content_sm_ltks": content_tks,
            "title_tks":       title_tks,
            "title_sm_tks":    title_tks,
            "type":            chunk_type,
            "page_idx":        item.get("page_idx", 0),
            "bbox":            item.get("bbox", [0, 0, 0, 0]),
            "img_id":          "",
        })

    return chunks


def _slice_with_overlap(lines: List[str]) -> List[str]:
    result: List[str] = []
    step  = max(1, PLAIN_CHUNK_SIZE - PLAIN_OVERLAP_SIZE)
    total = len(lines)
    start = 0

    while start < total:
        end   = min(start + PLAIN_CHUNK_SIZE, total)
        chunk = "\n".join(lines[start:end]).strip()
        if chunk:
            result.append(chunk)
        if end >= total:
            break
        start += step

    return result


class BaseParser(ABC):
    @abstractmethod
    def parse(
        self,
        file_path: str,
        options: Dict[str, Any] = None,
        progress_callback: Callable[[int], None] = None,
    ) -> ParseResult:
        pass


class PlainTextParser(BaseParser):
    def parse(
        self,
        file_path: str,
        options: Dict[str, Any] = None,
        progress_callback: Callable[[int], None] = None,
    ) -> ParseResult:

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        start_time = time.time()
        ext = os.path.splitext(file_path)[1].lower()

        if progress_callback:
            progress_callback(10)

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read()

        if progress_callback:
            progress_callback(30)

        if ext == ".md":
            content_list = self._split_md(raw_text)
        else:
            content_list = self._split_txt(raw_text)

        logger.info(
            f"[PlainParser-INFO] {ext} 直接切分完成，共 {len(content_list)} 个块"
            f"（CHUNK_SIZE={PLAIN_CHUNK_SIZE}, OVERLAP={PLAIN_OVERLAP_SIZE}）"
        )

        if progress_callback:
            progress_callback(70)

        plain_text      = self._to_plain_text(raw_text)
        standardized_md = raw_text
        middle_content  = self._generate_middle_content(standardized_md)
        doc_name        = os.path.splitext(os.path.basename(file_path))[0]
        chunks          = _content_list_to_chunks(content_list, doc_name=doc_name)
        processing_time = time.time() - start_time

        if progress_callback:
            progress_callback(100)

        return ParseResult(
            text=plain_text,
            markdown=standardized_md,
            middle_content=middle_content,
            metadata=DocumentMetadata(
                title=doc_name,
                pages=0,
                word_count=len(raw_text),
                file_type=ext,
                processing_time=processing_time,
            ),
            chunks=chunks,
            raw_output={},
        )

    def _split_md(self, markdown: str) -> List[Dict[str, Any]]:
        content_list: List[Dict[str, Any]] = []
        lines = markdown.split("\n")
        buffer: List[str] = []
        in_table = False
        table_lines: List[str] = []
        in_code = False
        code_lines: List[str] = []
        para_segments: List[str] = []

        def flush_buffer():
            text = "\n".join(buffer).strip()
            text = re.sub(r"[!#\\$/]", "", text).strip()
            if text:
                para_segments.append(text)
            buffer.clear()

        def flush_table():
            caption = []
            if para_segments:
                caption = [para_segments.pop()]
            table_body = "\n".join(table_lines).strip()
            if table_body:
                content_list.append({
                    "type": "table",
                    "table_caption": caption,
                    "table_body": table_body,
                })
            table_lines.clear()

        def flush_para_segments():
            if not para_segments:
                return
            all_lines: List[str] = []
            for seg in para_segments:
                all_lines.extend(seg.split("\n"))
                all_lines.append("")
            for chunk_text in _slice_with_overlap(all_lines):
                if chunk_text.strip():
                    content_list.append({"type": "text", "text": chunk_text})
            para_segments.clear()

        def is_table_row(line: str) -> bool:
            return bool(re.match(r"^\s*\|.*\|\s*$", line))

        i = 0
        while i < len(lines):
            line = lines[i]

            if line.strip().startswith("```"):
                if not in_code:
                    flush_buffer()
                    in_code = True
                    code_lines = [line]
                else:
                    code_lines.append(line)
                    in_code = False
                    flush_para_segments()
                    content_list.append({"type": "text", "text": "\n".join(code_lines)})
                    code_lines.clear()
                i += 1
                continue

            if in_code:
                code_lines.append(line)
                i += 1
                continue

            if line.strip().startswith("$$"):
                flush_buffer()
                eq_lines = [line]
                if not line.strip().endswith("$$") or len(line.strip()) == 2:
                    i += 1
                    while i < len(lines):
                        eq_lines.append(lines[i])
                        if lines[i].strip().endswith("$$"):
                            break
                        i += 1
                eq_text = "\n".join(eq_lines).strip()
                if eq_text:
                    flush_para_segments()
                    content_list.append({"type": "equation", "text": eq_text})
                i += 1
                continue

            if is_table_row(line):
                if not in_table:
                    flush_buffer()
                    in_table = True
                table_lines.append(line)
                i += 1
                continue
            else:
                if in_table:
                    flush_para_segments()
                    flush_table()
                    in_table = False

            if line.strip() == "":
                if buffer:
                    flush_buffer()
            else:
                buffer.append(line)

            i += 1

        if in_code and code_lines:
            flush_para_segments()
            content_list.append({"type": "text", "text": "\n".join(code_lines)})
        if in_table and table_lines:
            flush_para_segments()
            flush_table()
        if buffer:
            flush_buffer()
        flush_para_segments()

        return content_list

    def _split_txt(self, text: str) -> List[Dict[str, Any]]:
        lines = text.split("\n")
        content_list = []
        for chunk_text in _slice_with_overlap(lines):
            if chunk_text.strip():
                content_list.append({"type": "text", "text": chunk_text})
        return content_list

    def _to_plain_text(self, text: str) -> str:
        t = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        t = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', t)
        t = re.sub(r'[#*`]', '', t)
        t = re.sub(r'\n+', '\n', t)
        return t.strip()

    def _generate_middle_content(self, markdown: str) -> str:
        sections = ["<document>"]
        title_match = re.search(r'^#\s+(.+)$', markdown, re.MULTILINE)
        if title_match:
            sections.append(f"<title>{title_match.group(1).strip()}</title>")
        sections.append("<content>")
        sections.append(markdown)
        sections.append("</content>")
        sections.append("</document>")
        return "\n".join(sections)


class MinerUParser(BaseParser):

    def parse(
        self,
        file_path: str,
        options: Dict[str, Any] = None,
        progress_callback: Callable[[int], None] = None,
    ) -> ParseResult:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext in _PLAIN_TEXT_EXTS:
            logger.info(f"[Parser-INFO] 检测到 {ext} 文件，使用直接切分模式（跳过 MinerU）")
            return PlainTextParser().parse(file_path, options, progress_callback)

        if ext in _OFFICE_EXTS:
            logger.info(f"[Parser-INFO] 检测到 {ext} 文件，使用 LibreOffice 转换为 PDF")
            file_path = self._convert_to_pdf(file_path)
            if not file_path:
                raise ValueError(f"Failed to convert {ext} to PDF")
            ext = ".pdf"

        opts       = options or {}
        start_time = time.time()

        if progress_callback:
            progress_callback(10)

        result = self._parse_local(file_path, opts, progress_callback)
        processing_time = time.time() - start_time

        if progress_callback:
            progress_callback(80)

        final_result = self._process_result_from_local(result, file_path, processing_time)

        if progress_callback:
            progress_callback(100)

        return final_result

    def _parse_local(
        self,
        file_path: str,
        options: Dict[str, Any],
        progress_callback: Callable[[int], None] = None,
    ) -> Dict[str, Any]:
        """直接调用 mineru 源码进行解析"""
        from mineru.cli.common import do_parse

        output_dir    = tempfile.mkdtemp(prefix="mineru_")
        pdf_file_name = Path(file_path).stem
        pdf_bytes     = Path(file_path).read_bytes()

        backend        = options.get("backend",        "pipeline")
        parse_method   = options.get("parse_method",   "auto")
        formula_enable = options.get("formula_enable", True)
        table_enable   = options.get("table_enable",   True)

        logger.info(
            f"[Parser-INFO] 使用本地 MinerU 解析: {file_path}, "
            f"backend={backend}, parse_method={parse_method}"
        )

        try:
            do_parse(
                output_dir=output_dir,
                pdf_file_names=[pdf_file_name],
                pdf_bytes_list=[pdf_bytes],
                p_lang_list=["ch"],
                backend=backend,
                parse_method=parse_method,
                formula_enable=formula_enable,
                table_enable=table_enable,
                f_draw_layout_bbox=False,
                f_draw_span_bbox=False,
                f_dump_md=True,
                f_dump_middle_json=True,
                f_dump_content_list=True,
                f_dump_model_output=False,
                f_dump_orig_pdf=False,
            )
        except Exception as e:
            logger.error(f"[Parser-ERROR] MinerU 本地解析失败: {e}")
            raise

        if progress_callback:
            progress_callback(50)

        return {
            "output_dir":   output_dir,
            "file_name":    pdf_file_name,
            "parse_method": parse_method,
        }

    def _process_result_from_local(
        self,
        local_result: Dict[str, Any],
        file_path: str,
        processing_time: float,
    ) -> ParseResult:
        """处理本地 MinerU 解析结果"""
        output_dir   = local_result["output_dir"]
        file_name    = local_result["file_name"]
        parse_method = local_result.get("parse_method", "auto")

        # MinerU 实际输出路径是 output_dir/{file_name}/{parse_method}/
        result_dir = os.path.join(output_dir, file_name, parse_method)

        if not os.path.exists(result_dir):
            actual_files = []
            for root, _, files in os.walk(output_dir):
                for f in files:
                    actual_files.append(os.path.join(root, f))
            logger.error(
                f"[Parser-ERROR] 预期输出目录不存在: {result_dir}\n"
                f"实际生成的文件: {actual_files}"
            )
            raise FileNotFoundError(f"MinerU 输出目录不存在: {result_dir}")

        md_path           = os.path.join(result_dir, f"{file_name}.md")
        content_list_path = os.path.join(result_dir, f"{file_name}_content_list.json")
        middle_json_path  = os.path.join(result_dir, f"{file_name}_middle.json")

        markdown_content = ""
        if os.path.exists(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                markdown_content = f.read()
        else:
            logger.warning(f"[Parser-WARNING] markdown 文件不存在: {md_path}")

        content_list = []
        if os.path.exists(content_list_path):
            try:
                with open(content_list_path, "r", encoding="utf-8") as f:
                    content_list = json.load(f)
                logger.info(f"[Parser-INFO] 从 content_list.json 加载 {len(content_list)} 个块")
            except Exception as e:
                logger.warning(f"[Parser-WARNING] 读取 content_list 失败: {e}")

        middle_content: Any = {}
        if os.path.exists(middle_json_path):
            try:
                with open(middle_json_path, "r", encoding="utf-8") as f:
                    middle_content = json.load(f)
            except Exception as e:
                logger.warning(f"[Parser-WARNING] 读取 middle_json 失败: {e}")

        standardized_md = self._standardize_markdown(markdown_content)
        plain_text      = self._markdown_to_text(standardized_md)
        metadata        = self._extract_metadata_from_local(
            file_path, markdown_content, processing_time, content_list
        )
        doc_name = os.path.splitext(os.path.basename(file_path))[0]
        chunks   = _content_list_to_chunks(content_list, doc_name=doc_name)

        return ParseResult(
            text=plain_text,
            markdown=standardized_md,
            middle_content=middle_content,
            metadata=metadata,
            chunks=chunks,
            raw_output={"content_list": content_list, "middle_content": middle_content},
        )

    def _extract_metadata_from_local(
        self,
        file_path: str,
        markdown_content: str,
        processing_time: float,
        content_list: List[Dict],
    ) -> DocumentMetadata:
        """从本地解析结果提取元数据"""
        pages  = set()
        images = set()
        for item in content_list:
            if "page_idx" in item:
                pages.add(item["page_idx"])
            if item.get("type") == "image" and item.get("img_url"):
                images.add(item["img_url"])

        title_match = re.search(r'^#\s+(.+)$', markdown_content, re.MULTILINE)
        title = (
            title_match.group(1).strip()
            if title_match
            else os.path.splitext(os.path.basename(file_path))[0]
        )

        return DocumentMetadata(
            title=title,
            author="",
            pages=len(pages),
            word_count=len(markdown_content.replace("\n", "").replace(" ", "")),
            file_type=os.path.splitext(file_path)[1].lower(),
            has_images=bool(images),
            has_tables=any(i.get("type") == "table"    for i in content_list),
            has_formulas=any(i.get("type") == "equation" for i in content_list),
            processing_time=processing_time,
        )

    def _convert_to_pdf(self, file_path: str) -> Optional[str]:
        """使用 LibreOffice 将 Office 文档转换为 PDF"""
        try:
            cmd = [
                "soffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", tempfile.gettempdir(),
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                logger.error(f"LibreOffice conversion failed: {result.stderr}")
                return None

            base_name = os.path.splitext(os.path.basename(file_path))[0]
            pdf_path  = os.path.join(tempfile.gettempdir(), f"{base_name}.pdf")

            if os.path.exists(pdf_path):
                logger.info(f"Converted to PDF: {pdf_path}")
                return pdf_path
            else:
                logger.error(f"PDF file not found after conversion: {pdf_path}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("LibreOffice conversion timeout")
            return None
        except Exception as e:
            logger.error(f"LibreOffice conversion error: {e}")
            return None

    def _markdown_to_text(self, markdown: str) -> str:
        text = re.sub(r'!\[.*?\]\(.*?\)', '', markdown)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'[#*`]', '', text)
        text = re.sub(r'\n+', '\n', text)
        return text.strip()

    def _standardize_markdown(self, markdown: str) -> str:
        md = markdown
        md = re.sub(r'^\s*#\s+',   '# ',   md, flags=re.MULTILINE)
        md = re.sub(r'^\s*##\s+',  '## ',  md, flags=re.MULTILINE)
        md = re.sub(r'^\s*###\s+', '### ', md, flags=re.MULTILINE)
        md = re.sub(r'\n{3,}', '\n\n', md)
        md = re.sub(r'\|\s*-\s*\|', '| --- |', md)
        return md.strip()


class DocumentParser:
    def __init__(self):
        self.mineru_parser = MinerUParser()
        self._ensure_image_directory()

    def _ensure_image_directory(self):
        try:
            Path(LOCAL_IMAGE_DIR).mkdir(parents=True, exist_ok=True)
            logger.info(f"[Parser-INFO] 图片存储目录已创建/已存在: {LOCAL_IMAGE_DIR}")
        except Exception as e:
            logger.error(f"[Parser-ERROR] 创建图片目录失败: {e}")

    def _upload_image_local(self, img_path_src: str) -> Optional[Dict[str, str]]:
        """将图片复制到本地存储目录"""
        if not os.path.exists(img_path_src):
            logger.warning(f"[Parser-WARNING] 图片文件不存在: {img_path_src}")
            return None

        try:
            import shutil
            img_id       = _generate_uuid()
            img_ext      = os.path.splitext(img_path_src)[1]
            img_filename = f"{img_id}{img_ext}"
            img_path_dst = os.path.join(LOCAL_IMAGE_DIR, img_filename)

            shutil.copy2(img_path_src, img_path_dst)
            img_url = f"{IMAGE_URL_PREFIX}/{img_filename}"

            logger.info(f"[Parser-INFO] 图片处理完成 - ID: {img_id}, URL: {img_url}")
            return {
                "img_id":         img_id,
                "img_url":        img_url,
                "img_path_local": img_path_dst,
            }

        except Exception as e:
            logger.error(f"[Parser-ERROR] 上传图片失败: {e}")
            return None

    def _associate_images_with_chunks(
        self,
        chunks: List[Dict[str, Any]],
        image_info_list: List[Dict[str, Any]],
    ) -> None:
        """将图片关联到最近的文本块"""
        if not image_info_list:
            return

        for chunk_idx, chunk in enumerate(chunks):
            if chunk["type"] not in ("text", "table"):
                continue

            nearest_image = None
            min_distance  = float('inf')

            for img_info in image_info_list:
                distance = abs(chunk_idx - img_info.get("position", 0))
                if distance < 5 and distance < min_distance:
                    nearest_image = img_info
                    min_distance  = distance

            if nearest_image:
                chunk["img_id"] = nearest_image["img_id"]
                logger.info(
                    f"[Parser-INFO] 关联图片到块 {chunk_idx}: "
                    f"img_id={nearest_image['img_id']}, distance={min_distance}"
                )

    def parse(
        self,
        file_path: str,
        options: Dict[str, Any] = None,
        progress_callback: Callable[[int], None] = None,
    ) -> Dict[str, Any]:
        result = self.mineru_parser.parse(file_path, options, progress_callback)

        image_count = sum(1 for chunk in result.chunks if chunk.get("type") == "image")

        return {
            "text":           result.text,
            "markdown":       result.markdown,
            "middle_content": result.middle_content,
            "chunks":         result.chunks,
            "images":         [],
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
                "parser":          "plain_text" if result.raw_output == {} else "mineru_local",
                "image_count":     image_count,
            },
        }


class DocumentProcessor:
    def __init__(self):
        self.parser    = DocumentParser()
        self.chromadb  = ChromaDBService() if SERVICES_AVAILABLE else None
        self.embedding = EmbeddingService() if SERVICES_AVAILABLE else None
        self.mysql     = MySQLService()     if SERVICES_AVAILABLE else None

    def process_document(
        self,
        file_path: str,
        file_id: str,
        kb_id: str,
        options: Dict[str, Any] = None,
        progress_callback: Callable[[int], None] = None,
    ) -> Dict[str, Any]:
        if not SERVICES_AVAILABLE:
            raise RuntimeError("服务未正确初始化，请检查依赖")

        parse_result = self.parser.parse(file_path, options, progress_callback)

        chunks     = parse_result.get('chunks', [])
        embeddings = None

        if chunks and self.embedding:
            texts      = [c.get('content', c.get('text', '')) for c in chunks]
            embeddings = self.embedding.encode(texts)

        if chunks and self.chromadb and file_id and kb_id:
            self.chromadb.add_chunks(file_id, kb_id, chunks, embeddings)

        if chunks and self.mysql and file_id and kb_id:
            self.mysql.save_chunks(file_id, kb_id, chunks)

        if self.mysql and file_id:
            meta = parse_result.get('metadata', {})
            self.mysql.update_document_status(
                doc_id=file_id,
                status="completed",
                total_pages=meta.get('pages', 0),
                total_chunks=len(chunks),
                text_length=meta.get('word_count', 0),
                image_count=meta.get('image_count', 0),
                parser=meta.get('parser', 'unknown')
            )

        if self.mysql and kb_id and file_id:
            self.mysql.update_kb_document_status(kb_id, file_id, 'completed', 100)

        return parse_result