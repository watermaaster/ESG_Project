import pandas as pd
import numpy as np

# 1. 수질 데이터 로드
try:
    w1 = pd.read_excel("수질정보 2025.1~2025.12.xlsx", header=1)
    w2 = pd.read_excel("수질정보 2026.1~2026.5.xlsx", header=1)
    water_df = pd.concat([w1, w2], ignore_index=True)
    water_df['일자'] = pd.to_datetime(water_df['일자'].str.replace('.', '-'))
    print("✅ 수질 데이터 합치기 성공!")
except Exception as e:
    print(f"❌ 수질 데이터 로드 에러: {e}")

# 2. 기상 데이터 로드 (기상청 특수 파일 대응)
try:
    # 기상청 파일은 이름이 '기온,강수자료 2024.5~2026.5.xls' 인지 확인하세요!
    weather_df = pd.read_csv("기온,강수자료 2024.5~2026.5.xls", sep='\t', encoding='cp949')
    weather_df.columns = [c.strip() for c in weather_df.columns]
    date_col = [c for c in weather_df.columns if '일시' in c or '일자' in c][0]
    weather_df[date_col] = pd.to_datetime(weather_df[date_col])
    print("✅ 기상 데이터 로드 성공!")
except Exception as e:
    print(f"❌ 기상 데이터 로드 에러 (TSV 시도): {e}")
    # 만약 위 방법이 실패하면 엑셀로 재시도
    weather_df = pd.read_excel("기온,강수자료 2024.5~2026.5.xls", engine='xlrd')
    weather_df.columns = [c.strip() for c in weather_df.columns]
    date_col = [c for c in weather_df.columns if '일시' in c or '일자' in c][0]
    weather_df[date_col] = pd.to_datetime(weather_df[date_col])

# 3. 데이터 통합
final_df = pd.merge(water_df, weather_df, left_on='일자', right_on=date_col, how='inner')

# 4. ESG 지표 계산 (BOD 제거 부하량 기반 탄소 배출 추정)
# BOD * 유량으로 오염 총량을 구하고 전력 계수 적용
final_df['Carbon_Emission'] = final_df['BOD(㎎/L)'] * final_df['유량(㎥/s)'] * 86.4 * 0.5 * 0.4781
final_df.to_csv("dashboard_ready_data.csv", index=False, encoding='utf-8-sig')

print("🎉 모든 준비가 끝났습니다! 이제 'streamlit run app.py'를 실행하세요.")