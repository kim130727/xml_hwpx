import argparse
import json
import zipfile
from pathlib import Path

SECTION_PREFIX = "Contents/section"
SECTION_SUFFIX = ".xml"

def replace_in_hwpx(template_path: Path, output_path: Path, replacements: dict[str, str]) -> None:
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    # 출력 폴더 생성
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(template_path, "r") as zin:
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)

                # 본문 섹션 XML만 텍스트 치환
                if item.filename.startswith(SECTION_PREFIX) and item.filename.endswith(SECTION_SUFFIX):
                    xml = data.decode("utf-8")
                    for k, v in replacements.items():
                        xml = xml.replace(k, v)
                    data = xml.encode("utf-8")

                zout.writestr(item, data)

def main():
    parser = argparse.ArgumentParser(description="Replace tokens in HWPX template")
    parser.add_argument("--template", required=True, help="template.hwpx path")
    parser.add_argument("--out", required=True, help="output hwpx path")
    parser.add_argument("--repl", required=True, help="replacements json path (utf-8)")
    args = parser.parse_args()

    template_path = Path(args.template)
    output_path = Path(args.out)
    repl_path = Path(args.repl)

    replacements = json.loads(repl_path.read_text(encoding="utf-8"))

    # 안전장치: 키/값은 문자열만
    cleaned: dict[str, str] = {}
    for k, v in replacements.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise TypeError("replacements.json의 키/값은 모두 문자열이어야 합니다.")
        cleaned[k] = v

    replace_in_hwpx(template_path, output_path, cleaned)
    print(f"OK: wrote {output_path}")

if __name__ == "__main__":
    main()