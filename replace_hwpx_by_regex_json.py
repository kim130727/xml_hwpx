#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Any


FLAG_MAP = {
    "IGNORECASE": re.IGNORECASE,
    "MULTILINE": re.MULTILINE,
    "DOTALL": re.DOTALL,
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_data(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if not isinstance(data, dict):
        raise ValueError("주보 데이터 JSON은 객체 형식이어야 합니다.")
    return data


def load_rules(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []

    rules = load_json(path)
    if not isinstance(rules, list):
        raise ValueError("규칙 JSON은 배열 형식이어야 합니다.")
    return rules


def load_terms(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}

    terms = load_json(path)
    if not isinstance(terms, dict):
        raise ValueError("교회 용어 사전 JSON은 객체 형식이어야 합니다.")
    return {str(key): str(value) for key, value in terms.items()}


def format_value(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(f"{index}. {item}" for index, item in enumerate(value, start=1))
    return str(value)


def replace_placeholders(xml_text: str, data: dict[str, Any], report: dict[str, Any]) -> str:
    for key, value in data.items():
        placeholder = "{{" + key + "}}"
        replacement = format_value(value)
        count = xml_text.count(placeholder)
        if count:
            xml_text = xml_text.replace(placeholder, replacement)
            report["placeholders"][key] = report["placeholders"].get(key, 0) + count
    return xml_text


def compile_flags(flag_names: list[str] | None) -> int:
    flags = 0
    for name in flag_names or []:
        try:
            flags |= FLAG_MAP[name.upper()]
        except KeyError as exc:
            raise ValueError(f"지원하지 않는 정규식 플래그입니다: {name}") from exc
    return flags


def apply_regex_rules(xml_text: str, rules: list[dict[str, Any]], report: dict[str, Any]) -> str:
    for rule in rules:
        pattern = rule.get("pattern")
        replacement = rule.get("replacement", "")
        description = rule.get("description", pattern)
        max_count = int(rule.get("count", 0))
        flags = compile_flags(rule.get("flags"))

        if not pattern:
            continue

        new_text, count = re.subn(pattern, replacement, xml_text, count=max_count, flags=flags)
        xml_text = new_text
        report["rules"].append(
            {
                "description": description,
                "pattern": pattern,
                "count": count,
            }
        )
    return xml_text


def apply_term_dictionary(xml_text: str, terms: dict[str, str], report: dict[str, Any]) -> str:
    for wrong, correct in terms.items():
        count = xml_text.count(wrong)
        if count:
            xml_text = xml_text.replace(wrong, correct)
            report["terms"][wrong] = {"replacement": correct, "count": count}
    return xml_text


def find_unresolved_placeholders(xml_text: str) -> list[str]:
    matches = re.findall(r"\{\{[^{}]+\}\}", xml_text)
    return sorted(set(matches))


def replace_hwpx(
    input_hwpx: Path,
    data_json: Path,
    output_hwpx: Path,
    rules_json: Path | None = None,
    terms_json: Path | None = None,
    report_json: Path | None = None,
) -> dict[str, Any]:
    data = load_data(data_json)
    rules = load_rules(rules_json)
    terms = load_terms(terms_json)
    summary: dict[str, Any] = {
        "input": str(input_hwpx),
        "output": str(output_hwpx),
        "sections": [],
        "placeholders": {},
        "rules": [],
        "terms": {},
        "unresolved_placeholders": [],
    }

    unresolved: set[str] = set()

    if output_hwpx.exists():
        output_hwpx.unlink()

    with zipfile.ZipFile(input_hwpx, "r") as source, zipfile.ZipFile(
        output_hwpx, "w", zipfile.ZIP_DEFLATED
    ) as target:
        names = source.namelist()
        section_names = sorted(
            name for name in names if name.startswith("Contents/section") and name.endswith(".xml")
        )
        if not section_names:
            raise FileNotFoundError("Contents/section*.xml 파일을 찾지 못했습니다.")

        for item in source.infolist():
            data_bytes = source.read(item.filename)

            if item.filename in section_names:
                xml_text = data_bytes.decode("utf-8")
                before = xml_text

                xml_text = replace_placeholders(xml_text, data, summary)
                xml_text = apply_regex_rules(xml_text, rules, summary)
                xml_text = apply_term_dictionary(xml_text, terms, summary)

                unresolved.update(find_unresolved_placeholders(xml_text))
                summary["sections"].append(
                    {
                        "file": Path(item.filename).name,
                        "changed": before != xml_text,
                        "before_length": len(before),
                        "after_length": len(xml_text),
                    }
                )
                target.writestr(item, xml_text.encode("utf-8"))
            else:
                target.writestr(item, data_bytes)

    summary["unresolved_placeholders"] = sorted(unresolved)

    if report_json is not None:
        report_json.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="교회 전자주보 HWPX 자동 편집기")
    parser.add_argument("--input", required=True, help="입력 HWPX 파일")
    parser.add_argument("--data", required=True, help="주보 데이터 JSON")
    parser.add_argument("--output", required=True, help="출력 HWPX 파일")
    parser.add_argument("--rules", help="정규식 규칙 JSON")
    parser.add_argument("--terms", help="교회 용어 사전 JSON")
    parser.add_argument("--report", help="검수 리포트 JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = replace_hwpx(
        input_hwpx=Path(args.input),
        data_json=Path(args.data),
        output_hwpx=Path(args.output),
        rules_json=Path(args.rules) if args.rules else None,
        terms_json=Path(args.terms) if args.terms else None,
        report_json=Path(args.report) if args.report else None,
    )
    changed_sections = sum(1 for section in summary["sections"] if section["changed"])
    print(f"완료: {args.output}")
    print(f"변경된 section 수: {changed_sections}")
    if summary["unresolved_placeholders"]:
        print("미치환 표식:")
        for item in summary["unresolved_placeholders"]:
            print(f"  - {item}")


if __name__ == "__main__":
    main()
