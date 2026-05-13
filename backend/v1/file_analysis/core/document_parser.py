import os
import re
import json
import shutil
import time
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Callable, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

os.environ["TEMP"] = os.path.join(_BASE_DIR, "temp")
os.environ["TMP"] = os.path.join(_BASE_DIR, "temp")

# 动态生成 mineru.json，确保路径在任何机器上都正确
_models_base = os.path.join(_BASE_DIR, 'models', 'models--opendatalab--PDF-Extract-Kit-1.0')
_ref_path = os.path.join(_models_base, 'refs', 'main')
_snapshot = open(_ref_path).read().strip() if os.path.exists(_ref_path) else 'd1336ee3c2975a8b26c4b09ff39dc6b593d34141'
_snapshot_dir = os.path.join(_models_base, 'snapshots', _snapshot)
_mineru_config = {
    'models-dir': {
        'pipeline': _snapshot_dir
    }
}
_mineru_config_path = os.path.join(_BASE_DIR, 'mineru.json')
with open(_mineru_config_path, 'w', encoding='utf-8') as _f:
    json.dump(_mineru_config, _f, ensure_ascii=False, indent=2)

os.environ['MINERU_TOOLS_CONFIG_JSON'] = _mineru_config_path
os.environ['MINERU_MODEL_SOURCE'] = 'local'
os.environ['HF_HUB_CACHE'] = os.path.join(_BASE_DIR, 'models')

from config import config
from utils.logger import logger
from utils.rag_tokenizer import RagTokenizer

from mineru.cli.common import read_fn, convert_pdf_bytes_to_bytes
from mineru.utils.enum_class import MakeMode
from mineru.utils.model_utils import clean_memory
from mineru.data.data_reader_writer import FileBasedDataWriter
from mineru.backend.pipeline.pipeline_analyze import doc_analyze_streaming as pipeline_doc_analyze_streaming
from mineru.backend.pipeline.pipeline_middle_json_mkcontent import union_make as pipeline_union_make
from mineru.backend.vlm.vlm_analyze import doc_analyze as vlm_doc_analyze
from mineru.backend.vlm.vlm_middle_json_mkcontent import union_make as vlm_union_make
from mineru.backend.hybrid.hybrid_analyze import doc_analyze as hybrid_doc_analyze

# MinerU 原生 Office 解析（DOCX / PPTX / XLSX）
from mineru.backend.office.docx_analyze import office_docx_analyze
from mineru.backend.office.pptx_analyze import office_pptx_analyze
from mineru.backend.office.xlsx_analyze import office_xlsx_analyze
from mineru.backend.office.office_middle_json_mkcontent import union_make as office_union_make

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

# 原生支持的 Office 格式（MinerU 3.1+ 直接解析，无需 LibreOffice）
_NATIVE_OFFICE_EXTS = {".docx", ".pptx", ".xlsx"}
# 仍需 LibreOffice 转 PDF 的格式（旧格式 .doc/.ppt/.xls 及纯文本）
_LEGACY_OFFICE_EXTS = {".doc", ".ppt", ".xls", ".txt", ".md", ".html"}


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
    middle_content: Any          # dict（MinerU middle_json）
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





def _parse_by_pipeline(file_path: str, temp_image_dir: str) -> tuple:
    logger.info("[Parser-INFO] 使用 pipeline 引擎")
    pdf_bytes = read_fn(file_path)
    pdf_bytes_pages = convert_pdf_bytes_to_bytes(pdf_bytes)

    image_writer = FileBasedDataWriter(temp_image_dir)

    # 使用 streaming API，通过回调获取 middle_json
    result_holder = {}

    def on_doc_ready(doc_index, model_list, middle_json, ocr_enable):
        result_holder['middle_json'] = middle_json

    pipeline_doc_analyze_streaming(
        [pdf_bytes_pages],
        [image_writer],
        ["ch"],
        on_doc_ready,
        formula_enable=True,
        table_enable=True,
    )

    middle_json = result_holder.get('middle_json', {})
    if not middle_json:
        return {}, []

    image_dir    = os.path.basename(temp_image_dir)
    content_list = pipeline_union_make(middle_json["pdf_info"], MakeMode.CONTENT_LIST, image_dir)
    return middle_json, content_list


def _parse_by_vlm(file_path: str, temp_image_dir: str) -> tuple:
    logger.info("[Parser-INFO] 使用 vlm 引擎")
    pdf_bytes = read_fn(file_path)
    pdf_bytes_pages = convert_pdf_bytes_to_bytes(pdf_bytes)

    image_writer = FileBasedDataWriter(temp_image_dir)
    middle_json, _ = vlm_doc_analyze(
        pdf_bytes_pages,
        image_writer=image_writer,
        backend="transformers",
    )
    image_dir    = os.path.basename(temp_image_dir)
    content_list = vlm_union_make(middle_json["pdf_info"], MakeMode.CONTENT_LIST, image_dir)
    return middle_json, content_list


def _parse_by_hybrid(file_path: str, temp_image_dir: str) -> tuple:
    logger.info("[Parser-INFO] 使用 hybrid 引擎")
    pdf_bytes = read_fn(file_path)
    pdf_bytes_pages = convert_pdf_bytes_to_bytes(pdf_bytes)

    image_writer = FileBasedDataWriter(temp_image_dir)
    middle_json, _, _ = hybrid_doc_analyze(
        pdf_bytes_pages,
        image_writer=image_writer,
        backend="transformers",
        parse_method="auto",
        language="ch",
        inline_formula_enable=True,
    )
    image_dir    = os.path.basename(temp_image_dir)
    content_list = vlm_union_make(middle_json["pdf_info"], MakeMode.CONTENT_LIST, image_dir)
    return middle_json, content_list


def _parse_office_native(file_path: str, temp_image_dir: str) -> tuple:
    """使用 MinerU 3.1+ 原生 Office 解析（DOCX / PPTX / XLSX），无需 LibreOffice 转换。"""
    ext = os.path.splitext(file_path)[1].lower()
    logger.info(f"[Parser-INFO] 使用 MinerU 原生 Office 解析引擎: {ext}")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    image_writer = FileBasedDataWriter(temp_image_dir)

    if ext == ".docx":
        middle_json, _ = office_docx_analyze(file_bytes, image_writer=image_writer)
    elif ext == ".pptx":
        middle_json, _ = office_pptx_analyze(file_bytes, image_writer=image_writer)
    elif ext == ".xlsx":
        middle_json, _ = office_xlsx_analyze(file_bytes, image_writer=image_writer)
    else:
        raise ValueError(f"不支持的原生 Office 格式: {ext}")

    image_dir = os.path.basename(temp_image_dir)
    content_list = office_union_make(middle_json["pdf_info"], MakeMode.CONTENT_LIST, image_dir)
    return middle_json, content_list


SUPPORTED_ENGINES = ("pipeline", "vlm", "hybrid")


def _parse_pdf(file_path: str, temp_image_dir: str) -> tuple:
    engine = config.mineru.PARSE_ENGINE or os.getenv("MINERU_PARSE_ENGINE", "pipeline")
    engine = engine.lower().strip()
    logger.info(f"[Parser-INFO] 当前解析引擎: {engine}")

    if engine == "vlm":
        return _parse_by_vlm(file_path, temp_image_dir)
    elif engine == "hybrid":
        return _parse_by_hybrid(file_path, temp_image_dir)
    else:
        return _parse_by_pipeline(file_path, temp_image_dir)


def _convert_to_pdf_with_libreoffice(file_path: str, out_dir: str) -> str:
    cmd = [
        "soffice", "--headless", "--norestore", "--invisible",
        "--convert-to", "pdf",
        "--outdir", out_dir,
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice 转换失败: {result.stderr}")

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    pdf_path  = os.path.join(out_dir, f"{base_name}.pdf")
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"LibreOffice 转换后未找到 PDF: {pdf_path}")
    return pdf_path



class BaseParser(ABC):
    @abstractmethod
    def parse(
        self,
        file_path: str,
        options: Dict[str, Any] = None,
        progress_callback: Callable[[int], None] = None,
    ) -> ParseResult:
        pass


class MinerUParser(BaseParser):

    def parse(
        self,
        file_path: str,
        options: Dict[str, Any] = None,
        progress_callback: Callable[[int], None] = None,
    ) -> ParseResult:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        start_time = time.time()
        ext        = os.path.splitext(file_path)[1].lower()

        if progress_callback:
            progress_callback(10)

        temp_dir       = tempfile.mkdtemp(prefix="mineru_")
        temp_image_dir = os.path.join(temp_dir, "images")
        os.makedirs(temp_image_dir, exist_ok=True)

        try:
            if ext in _NATIVE_OFFICE_EXTS:
                # MinerU 3.1+ 原生解析 DOCX/PPTX/XLSX，无需 LibreOffice
                if progress_callback:
                    progress_callback(30)
                middle_json, content_list = _parse_office_native(file_path, temp_image_dir)
            elif ext in _LEGACY_OFFICE_EXTS:
                # 旧格式 .doc/.ppt/.xls 及纯文本仍需 LibreOffice 转 PDF
                logger.info(f"[Parser-INFO] {ext} 文件先用 LibreOffice 转为 PDF")
                pdf_path = _convert_to_pdf_with_libreoffice(file_path, temp_dir)
                if progress_callback:
                    progress_callback(30)
                middle_json, content_list = _parse_pdf(pdf_path, temp_image_dir)
            else:
                # PDF 直接解析
                if progress_callback:
                    progress_callback(30)
                middle_json, content_list = _parse_pdf(file_path, temp_image_dir)

            if progress_callback:
                progress_callback(70)

        except Exception as e:
            logger.error(f"[Parser-ERROR] 解析失败: {e}")
            raise

        processing_time = time.time() - start_time
        doc_name        = os.path.splitext(os.path.basename(file_path))[0]
        chunks          = _content_list_to_chunks(content_list, doc_name=doc_name)
        metadata        = self._extract_metadata(file_path, middle_json, content_list, processing_time)

        if progress_callback:
            progress_callback(100)

        return ParseResult(
            text=self._to_plain_text(middle_json),
            markdown="",          # 不再单独维护 markdown，middle_json 已足够
            middle_content=middle_json,
            metadata=metadata,
            chunks=chunks,
            raw_output={
                "content_list": content_list, 
                "middle_content": middle_json,
                "temp_image_dir": temp_image_dir,
            },
        )

    def _extract_metadata(
        self,
        file_path: str,
        middle_json: dict,
        content_list: List[Dict],
        processing_time: float,
    ) -> DocumentMetadata:
        pages  = {item["page_idx"] for item in content_list if "page_idx" in item}
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
            has_tables=any(i.get("type") == "table"    for i in content_list),
            has_formulas=any(i.get("type") == "equation" for i in content_list),
            processing_time=processing_time,
        )

    def _to_plain_text(self, middle_json: dict) -> str:
        """从 middle_json 提取纯文本，兼容 PDF pipeline 和 Office 原生解析两种结构。"""
        lines = []
        for page in middle_json.get("pdf_info", []):
            # PDF pipeline 结构: preproc_blocks -> lines -> spans
            for block in page.get("preproc_blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("content", "").strip()
                        if text:
                            lines.append(text)
            # Office 原生解析结构: para_blocks -> lines -> spans
            for block in page.get("para_blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("content", "").strip()
                        if text:
                            lines.append(text)
        return "\n".join(lines)



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

        # 清理临时目录
        _raw_temp_image_dir = result.raw_output.get('temp_image_dir', '')
        if _raw_temp_image_dir:
            _temp_dir = os.path.dirname(_raw_temp_image_dir)
            if os.path.isdir(_temp_dir):
                shutil.rmtree(_temp_dir, ignore_errors=True)

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
                "parser":          "mineru_local",
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

        # 支持通过 options 注入 chunk 合并函数（由 ParserService 提供）
        chunk_merger = (options or {}).get("chunk_merger")
        if callable(chunk_merger):
            raw_chunks = chunk_merger(raw_chunks)

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
