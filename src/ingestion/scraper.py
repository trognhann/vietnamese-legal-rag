"""
Vietnamese Legal Document Scraper
==================================
Tự động thu thập văn bản pháp luật từ các trang web pháp lý Việt Nam.

Tính năng:
- Hỗ trợ nhiều nguồn (vbpl.vn, thuvienphapluat.vn, ...)
- Tổ chức file theo domain và loại văn bản
- Xoay vòng User-Agent để tránh bị chặn
- Ghi log chi tiết ra file và terminal
- Chuẩn hóa tên file (bỏ dấu, khoảng trắng)
- Thống kê tải xuống cuối phiên
"""

import os
import re
import time
import random
import logging
import hashlib
import unicodedata
import urllib.parse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

# ─────────────────────────────────────────────
# Cấu hình đường dẫn
# ─────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data" / "1_raw" / "pdf"
LOG_DIR  = ROOT_DIR / "logs"
LOG_FILE = LOG_DIR / f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

console = Console()

# ─────────────────────────────────────────────
# Logging: vừa ra terminal (Rich), vừa ra file
# ─────────────────────────────────────────────
def setup_logging() -> logging.Logger:
    logger = logging.getLogger("vn_legal_scraper")
    logger.setLevel(logging.DEBUG)

    # File handler - lưu đầy đủ thông tin
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    # Console handler - dùng Rich
    ch = RichHandler(console=console, rich_tracebacks=True, show_path=False)
    ch.setLevel(logging.INFO)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

logger = setup_logging()

# ─────────────────────────────────────────────
# Danh sách User-Agent xoay vòng
# ─────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.52 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 OPR/110.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

# ─────────────────────────────────────────────
# Cấu hình nguồn dữ liệu
# ─────────────────────────────────────────────
@dataclass
class LegalSource:
    """Mô tả một nguồn văn bản pháp luật."""
    name: str                    # Tên hiển thị
    domain: str                  # Tên domain (dùng làm thư mục con)
    base_url: str                # URL trang danh sách
    pagination_pattern: str      # Pattern URL phân trang (dùng {page})
    max_pages: int = 5           # Số trang tối đa
    extra_headers: dict = field(default_factory=dict)

# Danh sách nguồn được hỗ trợ
LEGAL_SOURCES: list[LegalSource] = [
    LegalSource(
        name="Cơ sở dữ liệu Quốc gia về VBPL (vbpl.vn)",
        domain="vbpl",
        base_url="https://vbpl.vn/TW/Pages/vbpq-tim-kiem.aspx?type=0",
        pagination_pattern="https://vbpl.vn/TW/Pages/vbpq-tim-kiem.aspx?type=0&page={page}",
        max_pages=3,
        extra_headers={"Referer": "https://vbpl.vn/"},
    ),
    LegalSource(
        name="Thư viện Pháp luật (thuvienphapluat.vn)",
        domain="thuvienphapluat",
        base_url="https://thuvienphapluat.vn/archive/Luat/lID45.aspx",
        pagination_pattern="https://thuvienphapluat.vn/archive/Luat/lID45.aspx?page={page}",
        max_pages=3,
        extra_headers={"Referer": "https://thuvienphapluat.vn/"},
    ),
]

# ─────────────────────────────────────────────
# Ánh xạ từ khóa → danh mục văn bản
# ─────────────────────────────────────────────
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "luat":          ["luật", "luat", "law"],
    "nghi_dinh":     ["nghị định", "nghi dinh", "decree"],
    "thong_tu":      ["thông tư", "thong tu", "circular"],
    "quyet_dinh":    ["quyết định", "quyet dinh", "decision"],
    "chi_thi":       ["chỉ thị", "chi thi", "directive"],
    "nghi_quyet":    ["nghị quyết", "nghi quyet", "resolution"],
    "phap_lenh":     ["pháp lệnh", "phap lenh", "ordinance"],
    "hien_phap":     ["hiến pháp", "hien phap", "constitution"],
    "khac":          [],   # fallback
}

# ─────────────────────────────────────────────
# Thống kê phiên làm việc
# ─────────────────────────────────────────────
@dataclass
class SessionStats:
    total_found: int = 0
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    failed_urls: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# Các hàm tiện ích
# ═══════════════════════════════════════════════════════════════

# Bảng chuyển đổi ký tự đặc biệt không phân tích được qua NFKD
_SPECIAL_CHAR_MAP: dict[str, str] = {
    "đ": "d", "Đ": "D",
    "\u2019": "'", "\u2018": "'",   # smart quotes
    "\u201c": '"', "\u201d": '"',
}


def normalize_filename(text: str, extension: str = ".pdf") -> str:
    """
    Chuẩn hóa tên file:
    - Bỏ dấu tiếng Việt → ASCII (kể cả đ/Đ)
    - Lowercase, thay khoảng trắng bằng dấu gạch dưới
    - Xóa ký tự đặc biệt
    - Thêm đuôi file

    Ví dụ: "Luật Doanh nghiệp 2020" → "luat_doanh_nghiep_2020.pdf"
    """
    # Bước 0: Thay thế ký tự đặc biệt không xử lý được qua NFKD
    for src, dst in _SPECIAL_CHAR_MAP.items():
        text = text.replace(src, dst)
    # Bước 1: Chuẩn hóa Unicode → tách dấu
    text = unicodedata.normalize("NFKD", text)
    # Bước 2: Chỉ giữ ký tự ASCII (bỏ dấu)
    text = "".join(c for c in text if not unicodedata.combining(c))
    # Bước 3: Lowercase
    text = text.lower()
    # Bước 4: Thay dấu gạch ngang, khoảng trắng, dấu / bằng _
    text = re.sub(r"[\s\-–—/]+", "_", text)
    # Bước 5: Xóa ký tự không phải chữ/số/_
    text = re.sub(r"[^\w]", "", text)
    # Bước 6: Xóa nhiều _ liên tiếp
    text = re.sub(r"_+", "_", text).strip("_")
    # Bước 7: Giới hạn độ dài tên file
    if len(text) > 120:
        text = text[:120]
    return text + extension


def classify_document(text: str) -> str:
    """
    Phân loại văn bản theo tên/tiêu đề gốc (chứa tiếng Việt có dấu).
    Trả về key trong CATEGORY_KEYWORDS.
    """
    lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                return category
    return "khac"


def get_domain_from_url(url: str) -> str:
    """Lấy tên miền đơn giản từ URL."""
    parsed = urllib.parse.urlparse(url)
    # vd: "vbpl.vn" hoặc "thuvienphapluat.vn"
    return parsed.netloc.replace("www.", "")


def get_file_hash(filepath: Path) -> str:
    """Tính MD5 hash của file để kiểm tra trùng lặp."""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def random_delay(min_s: float = 2.0, max_s: float = 5.0):
    """Delay ngẫu nhiên để tránh bị chặn IP."""
    delay = random.uniform(min_s, max_s)
    logger.debug(f"⏱  Chờ {delay:.1f}s trước yêu cầu tiếp theo...")
    time.sleep(delay)


def build_session(source: LegalSource) -> requests.Session:
    """Tạo requests.Session với User-Agent ngẫu nhiên và headers phù hợp."""
    session = requests.Session()
    ua = random.choice(USER_AGENTS)
    session.headers.update({
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        **source.extra_headers,
    })
    logger.debug(f"🌐 User-Agent: {ua[:60]}...")
    return session


# ═══════════════════════════════════════════════════════════════
# Lớp trích xuất link tải file
# ═══════════════════════════════════════════════════════════════

class LinkExtractor:
    """Trích xuất các liên kết tải file PDF/DOC/DOCX từ trang HTML."""

    FILE_EXTENSIONS = {".pdf", ".doc", ".docx"}

    @classmethod
    def extract_from_html(cls, html: str, base_url: str) -> list[dict]:
        """
        Trả về danh sách dict:
        {
            "url": "https://...",
            "text": "Tên văn bản",
            "ext": ".pdf"
        }
        """
        soup = BeautifulSoup(html, "html.parser")
        found: list[dict] = []
        seen_urls: set[str] = set()

        for tag in soup.find_all("a", href=True):
            href: str = tag["href"].strip()
            if not href:
                continue

            # Giải mã URL tương đối
            full_url = urllib.parse.urljoin(base_url, href)

            # Kiểm tra đuôi file
            parsed_path = urllib.parse.urlparse(full_url).path.lower()
            ext = None
            for e in cls.FILE_EXTENSIONS:
                if parsed_path.endswith(e):
                    ext = e
                    break

            # Kiểm tra param "type" hoặc "download" thường gặp ở vbpl.vn
            if ext is None:
                if "download" in href.lower() or "filedownload" in href.lower():
                    ext = ".pdf"  # giả định PDF

            if ext is None:
                continue

            # Loại trùng
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            link_text = tag.get_text(separator=" ", strip=True) or "van_ban"
            found.append({"url": full_url, "text": link_text, "ext": ext})

        return found


# ═══════════════════════════════════════════════════════════════
# Lớp tải file
# ═══════════════════════════════════════════════════════════════

class FileDownloader:
    """Xử lý việc tải file về và lưu vào đúng thư mục."""

    def __init__(self, base_dir: Path, stats: SessionStats):
        self.base_dir = base_dir
        self.stats = stats
        self._existing_hashes: dict[str, Path] = {}  # hash → path

    def _get_target_dir(self, domain: str, doc_type: str) -> Path:
        """
        Tổ chức: data/1_raw/pdf/<domain>/<doc_type>/
        Ví dụ:   data/1_raw/pdf/vbpl/luat/
        """
        target = self.base_dir / domain / doc_type
        target.mkdir(parents=True, exist_ok=True)
        return target

    def _resolve_filename(self, link: dict, target_dir: Path) -> tuple[str, Path]:
        """Tạo tên file chuẩn hóa và đường dẫn đầy đủ."""
        raw_name = link["text"] or "van_ban"
        normalized = normalize_filename(raw_name, extension=link["ext"])
        filepath = target_dir / normalized

        # Xử lý trùng tên: thêm số thứ tự
        if filepath.exists():
            stem = filepath.stem
            for i in range(1, 1000):
                candidate = target_dir / f"{stem}_{i}{link['ext']}"
                if not candidate.exists():
                    filepath = candidate
                    break

        return normalized, filepath

    def download(
        self,
        link: dict,
        session: requests.Session,
        domain: str,
    ) -> bool:
        """
        Tải một file. Trả về True nếu thành công.
        """
        url = link["url"]
        text = link["text"]

        # Phân loại loại văn bản
        doc_type = classify_document(text)
        target_dir = self._get_target_dir(domain, doc_type)
        normalized_name, filepath = self._resolve_filename(link, target_dir)

        logger.info(f"⬇  Đang tải: [bold cyan]{text[:70]}[/bold cyan]")
        logger.debug(f"   URL: {url}")
        logger.debug(f"   Lưu vào: {filepath.relative_to(ROOT_DIR)}")

        try:
            # Xoay User-Agent cho mỗi lần tải
            session.headers["User-Agent"] = random.choice(USER_AGENTS)

            resp = session.get(url, timeout=30, stream=True)
            resp.raise_for_status()

            # Kiểm tra Content-Type
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" in content_type and link["ext"] != ".html":
                logger.warning(f"⚠  Bỏ qua (trả về HTML thay vì file): {url}")
                self.stats.skipped += 1
                return False

            # Tải và ghi file
            total_bytes = 0
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=16384):
                    if chunk:
                        f.write(chunk)
                        total_bytes += len(chunk)

            # Kiểm tra file hợp lệ (> 1KB)
            if total_bytes < 1024:
                logger.warning(f"⚠  File quá nhỏ ({total_bytes} bytes), có thể lỗi: {url}")
                filepath.unlink(missing_ok=True)
                self.stats.failed += 1
                self.stats.failed_urls.append(url)
                return False

            size_kb = total_bytes / 1024
            logger.info(
                f"✅ Thành công: [green]{normalized_name}[/green] "
                f"({size_kb:.1f} KB) → {doc_type}/"
            )
            self.stats.downloaded += 1
            return True

        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP Error {e.response.status_code}: {url}")
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Lỗi kết nối: {url}")
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout: {url}")
        except Exception as e:
            logger.error(f"❌ Lỗi không xác định: {e} | URL: {url}")

        self.stats.failed += 1
        self.stats.failed_urls.append(url)
        return False


# ═══════════════════════════════════════════════════════════════
# Lớp thu thập chính
# ═══════════════════════════════════════════════════════════════

class VietnamLegalScraper:
    """Crawler chính: duyệt qua nhiều nguồn, nhiều trang, tải file."""

    def __init__(self, sources: Optional[list[LegalSource]] = None):
        self.sources = sources or LEGAL_SOURCES
        self.stats = SessionStats()
        self.downloader = FileDownloader(DATA_DIR, self.stats)

    def _fetch_page(self, url: str, session: requests.Session) -> Optional[str]:
        """Lấy nội dung HTML của một trang."""
        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text
        except Exception as e:
            logger.error(f"❌ Không thể tải trang: {url} → {e}")
            return None

    def scrape_source(self, source: LegalSource):
        """Thu thập từ một nguồn dữ liệu."""
        console.rule(f"[bold blue]🔍 Nguồn: {source.name}")
        logger.info(f"Bắt đầu thu thập: {source.name} | Domain: {source.domain}")

        session = build_session(source)
        all_links: list[dict] = []

        # ─── Duyệt qua các trang ───
        for page_num in range(1, source.max_pages + 1):
            if page_num == 1:
                page_url = source.base_url
            else:
                page_url = source.pagination_pattern.format(page=page_num)

            logger.info(f"📄 Trang {page_num}/{source.max_pages}: {page_url}")
            html = self._fetch_page(page_url, session)

            if html is None:
                logger.warning(f"⚠  Bỏ qua trang {page_num} (không lấy được HTML)")
                continue

            links = LinkExtractor.extract_from_html(html, page_url)
            logger.info(f"   → Tìm thấy {len(links)} link tải file trên trang {page_num}")
            all_links.extend(links)

            if page_num < source.max_pages:
                random_delay(1.5, 3.5)

        # Loại trùng URL trên toàn bộ nguồn
        seen: set[str] = set()
        unique_links = []
        for lnk in all_links:
            if lnk["url"] not in seen:
                seen.add(lnk["url"])
                unique_links.append(lnk)

        self.stats.total_found += len(unique_links)
        logger.info(f"📋 Tổng: {len(unique_links)} file duy nhất cần tải từ {source.name}")

        # ─── Tải từng file ───
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(
                f"Đang tải từ {source.domain}...", total=len(unique_links)
            )

            for idx, link in enumerate(unique_links, start=1):
                progress.update(task, description=f"[{idx}/{len(unique_links)}] {link['text'][:50]}")

                # Xoay session theo từng file
                if idx % 5 == 0:
                    session = build_session(source)
                    logger.debug("🔄 Làm mới session & User-Agent")

                success = self.downloader.download(link, session, source.domain)
                progress.advance(task)

                # Delay chống bot
                if idx < len(unique_links):
                    random_delay(2.0, 5.0)

    def run(self):
        """Chạy toàn bộ quá trình thu thập."""
        start_time = datetime.now()
        console.print(Panel.fit(
            "[bold green]🇻🇳 Vietnamese Legal Document Scraper[/bold green]\n"
            f"[dim]Bắt đầu lúc: {start_time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n"
            f"[dim]Log file: {LOG_FILE}[/dim]",
            border_style="green"
        ))

        for source in self.sources:
            try:
                self.scrape_source(source)
            except KeyboardInterrupt:
                logger.warning("⛔ Người dùng dừng script!")
                break
            except Exception as e:
                logger.error(f"❌ Lỗi nghiêm trọng khi xử lý nguồn {source.name}: {e}")
                continue

        self._print_summary(start_time)

    def _print_summary(self, start_time: datetime):
        """In bảng thống kê kết quả."""
        elapsed = datetime.now() - start_time
        minutes, seconds = divmod(int(elapsed.total_seconds()), 60)

        table = Table(title="📊 Thống kê phiên tải xuống", border_style="cyan", show_lines=True)
        table.add_column("Chỉ số", style="bold")
        table.add_column("Giá trị", justify="right")

        table.add_row("🔍 Tổng link tìm thấy", str(self.stats.total_found))
        table.add_row("✅ Tải thành công",       f"[green]{self.stats.downloaded}[/green]")
        table.add_row("⏭  Bỏ qua (trùng/lỗi)",  f"[yellow]{self.stats.skipped}[/yellow]")
        table.add_row("❌ Lỗi",                   f"[red]{self.stats.failed}[/red]")
        table.add_row("⏱  Thời gian chạy",        f"{minutes}m {seconds}s")
        table.add_row("📁 Thư mục lưu",           str(DATA_DIR.relative_to(ROOT_DIR)))
        table.add_row("📝 File log",               str(LOG_FILE.name))

        console.print(table)

        if self.stats.failed_urls:
            console.print("\n[bold red]❌ Các URL bị lỗi:[/bold red]")
            for url in self.stats.failed_urls:
                console.print(f"  • {url}")

        logger.info(
            f"PHIÊN KẾT THÚC | Tìm: {self.stats.total_found} | "
            f"Tải: {self.stats.downloaded} | Bỏ: {self.stats.skipped} | "
            f"Lỗi: {self.stats.failed} | Thời gian: {minutes}m {seconds}s"
        )


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    scraper = VietnamLegalScraper(sources=LEGAL_SOURCES)
    scraper.run()
