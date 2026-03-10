from flask import Flask, render_template, request
import os
import json
import glob

app = Flask(__name__)

# 💡 [핵심 수정] 웹 서버도 data/report 폴더를 찾도록 경로 수정 ('reports' -> 'report')
REPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'report'))

@app.route('/')
def index():
    # 1. 저장된 모든 날짜의 리포트 파일 목록 가져오기
    files = sorted(glob.glob(os.path.join(REPORT_DIR, 'report_*.json')), reverse=True)
    available_dates = [os.path.basename(f).replace('report_', '').replace('.json', '') for f in files]
    
    if not available_dates:
        return "생성된 리포트가 없습니다. daily_report_generator.py를 먼저 실행해주세요."

    # 2. 사용자가 날짜를 선택했는지 확인 (기본값: 가장 최근 날짜)
    selected_date = request.args.get('date', available_dates[0])
    
    if selected_date not in available_dates:
        selected_date = available_dates[0]

    # 3. 선택한 날짜의 JSON 데이터 로드
    target_file = os.path.join(REPORT_DIR, f'report_{selected_date}.json')
    with open(target_file, 'r', encoding='utf-8') as f:
        report_data = json.load(f)

    return render_template('index.html', dates=available_dates, selected_date=selected_date, data=report_data)

if __name__ == '__main__':
    # 외부(EC2 퍼블릭 IP)에서 접속할 수 있도록 host를 0.0.0.0으로 설정합니다.
    app.run(host='0.0.0.0', port=5000, debug=True)