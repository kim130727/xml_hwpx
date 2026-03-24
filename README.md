
“HWPX 안에 이미 들어 있는 특정 문자열을 찾아서, JSON에 정의한 값으로 정규식 치환”

uv run replace_hwpx_by_regex_json.py --input start.hwpx --json rules_example.json --output result.hwpx

예를 들면 이런 것입니다.

* 원본 HWPX 내용: `홍길동`
* JSON: `"홍길동" → "김철수"`
* 또는
* 원본 HWPX 내용: `2025.03.01`
* JSON 정규식: `\d{4}\.\d{2}\.\d{2}` → `2026.03.23`

즉 핵심은 `{{NAME}}` 같은 토큰이 아니라,
**문서 안의 실제 기존 값 자체를 정규식으로 찾아 바꾸는 방식**입니다.

아래처럼 README를 다시 쓰는 것이 맞습니다.

---

# README.md

````md
# HWPX 정규식 치환 도구

HWPX(한글 문서) 내부 XML을 읽어서,  
문서 안에 이미 존재하는 특정 문자열이나 패턴을  
JSON에 정의한 정규식 규칙으로 치환하는 Python 도구입니다.

---

## 주요 목적

이 도구는 플레이스홀더(`{{NAME}}`)를 치환하는 방식이 아니라,  
HWPX 문서 안의 **기존 텍스트 값**을 찾아서  
JSON 규칙에 따라 **정규식 기반으로 변경**하는 용도입니다.

예:

- `홍길동` → `김철수`
- `2025.03.01` → `2026.03.23`
- `010-1234-5678` → `010-9999-0000`

---

## 프로젝트 구조

```text
.
├── replace_hwpx_by_regex_json.py   # HWPX 내부 문자열을 정규식으로 치환
├── rules_example.json              # 치환 규칙 예시
└── README.md
````

---

## 작동 방식

1. HWPX 파일을 ZIP처럼 열기
2. `Contents/section*.xml` 읽기
3. JSON에 정의한 정규식 규칙 적용
4. 수정된 XML을 다시 HWPX로 압축 저장

---

## JSON 규칙 형식

치환 규칙은 배열 형태로 작성합니다.

```json
[
  {
    "pattern": "홍길동",
    "replacement": "김철수"
  },
  {
    "pattern": "2025\\.03\\.01",
    "replacement": "2026.03.23"
  },
  {
    "pattern": "010-\\d{4}-\\d{4}",
    "replacement": "010-9999-0000"
  }
]
```

### 설명

* `pattern`: 찾을 정규식
* `replacement`: 바꿀 값

---

## 사용 예시

```bash
python replace_hwpx_by_regex_json.py \
  --input sample.hwpx \
  --json rules_example.json \
  --output result.hwpx
```

---

## 예시 시나리오

원본 문서:

```text
성명: 홍길동
연락처: 010-1234-5678
작성일: 2025.03.01
```

JSON 규칙:

```json
[
  {
    "pattern": "홍길동",
    "replacement": "김철수"
  },
  {
    "pattern": "010-\\d{4}-\\d{4}",
    "replacement": "010-9999-0000"
  },
  {
    "pattern": "2025\\.03\\.01",
    "replacement": "2026.03.23"
  }
]
```

변환 결과:

```text
성명: 김철수
연락처: 010-9999-0000
작성일: 2026.03.23
```

---

## 주의사항

### 1. HWPX는 XML 구조입니다

문서의 텍스트가 XML 내부에서 여러 조각으로 분리되어 있으면
눈에 보기에는 한 문장이어도 정규식 치환이 실패할 수 있습니다.

예:

* 화면에는 `홍길동`으로 보이지만
* XML에서는 `홍` + `길동`으로 나뉘어 있을 수 있음

따라서 짧고 명확한 값 치환은 잘 되지만,
긴 문장 전체 치환은 실패할 수 있습니다.

---

### 2. 스타일/레이아웃 보존 목적이 아닙니다

이 도구는 문서 내용을 일부 바꾸는 자동화 도구이며,
한글의 모든 스타일과 시각적 구조를 해석하는 렌더러는 아닙니다.

---

### 3. 특수문자 주의

정규식에서 `.`, `(`, `)`, `[`, `]`, `?`, `+`, `*` 등은
특수의미가 있으므로 일반 문자로 찾으려면 이스케이프가 필요합니다.

예:

* `2025.03.01` 그대로 찾기 → `2025\\.03\\.01`

---

## 추천 용도

* 계약서 이름 일괄 변경
* 날짜, 전화번호, 주소 자동 치환
* 보고서 내 특정 표현 자동 수정
* 동일 양식 문서 대량 후처리

---

## 확장 가능 기능

* 치환된 항목 로그 저장
* section별 변경 내역 출력
* 이미지/표 제외 옵션
* 여러 HWPX 일괄 처리
* GUI 또는 웹 업로드 연동

---

## 한 줄 요약

이 도구는
**HWPX 안의 기존 텍스트를 JSON 정규식 규칙으로 찾아 바꾸는 자동화 도구**입니다.

````

---

그리고 코드도 개념이 바뀌어야 합니다.

기존 방식은 이런 구조였습니다.

```python
{{NAME}} -> JSON["NAME"]
````

지금 원하시는 방식은 이런 구조입니다.

```python
re.sub(pattern, replacement, xml_text)
```

예를 들면 실제 핵심 코드는 이렇게 가야 합니다.

```python
import json
import re

def apply_rules(xml_text: str, rules: list[dict]) -> str:
    for rule in rules:
        pattern = rule["pattern"]
        replacement = rule["replacement"]
        xml_text = re.sub(pattern, replacement, xml_text)
    return xml_text
```

JSON도 딕셔너리형이 아니라 **규칙 리스트형**이 더 적합합니다.

```json
[
  {
    "pattern": "홍길동",
    "replacement": "김철수"
  },
  {
    "pattern": "2025\\.03\\.01",
    "replacement": "2026.03.23"
  }
]
```

원하시는 표현을 더 정확히 한 줄로 정리하면 이렇습니다.

**“HWPX를 읽어서 JSON 키를 넣는 것이 아니라, HWPX 안의 기존 특정 값을 JSON에 정의한 정규식 규칙으로 찾아 바꾸는 것”**

