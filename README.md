# 보안 주간 리포트 자동화 시스템

매주 수요일 오전 11시(KST)에 GitHub Actions가 자동으로 실행되어, Claude 또는 GPT API로 보안 주간 리포트를 생성하고 이메일로 발송하는 자동화 시스템입니다.

블루팀 / 침해사고대응 / 보안관제에 관심 있는 보안 전공자를 위한 맞춤형 주간 뉴스레터를 자동으로 생성합니다.

---

## 리포트 구성

1. 🎯 대외활동 · 공모전 · 대회 (블루팀, CTF)
2. 💼 채용 공고 (블루팀 우선, 기타 보안 직군)
3. 🔥 주요 취약점 & CVE
4. 📰 보안 뉴스 & 침해사고
5. 🛠 주목할 도구 & 연구

---

## GitHub Secrets 설정

레포지토리 → Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 설명 | 예시 |
|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API 키 (Claude 사용 시) | `sk-ant-...` |
| `OPENAI_API_KEY` | OpenAI API 키 (GPT 사용 시) | `sk-...` |
| `LLM_PROVIDER` | 사용할 LLM (`claude` 또는 `openai`). 미설정 시 `config.yml` 기본값 사용 | `claude` |
| `EMAIL_SENDER` | 발신 Gmail 주소 | `myemail@gmail.com` |
| `EMAIL_PASSWORD` | Gmail 앱 비밀번호 (일반 비밀번호 ❌, 앱 비밀번호 ✅) | `xxxx xxxx xxxx xxxx` |
| `EMAIL_RECEIVER` | 수신 이메일 주소 | `receiver@example.com` |

> **Gmail 앱 비밀번호 발급 방법**
> 1. Google 계정 → 보안 → 2단계 인증 활성화
> 2. 보안 → 앱 비밀번호 → 앱 선택: "기타(직접 입력)" → 이름 입력 후 생성
> 3. 생성된 16자리 비밀번호를 `EMAIL_PASSWORD` Secret에 등록

---

## LLM Provider 전환 방법

`config.yml`의 `provider` 값 **한 줄만** 변경하면 됩니다. 다른 파일은 수정 불필요합니다.

```yaml
llm:
  provider: "claude"   # ← "openai" 로 바꾸면 GPT로 전환
```

또는 GitHub Secret `LLM_PROVIDER` 값을 변경하면 `config.yml`보다 우선 적용됩니다.

---

## 수동 실행 방법

1. 레포지토리 → **Actions** 탭 클릭
2. 좌측에서 **보안 주간 리포트 자동 생성** 워크플로우 선택
3. 우측 상단 **Run workflow** 버튼 클릭
4. 브랜치 선택 후 **Run workflow** 확인

---

## 로컬 테스트 방법

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 설정
export ANTHROPIC_API_KEY="sk-ant-..."
export EMAIL_SENDER="myemail@gmail.com"
export EMAIL_PASSWORD="xxxx xxxx xxxx xxxx"
export EMAIL_RECEIVER="receiver@example.com"
# (선택) LLM_PROVIDER 미설정 시 config.yml 기본값 사용
export LLM_PROVIDER="claude"

# 3. 리포트 생성 실행
python scripts/generate_report.py
```

생성된 리포트는 `reports/YYYY-MM-DD.md` 파일로 저장되고 이메일로 발송됩니다.

---

## 프로젝트 구조

```
security-weekly-report/
├── .github/
│   └── workflows/
│       └── weekly-report.yml   # GitHub Actions 스케줄
├── scripts/
│   ├── generate_report.py      # 메인 실행 스크립트
│   ├── llm/
│   │   ├── __init__.py         # get_llm() 팩토리 함수
│   │   ├── base.py             # BaseLLM 추상 클래스
│   │   ├── claude.py           # Claude (web_search 툴 포함)
│   │   └── openai.py           # GPT-4o (browsing 포함)
│   └── notifier/
│       ├── __init__.py
│       └── email_sender.py     # Gmail SMTP 발송 (마크다운 → HTML)
├── reports/                    # 날짜별 리포트 누적 저장
├── config.yml                  # LLM/이메일/섹션 설정
├── requirements.txt
└── README.md
```
