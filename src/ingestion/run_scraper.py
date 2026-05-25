"""
CLI điều khiển scraper văn bản pháp luật Việt Nam.

Cách dùng:
    python -m src.ingestion.run_scraper --help
    python -m src.ingestion.run_scraper --source vbpl --pages 5
    python -m src.ingestion.run_scraper --url "https://..." --pages 2
    python -m src.ingestion.run_scraper --all
"""

import argparse
import sys
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.ingestion.scraper import (
    VietnamLegalScraper,
    LegalSource,
    LEGAL_SOURCES,
    logger,
    console,
)
from rich.table import Table
from rich import print as rprint


def list_sources():
    """In danh sách nguồn được hỗ trợ."""
    table = Table(title="📚 Nguồn văn bản pháp luật được hỗ trợ", border_style="blue")
    table.add_column("ID", style="bold cyan", width=20)
    table.add_column("Tên nguồn")
    table.add_column("Số trang mặc định", justify="center")

    for src in LEGAL_SOURCES:
        table.add_row(src.domain, src.name, str(src.max_pages))

    console.print(table)


def parse_args():
    parser = argparse.ArgumentParser(
        description="🇻🇳 Vietnamese Legal Document Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  # Xem danh sách nguồn
  python -m src.ingestion.run_scraper --list

  # Tải từ tất cả nguồn (mặc định)
  python -m src.ingestion.run_scraper --all

  # Tải từ nguồn cụ thể
  python -m src.ingestion.run_scraper --source vbpl --pages 3
  python -m src.ingestion.run_scraper --source thuvienphapluat --pages 5

  # Tải từ URL tuỳ biến
  python -m src.ingestion.run_scraper \\
    --url "https://vbpl.vn/TW/Pages/vbpq-tim-kiem.aspx?type=0" \\
    --domain my_source --pages 2
        """
    )

    parser.add_argument(
        "--list", action="store_true",
        help="Liệt kê tất cả nguồn được hỗ trợ"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Thu thập từ tất cả nguồn được cấu hình"
    )
    parser.add_argument(
        "--source", type=str, metavar="DOMAIN",
        help="Chọn nguồn theo domain ID (vd: vbpl, thuvienphapluat)"
    )
    parser.add_argument(
        "--url", type=str,
        help="URL tuỳ biến để thu thập"
    )
    parser.add_argument(
        "--domain", type=str, default="custom",
        help="Tên domain tuỳ biến (dùng cùng --url, mặc định: 'custom')"
    )
    parser.add_argument(
        "--pages", type=int, default=None,
        help="Số trang tối đa (ghi đè cấu hình mặc định)"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # ── Hiển thị danh sách nguồn ──
    if args.list:
        list_sources()
        return

    selected_sources: list[LegalSource] = []

    # ── URL tuỳ biến ──
    if args.url:
        pages = args.pages or 1
        custom_src = LegalSource(
            name=f"Tuỳ biến ({args.url[:60]}...)" if len(args.url) > 60 else f"Tuỳ biến ({args.url})",
            domain=args.domain,
            base_url=args.url,
            pagination_pattern=args.url + ("&page={page}" if "?" in args.url else "?page={page}"),
            max_pages=pages,
        )
        selected_sources.append(custom_src)

    # ── Nguồn cụ thể theo domain ──
    elif args.source:
        matched = [s for s in LEGAL_SOURCES if s.domain == args.source]
        if not matched:
            rprint(f"[bold red]❌ Không tìm thấy nguồn: '{args.source}'[/bold red]")
            rprint("Chạy [cyan]--list[/cyan] để xem danh sách nguồn.")
            sys.exit(1)
        selected_sources = matched
        if args.pages:
            for s in selected_sources:
                s.max_pages = args.pages

    # ── Tất cả nguồn (--all hoặc mặc định) ──
    else:
        selected_sources = LEGAL_SOURCES
        if args.pages:
            for s in selected_sources:
                s.max_pages = args.pages

    # ── Chạy scraper ──
    scraper = VietnamLegalScraper(sources=selected_sources)
    scraper.run()


if __name__ == "__main__":
    main()
