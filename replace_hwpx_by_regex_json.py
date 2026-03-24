#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HWPX 내부 문자열을 JSON 정규식 규칙으로 치환하는 스크립트

사용 예:
python replace_hwpx_by_regex_json.py ^
  --input sample.hwpx ^
  --json rules_example.json ^
  --output result.hwpx
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
import zipfile
from pathlib import Path


def load_rules(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        rules = json.load(f)
    if not isinstance(rules, list):
        raise ValueError("JSON은 반드시 리스트 형태여야 합니다.")
    return rules


def apply_rules(xml_text: str, rules: list[dict]) -> str:
    for rule in rules:
        pattern = rule.get("pattern")
        replacement = rule.get("replacement", "")

        if not pattern:
            continue

        try:
            xml_text = re.sub(pattern, replacement, xml_text)
        except re.error as e:
            print(f"[경고] 정규식 오류: {pattern} -> {e}")

    return xml_text


def replace_hwpx(input_hwpx: Path, rules_json: Path, output_hwpx: Path) -> None:
    rules = load_rules(rules_json)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # 1. HWPX unzip
        with zipfile.ZipFile(input_hwpx, "r") as zf:
            zf.extractall(tmp)

        contents = tmp / "Contents"
        if not contents.exists():
            raise FileNotFoundError("HWPX 내부에 Contents 폴더가 없습니다.")

        section_files = sorted(contents.glob("section*.xml"))
        if not section_files:
            raise FileNotFoundError("Contents/section*.xml 파일을 찾지 못했습니다.")

        # 2. XML 치환
        for section in section_files:
            xml_text = section.read_text(encoding="utf-8")
            new_text = apply_rules(xml_text, rules)
            section.write_text(new_text, encoding="utf-8")

        # 3. 다시 압축
        if output_hwpx.exists():
            output_hwpx.unlink()

        with zipfile.ZipFile(output_hwpx, "w", zipfile.ZIP_DEFLATED) as out_zip:
            for path in sorted(tmp.rglob("*")):
                if path.is_file():
                    out_zip.write(path, path.relative_to(tmp))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="입력 HWPX 파일")
    parser.add_argument("--json", required=True, help="정규식 규칙 JSON")
    parser.add_argument("--output", required=True, help="출력 HWPX 파일")
    args = parser.parse_args()

    replace_hwpx(Path(args.input), Path(args.json), Path(args.output))
    print(f"완료: {args.output}")


if __name__ == "__main__":
    main()
