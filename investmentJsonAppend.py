import json
from datetime import datetime, timedelta

# 파일 경로
shortcoin_file = 'current_recommendation.json'  # current_recommendation.json
report_file = 'ReportData.json'  # ReportData.json

# current_recommendation.json에서 데이터를 읽어서 ReportData.json에 누적시키는 함수
def append_to_report_data(file_name, output_file_name):
    # current_recommendation.json 파일에서 데이터 읽기
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
            # new_data가 리스트가 아니면 리스트로 감싸기
            if not isinstance(new_data, list):
                new_data = [new_data]
    except FileNotFoundError:
        print(f"{file_name} not found.")
        return

    # ReportData.json에서 기존 데이터 불러오기
    try:
        with open(output_file_name, 'r', encoding='utf-8') as f:
            all_reports = json.load(f)
            # all_reports가 리스트가 아닌 경우 리스트로 감싸기
            if not isinstance(all_reports, list):
                all_reports = [all_reports]
    except FileNotFoundError:
        all_reports = []

    # 현재 시간으로 타임스탬프 추가
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 새로운 데이터에 timestamp 추가
    for report in new_data:
        report['timestamp'] = timestamp  # 타임스탬프 추가

    # 새로운 데이터를 ReportData에 누적
    all_reports.extend(new_data)

    # ReportData.json에 저장
    with open(output_file_name, 'w', encoding='utf-8') as f:
        json.dump(all_reports, f, ensure_ascii=False, indent=4)
        print(f"응답이 {output_file_name}에 누적되었습니다.")

# 7일 이상된 데이터 삭제 함수
def delete_old_data(days, output_file_name):
    # 현재 날짜와 3일 전 날짜 계산
    days_ago = datetime.now() - timedelta(days)
    days_ago_str = days_ago.strftime('%Y-%m-%d %H:%M:%S')

    # ReportData.json에서 기존 데이터 불러오기
    try:
        with open(output_file_name, 'r', encoding='utf-8') as f:
            all_reports = json.load(f)
            # all_reports가 리스트가 아닌 경우 리스트로 감싸기
            if not isinstance(all_reports, list):
                all_reports = [all_reports]
    except FileNotFoundError:
        all_reports = []

    # 7일 이상된 데이터 삭제
    filtered_reports = [report for report in all_reports if report['timestamp'] >= days_ago_str]

    # 필터링된 데이터를 ReportData.json에 저장
    with open(output_file_name, 'w', encoding='utf-8') as f:
        json.dump(filtered_reports, f, ensure_ascii=False, indent=4)

# 실행 예시

