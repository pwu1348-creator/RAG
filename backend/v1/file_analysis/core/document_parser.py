import os
import re
import json
import shutil
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

from mineru.cli.common import read_fn, convert_pdf_bytes_to_bytes_by_pypdfium2
from mineru.utils.engine_utils import get_vlm_engine
from mineru.utils.enum_class import MakeMode
from mineru.utils.model_utils import clean_memory
from mineru.data.data_reader_writer import FileBasedDataWriter
from mineru.backend.pipeline.pipeline_analyze import doc_analyze as pipeline_doc_analyze
from mineru.backend.pipeline.model_json_to_middle_json import result_to_middle_json as pipeline_result_to_middle_json
from mineru.backend.pipeline.pipeline_middle_json_mkcontent import union_make as pipeline_union_make
from mineru.backend.vlm.vlm_analyze import doc_analyze as vlm_doc_analyze
from mineru.backend.vlm.vlm_middle_json_mkcontent import union_make as vlm_union_make
from mineru.backend.hybrid.hybrid_analyze import doc_analyze as hybrid_doc_analyze

try:
    from services.chromadb_service import ChromaDBService
    from services.embedding_service import EmbeddingService
    from services.mysql_service import MySQLService
    SERVICES_AVAILABLE = True
except ImportError as e:
    SERVICES_AVAILABLE = False
    logger.warning(f"[Parser-WARNING] 部分服务不可用: {e}")

_tokenizer = RagTokenizer()

# 本地文件存储路径配置（暂时替代MinIO）
LOCAL_STORAGE_ROOT = r"D:\pengpengRAG\backend\v1\file_analysis\uploads"
LOCAL_IMAGE_DIR = os.path.join(LOCAL_STORAGE_ROOT, "image-minIO")
IMAGE_URL_PREFIX = "http://localhost:8000/uploads/image-minIO"

# Office 类文件扩展名，需要先用 LibreOffice 转 PDF
_OFFICE_EXTS = {".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".md", ".html"}


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
    """将 MinerU content_list 转换为内部 chunk 格式"""
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
            # image 等类型跳过，由上层单独处理
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


# ---------------------------------------------------------------------------
# MinerU 底层引擎调用（对齐第二个文件的风格）
# ---------------------------------------------------------------------------

def _parse_by_pipeline(file_path: str, temp_image_dir: str) -> tuple:
    """使用 pipeline 引擎解析 PDF"""
    logger.info("[Parser-INFO] 使用 pipeline 引擎")
    pdf_bytes = read_fn(file_path)
    pdf_bytes = [convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes)]

    infer_results, all_image_lists, all_pdf_docs, lang_list, ocr_enabled_list = pipeline_doc_analyze(
        pdf_bytes, ["ch"]
    )
    if not infer_results:
        return {}, []

    image_writer = FileBasedDataWriter(temp_image_dir)
    middle_json = pipeline_result_to_middle_json(
        infer_results[0], all_image_lists[0], all_pdf_docs[0],
        image_writer, lang_list[0], ocr_enabled_list[0],
        formula_enable=True,
    )
    image_dir    = os.path.basename(temp_image_dir)
    content_list = pipeline_union_make(middle_json["pdf_info"], MakeMode.CONTENT_LIST, image_dir)
    return middle_json, content_list


def _parse_by_vlm(file_path: str, temp_image_dir: str) -> tuple:
    """使用 VLM 引擎解析 PDF"""
    logger.info("[Parser-INFO] 使用 vlm 引擎")
    backend   = get_vlm_engine(inference_engine="transformers", is_async=False)
    pdf_bytes = read_fn(file_path)
    pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes, 0, None)

    image_writer = FileBasedDataWriter(temp_image_dir)
    middle_json, _ = vlm_doc_analyze(
        pdf_bytes, image_writer=image_writer, backend=backend,
        server_url=None, gpu_memory_utilization=0.4,
    )
    image_dir    = os.path.basename(temp_image_dir)
    content_list = vlm_union_make(middle_json["pdf_info"], MakeMode.CONTENT_LIST, image_dir)
    return middle_json, content_list


def _parse_by_hybrid(file_path: str, temp_image_dir: str) -> tuple:
    """使用 hybrid 引擎解析 PDF"""
    logger.info("[Parser-INFO] 使用 hybrid 引擎")
    backend   = get_vlm_engine(inference_engine="transformers", is_async=False)
    pdf_bytes = read_fn(file_path)
    pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes, 0, None)

    image_writer = FileBasedDataWriter(temp_image_dir)
    middle_json, _, _ = hybrid_doc_analyze(
        pdf_bytes,
        image_writer=image_writer,
        backend=backend,
        parse_method="hybrid_auto",
        language="ch",
        inline_formula_enable=True,
        server_url=None,
        gpu_memory_utilization=0.4,
    )
    image_dir    = os.path.basename(temp_image_dir)
    content_list = vlm_union_make(middle_json["pdf_info"], MakeMode.CONTENT_LIST, image_dir)
    return middle_json, content_list


def _parse_pdf(file_path: str, temp_image_dir: str) -> tuple:
    """根据环境变量选择引擎，统一入口"""
    engine = os.getenv("MINERU_PARSE_ENGINE", "pipeline")
    if engine == "vlm":
        return _parse_by_vlm(file_path, temp_image_dir)
    elif engine == "hybrid":
        return _parse_by_hybrid(file_path, temp_image_dir)
    else:
        return _parse_by_pipeline(file_path, temp_image_dir)


def _convert_to_pdf_with_libreoffice(file_path: str, out_dir: str) -> str:
    """使用 LibreOffice 将 Office/文本文件转换为 PDF，返回 PDF 路径"""
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


# ---------------------------------------------------------------------------
# 解析器主类
# ---------------------------------------------------------------------------

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
    """
    统一走 MinerU 底层引擎解析。
    - PDF  → 直接调用底层引擎
    - 其余 → LibreOffice 转 PDF → 再调用底层引擎
    """

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
            # Office / 文本类先转 PDF
            if ext in _OFFICE_EXTS:
                logger.info(f"[Parser-INFO] {ext} 文件先用 LibreOffice 转为 PDF")
                pdf_path = _convert_to_pdf_with_libreoffice(file_path, temp_dir)
            else:
                pdf_path = file_path

            if progress_callback:
                progress_callback(30)

            middle_json, content_list = _parse_pdf(pdf_path, temp_image_dir)

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

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    def _extract_metadata(
        self,
        file_path: str,
        middle_json: dict,
        content_list: List[Dict],
        processing_time: float,
    ) -> DocumentMetadata:
        pages  = {item["page_idx"] for item in content_list if "page_idx" in item}
        images = {item.get("img_path") for item in content_list if item.get("type") == "image" and item.get("img_path")}

        # 尝试从 content_list 的第一个文本块提取标题
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
        """从 middle_json 拼出纯文本，供上层使用"""
        lines = []
        for page in middle_json.get("pdf_info", []):
            for block in page.get("preproc_blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("content", "").strip()
                        if text:
                            lines.append(text)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# DocumentParser：组合 MinerUParser + 图片本地存储
# ---------------------------------------------------------------------------

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
        """将图片复制到本地存储目录，返回 img_id / img_url"""
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
        """
        遍历 content_list 中的 image 条目，上传到本地，
        然后按位置关联到最近的文本块（distance < 5）。
        返回 image_info_list。
        """
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

        # 关联到最近的文本/表格块
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

        # 取出解析时产生的临时图片目录（存在 raw_output 里）
        temp_image_dir = options.get("temp_image_dir", "") if options else ""
        image_info_list = []
        if temp_image_dir and os.path.isdir(temp_image_dir):
            content_list    = result.raw_output.get("content_list", [])
            image_info_list = self._process_images(content_list, temp_image_dir, result.chunks)

        image_count = len(image_info_list)

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


# ---------------------------------------------------------------------------
# DocumentProcessor：解析 + 向量化 + 存储
# ---------------------------------------------------------------------------

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

        chunks     = parse_result.get("chunks", [])
        embeddings = None

        if chunks and self.embedding:
            texts      = [c.get("content", c.get("text", "")) for c in chunks]
            embeddings = self.embedding.encode(texts)

        if chunks and self.chromadb and file_id and kb_id:
            self.chromadb.add_chunks(file_id, kb_id, chunks, embeddings)

        if chunks and self.mysql and file_id and kb_id:
            self.mysql.save_chunks(file_id, kb_id, chunks)
            # 保存图片元数据
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

        return parse_result