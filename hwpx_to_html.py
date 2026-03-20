import argparse
import html
import zipfile
from pathlib import Path

from hwpx.tools.text_extractor import TextExtractor


def extract_images(hwpx_path: Path, assets_dir: Path) -> list[str]:
    """
    HWPX 내부 BinData/* 파일을 assets_dir로 추출하고,
    HTML에서 사용할 상대경로 리스트를 반환합니다.
    """
    assets_dir.mkdir(parents=True, exist_ok=True)
    image_rel_paths: list[str] = []

    with zipfile.ZipFile(hwpx_path, "r") as z:
        for name in z.namelist():
            if not name.startswith("BinData/"):
                continue
            # 폴더 엔트리 제외
            if name.endswith("/"):
                continue

            filename = Path(name).name
            out_path = assets_dir / filename

            # 추출(덮어쓰기)
            out_path.write_bytes(z.read(name))

            # 이미지 확장자만 HTML에 포함(필요하면 더 추가)
            if out_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}:
                image_rel_paths.append(f"{assets_dir.name}/{filename}")

    # 보기 좋게 정렬
    image_rel_paths.sort()
    return image_rel_paths


def hwpx_text_to_paragraphs(hwpx_path: Path) -> list[str]:
    with TextExtractor(str(hwpx_path)) as ex:
        text = ex.extract_text() or ""

    # 문단 분리: 빈 줄 기준 (원하는 기준에 맞게 조정 가능)
    paras = []
    for p in text.replace("\r\n", "\n").split("\n\n"):
        p = p.strip()
        if p:
            paras.append(p)
    return paras


def write_html(out_html: Path, title: str, paragraphs: list[str], image_rel_paths: list[str]) -> None:
    """
    매우 단순하지만 인쇄/공유에 쓸 수 있는 HTML 생성.
    """
    out_html.parent.mkdir(parents=True, exist_ok=True)

    # 문단을 <p>로. 줄바꿈은 <br>로.
    para_html = []
    for t in paragraphs:
        safe = html.escape(t).replace("\n", "<br>")
        para_html.append(f"<p>{safe}</p>")

    # 이미지 갤러리(문서 내 위치 매핑 X, 단순 노출)
    imgs_html = []
    if image_rel_paths:
        imgs_html.append("<h2>Images (extracted from BinData)</h2>")
        imgs_html.append('<div class="gallery">')
        for rel in image_rel_paths:
            imgs_html.append(
                f'<figure><img src="{html.escape(rel)}" alt="{html.escape(rel)}"><figcaption>{html.escape(rel)}</figcaption></figure>'
            )
        imgs_html.append("</div>")

    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans KR", Arial, sans-serif; margin: 24px; line-height: 1.6; }}
    .container {{ max-width: 900px; margin: 0 auto; }}
    h1 {{ font-size: 20px; margin: 0 0 16px; }}
    p {{ margin: 0 0 10px; }}
    .gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }}
    figure {{ margin: 0; border: 1px solid #ddd; padding: 8px; border-radius: 8px; }}
    img {{ width: 100%; height: auto; display: block; }}
    figcaption {{ font-size: 12px; color: #555; word-break: break-all; margin-top: 6px; }}
    @media print {{
      body {{ margin: 0; }}
      .container {{ max-width: none; margin: 0; padding: 16px; }}
      figure {{ break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>{html.escape(title)}</h1>
    {''.join(para_html)}
    {''.join(imgs_html)}
  </div>
</body>
</html>
"""
    out_html.write_text(html_doc, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Export HWPX text to HTML and extract BinData images.")
    ap.add_argument("--in", dest="in_path", required=True, help="Input .hwpx file")
    ap.add_argument("--out", dest="out_html", required=True, help="Output .html file")
    ap.add_argument("--assets", dest="assets_dir", default="assets", help="Directory to extract BinData files into (default: assets)")
    ap.add_argument("--title", dest="title", default="HWPX Export", help="HTML title")
    args = ap.parse_args()

    hwpx_path = Path(args.in_path)
    out_html = Path(args.out_html)
    assets_dir = out_html.parent / args.assets_dir  # HTML 옆에 assets 폴더 생성

    if not hwpx_path.exists():
        raise FileNotFoundError(f"Input not found: {hwpx_path}")

    paragraphs = hwpx_text_to_paragraphs(hwpx_path)
    image_rel_paths = extract_images(hwpx_path, assets_dir)
    write_html(out_html, args.title, paragraphs, image_rel_paths)

    print(f"OK: wrote HTML -> {out_html}")
    print(f"OK: extracted assets -> {assets_dir} ({len(image_rel_paths)} image files linked)")


if __name__ == "__main__":
    main()