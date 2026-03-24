from pathlib import Path

from replace_hwpx_by_regex_json import replace_hwpx


def main() -> None:
    base = Path(__file__).resolve().parent
    work = base / "work"
    report_path = work / "report.json"
    summary = replace_hwpx(
        input_hwpx=work / "start.hwpx",
        data_json=base / "bulletin_data_example.json",
        rules_json=base / "rules_example.json",
        terms_json=base / "church_terms_dict.json",
        output_hwpx=work / "result.hwpx",
        report_json=report_path,
    )
    print(f"전자주보 생성 완료: {work / 'result.hwpx'}")
    print(f"검수 리포트: {report_path}")
    print(f"미치환 표식 수: {len(summary['unresolved_placeholders'])}")


if __name__ == "__main__":
    main()
