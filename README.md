# 교회 전자주보봇 HWPX 자동편집

HWPX 템플릿 안의 치환 표식과 정규식 규칙을 이용해 매주 전자주보를 자동으로 갱신하는 프로젝트입니다.

이 프로젝트는 다음 흐름을 기본으로 합니다.

1. HWPX 템플릿에 `{{주보일자}}`, `{{설교제목}}` 같은 표식을 넣습니다.
2. 매주 바뀌는 내용을 JSON으로 작성합니다.
3. Python 스크립트가 HWPX 내부 XML을 열어 표식을 치환합니다.
4. 정규식 규칙으로 날짜, 성경본문, 공백, 번호 형식을 정리합니다.
5. 결과 HWPX와 검수용 리포트를 생성합니다.

완전한 레이아웃 재조판보다는 "틀은 고정하고 값만 안전하게 교체"하는 운영 방식에 맞춰져 있습니다.

## 프로젝트 구성

```text
.
├─ replace_hwpx_by_regex_json.py   # HWPX 치환 및 정규식 후처리 엔진
├─ main.py                         # 간단한 실행 진입점
├─ bulletin_data_example.json      # 주보 데이터 예시
├─ rules_example.json              # 정규식 후처리 규칙 예시
├─ church_terms_dict.json          # 교회 용어 예외 사전 예시
├─ template_guideline.md           # 템플릿 설계 가이드
└─ work/                           # 대용량 HWPX 및 생성 결과 보관
```

## 준비 데이터

`bulletin_data_example.json`

```json
{
  "주보일자": "2026년 3월 29일 주일예배",
  "예배명": "주일 오전예배",
  "설교제목": "믿음으로 걷는 사람",
  "성경본문": "히브리서 11:1-6",
  "대표기도": "김은혜 집사",
  "찬양제목": "은혜 아니면",
  "광고목록": [
    "다음 주는 성찬식이 있습니다.",
    "청년부 수련회 신청을 받습니다.",
    "새가족 환영 모임은 예배 후 친교실에서 진행됩니다."
  ]
}
```

## 정규식 규칙 형식

`rules_example.json`

```json
[
  {
    "description": "연속 공백 정리",
    "pattern": "[ \\t]{2,}",
    "replacement": " "
  },
  {
    "description": "물결표 통일",
    "pattern": "\\s*~\\s*",
    "replacement": "-"
  }
]
```

필드 설명:

- `description`: 규칙 설명
- `pattern`: Python `re.sub()`에 전달할 정규식
- `replacement`: 치환 문자열
- `count`: 선택. 치환 횟수 제한
- `flags`: 선택. `IGNORECASE`, `MULTILINE`, `DOTALL` 지원

## 실행 방법

가상환경이 준비되어 있다면:

```powershell
uv run python .\replace_hwpx_by_regex_json.py `
  --input .\work\start.hwpx `
  --data .\bulletin_data_example.json `
  --rules .\rules_example.json `
  --terms .\church_terms_dict.json `
  --output .\work\result.hwpx `
  --report .\work\report.json
```

또는 간단히:

```powershell
uv run python .\main.py
```

## 지원 기능

- HWPX 내부 `Contents/section*.xml` 일괄 처리
- `{{키}}` 표식 치환
- 리스트 값을 번호 목록으로 자동 합성
- 정규식 후처리
- 교회 용어 예외 사전 기반 보정
- 치환 수, 누락 표식, XML 파일별 변경 수를 담은 리포트 생성

## 운영 권장 방식

- 템플릿은 최대한 고정합니다.
- 광고, 봉사표, 설교 정보처럼 매주 바뀌는 값만 JSON 또는 시트에서 관리합니다.
- 장평, 표 너비, 셀 테두리, 문단 스타일은 템플릿 단계에서 먼저 안정화합니다.
- 자동 생성 후 최종 검수는 1분 정도 진행하는 것을 권장합니다.

## 한계

- HWPX 내부 텍스트가 여러 XML 런으로 분리되어 있으면 일부 긴 문장 치환은 실패할 수 있습니다.
- 맞춤법과 띄어쓰기의 완전 자동 교정은 범용 규칙만으로 한계가 있습니다.
- 표 레이아웃의 미세한 재배치는 한글 편집기와 100% 동일하게 재현하기 어렵습니다.

그래서 이 프로젝트는 "정규식 + 템플릿 기반 자동화 90%"에 초점을 둡니다.
