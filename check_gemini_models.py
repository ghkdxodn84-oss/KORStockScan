import sys
import json
from pathlib import Path
from google import genai

# 1. KORStockScan 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 2. 기존 설정 파일에서 API 키 불러오기
from src.utils.constants import CONFIG_PATH, DEV_PATH

def load_system_config():
    target = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with open(target, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"🚨 설정 로드 실패: {e}")
        return {}

def main():
    conf = load_system_config()
    api_keys = [v for k, v in conf.items() if k.startswith("GEMINI_API_KEY")]
    
    if not api_keys:
        print("❌ 설정 파일(config.json)에서 GEMINI_API_KEY를 찾을 수 없습니다.")
        return

    print(f"🔑 API 키 발견! 모델 목록을 조회합니다...\n")
    
    try:
        # Client 초기화
        client = genai.Client(api_key=api_keys[0])
        
        print("==================================================")
        print("🤖 [사용 가능한 Gemini 모델 목록]")
        print("==================================================")
        
        count = 0
        # 에러를 유발했던 generation_methods 필터링 제거
        for model in client.models.list():
            # 이름에 'gemini'가 포함된 모델만 직관적으로 필터링
            if 'gemini' in model.name.lower():
                print(f"✅ 정확한 모델 ID : {model.name}")
                # display_name 속성이 없을 경우를 대비한 안전한 가져오기
                display_name = getattr(model, 'display_name', '설명 없음')
                print(f"   출시명/설명    : {display_name}")
                print("-" * 50)
                count += 1
                
        print(f"\n총 {count}개의 Gemini 모델을 사용할 수 있습니다.")
        print("목록에서 가장 똑똑한 'gemini-2.5-pro' 또는 'gemini-pro' 계열의 정확한 모델 ID를 복사하세요!")

    except Exception as e:
        print(f"🚨 API 호출 중 에러 발생: {e}")

if __name__ == "__main__":
    main()