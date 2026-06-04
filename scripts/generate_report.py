import argparse
import os
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path

import yaml

# 프로젝트 루트를 sys.path에 추가
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from llm import get_llm
from notifier import email_sender


SYSTEM_PROMPT = """
당신은 정보보안 분야 전문 리서처입니다.
웹 검색을 통해 최신 정보를 수집하고, 블루팀/침해사고대응/보안관제에 관심 있는
보안 전공자 관점에서 주간 리포트를 작성합니다.
반드시 한국어로 작성하며, 마크다운 형식을 사용합니다.
각 항목에는 출처 링크를 포함합니다.
아래에 섹션별로 우선적으로 검색해야 할 사이트와 추천 검색 쿼리가 주어집니다.
반드시 해당 사이트들을 먼저 확인하고, 없으면 일반 검색으로 보완하세요.
"""

USER_PROMPT = """
오늘: {today} | 이번 주: {week_range}
각 항목에 출처 링크 필수. 정보 없으면 "해당 정보 없음" 표시.

# 📊 보안 주간 리포트 — {today}

## 🎯 1. 대외활동·공모전·대회
사이트: {activities_sites} / 쿼리: {activities_queries}
- 블루팀/침해사고대응/포렌식: KISA·국가기관 훈련·공모전 (이름, 주최, 마감일, 링크)
- CTF [{ctf_sites}]: 이번 주 진행·예정 CTF, 국내 CTF 일정 (대회명, 날짜, 링크)

## 💼 2. 채용 공고
사이트: {jobs_sites} / 쿼리: {jobs_queries}
- 블루팀(보안관제·SOC·SIEM·포렌식·위협헌팅·악성코드분석): 회사명, 직무, 자격요약, 마감일, 링크
- 기타(정보보안·모의해킹·AppSec·CISO·시큐어코딩): 동일 형식

## 🔥 3. 주요 취약점 & CVE
사이트: {cve_sites} / 쿼리: {cve_queries}
- CVSS 7.0↑ CVE, PoC 공개 시 ⚠️ 표시
- 항목: CVE ID, CVSS, 영향 제품·버전, 조치방법, 링크

## 📰 4. 보안 뉴스 & 침해사고
사이트: {news_sites} / 쿼리: {news_queries}
- 국내외 침해사고 (블루팀 관점: 침입경로·탐지포인트·대응)
- 랜섬웨어·APT 동향, 보안 정책·규제 변화

## 🛠 5. 주목할 도구 & 연구
사이트: {tools_sites} / 쿼리: {tools_queries}
- 신규·업데이트 SIEM/EDR/SOAR/포렌식 도구, 위협인텔리전스·악성코드 연구·블로그
- 항목: 도구명/제목, 한 줄 요약, 링크
"""


def load_config() -> dict:
    config_path = ROOT_DIR / "config.yml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_week_range(today: datetime) -> str:
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return f"{monday.strftime('%Y-%m-%d')} ~ {sunday.strftime('%Y-%m-%d')}"


def save_report(content: str, today: datetime) -> Path:
    reports_dir = ROOT_DIR / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / f"{today.strftime('%Y-%m-%d')}.md"
    report_path.write_text(content, encoding="utf-8")
    print(f"리포트 저장 완료: {report_path}")
    return report_path


def build_prompt(config: dict, today: datetime) -> str:
    """config의 sources 섹션을 읽어 프롬프트에 사이트/쿼리 정보를 주입"""
    sources = config.get("sources", {})
    year = today.strftime("%Y")
    month = today.strftime("%m").lstrip("0")

    def fmt_sites(key: str) -> str:
        sites = sources.get(key, {}).get("primary_sites", [])
        return ", ".join(sites) if sites else "일반 검색"

    def fmt_queries(key: str) -> str:
        queries = sources.get(key, {}).get("web_search_queries", [])
        formatted = [q.replace("{year}", year).replace("{month}", month) for q in queries]
        return "\n  - " + "\n  - ".join(formatted) if formatted else "일반 검색"

    return USER_PROMPT.format(
        today=today.strftime("%Y-%m-%d"),
        week_range=get_week_range(today),
        year=year,
        month=month,
        activities_sites=fmt_sites("activities"),
        activities_queries=fmt_queries("activities"),
        ctf_sites=fmt_sites("ctf"),
        ctf_queries=fmt_queries("ctf"),
        jobs_sites=fmt_sites("jobs"),
        jobs_queries=fmt_queries("jobs"),
        cve_sites=fmt_sites("cve"),
        cve_queries=fmt_queries("cve"),
        news_sites=fmt_sites("news"),
        news_queries=fmt_queries("news"),
        tools_sites=fmt_sites("tools"),
        tools_queries=fmt_queries("tools"),
    )


def main():
    parser = argparse.ArgumentParser(description="보안 주간 리포트 생성기")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="이메일 발송 없이 리포트를 콘솔에 출력만 합니다",
    )
    args = parser.parse_args()

    config = load_config()

    # 환경변수가 있으면 config보다 우선 적용
    provider = os.environ.get("LLM_PROVIDER") or config["llm"]["provider"]
    print(f"LLM Provider: {provider}")
    if args.dry_run:
        print("[DRY-RUN 모드] 이메일 발송 없이 리포트만 생성합니다.\n")

    today = datetime.now()
    prompt = build_prompt(config, today)

    try:
        llm = get_llm(provider)
        print("리포트 생성 중... (웹 검색 포함, 수 분 소요될 수 있습니다)")
        report_content = llm.generate(prompt, system_prompt=SYSTEM_PROMPT)

        save_report(report_content, today)

        if args.dry_run:
            print("\n" + "=" * 60)
            print(report_content)
            print("=" * 60)
            print("\n[DRY-RUN] 이메일 발송 생략.")
        else:
            email_sender.send(report_content)

    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"리포트 생성 실패:\n{error_detail}", file=sys.stderr)
        if not args.dry_run:
            try:
                email_sender.send_error(error_detail)
            except Exception as mail_err:
                print(f"에러 이메일 발송도 실패: {mail_err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
