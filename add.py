import streamlit as st
import pandas as pd
import numpy as np
import datetime

# -------------------------------------------------------------------
# 0. PAGE CONFIGURATION & STYLES
# -------------------------------------------------------------------
st.set_page_config(
    page_title="AI 아쿠아포닉스 통합 대시보드",
    page_icon="🐟🌿",
    layout="wide"
)

# 사용자 정의 스탈링 (내부 관리용 기능 중심 UI, 여백 확보)
st.markdown("""
    <style>
    .status-dot-green {
        height: 12px; width: 12px; background-color: #28a745;
        border-radius: 50%; display: inline-block; margin-right: 5px;
    }
    .status-dot-red {
        height: 12px; width: 12px; background-color: #dc3545;
        border-radius: 50%; display: inline-block; margin-right: 5px;
    }
    .relative-label {
        color: #856404; background-color: #fff3cd; border: 1px solid #ffeeba;
        padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;
    }
    .metric-card {
        background-color: #f8f9fa; border: 1px solid #dee2e6;
        border-radius: 8px; padding: 12px; margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Session State 초기화 (임계값 및 세팅 상태 관리)
if 'thresholds' not in st.session_state:
    st.session_state.thresholds = {
        'water_temp': {'normal_low': 22.0, 'normal_high': 26.0, 'caution_low': 20.0, 'caution_high': 28.0},
        'ph': {'normal_low': 6.5, 'normal_high': 7.5, 'caution_low': 6.0, 'caution_high': 8.0},
        'soil_moisture': {'normal_low': 60.0, 'normal_high': 80.0, 'caution_low': 50.0, 'caution_high': 90.0},
        'ec': {'normal_low': 1.2, 'normal_high': 1.8, 'caution_low': 1.0, 'caution_high': 2.0},
    }

if 'disease_tags_fish' not in st.session_state:
    st.session_state.disease_tags_fish = ["아가미부식병", "솔방울병", "솔방울병 의심"]

if 'disease_tags_plant' not in st.session_state:
    st.session_state.disease_tags_plant = ["점무늬병", "노균병"]

if 'manual_inputs' not in st.session_state:
    st.session_state.manual_inputs = {
        'ammonia': 0.15, 'ammonia_ts': '2026-08-31 09:00',
        'do': 7.2, 'do_ts': '2026-08-31 09:00'
    }

# -------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------
def get_tier_status(val, metric_key):
    t = st.session_state.thresholds.get(metric_key, {})
    if not t:
        return "정상", "🟢"
    if t['normal_low'] <= val <= t['normal_high']:
        return "정상", "🟢"
    elif t['caution_low'] <= val < t['normal_low'] or t['normal_high'] < val <= t['caution_high']:
        return "주의", "🟡"
    else:
        return "위험", "🔴"

def render_threshold_inputs(metric_key, metric_name):
    with st.expander(f"⚙️ {metric_name} 임계값 설정 (3단계)"):
        st.caption("수치 미정: 입력 필드 및 동적 반영 로직 구축 완료")
        col_n1, col_n2 = st.columns(2)
        n_low = col_n1.number_input(f"{metric_name} 정상 하한", value=st.session_state.thresholds[metric_key]['normal_low'], key=f"{metric_key}_nl")
        n_high = col_n2.number_input(f"{metric_name} 정상 상한", value=st.session_state.thresholds[metric_key]['normal_high'], key=f"{metric_key}_nh")
        
        col_c1, col_c2 = st.columns(2)
        c_low = col_c1.number_input(f"{metric_name} 주의 하한", value=st.session_state.thresholds[metric_key]['caution_low'], key=f"{metric_key}_cl")
        c_high = col_c2.number_input(f"{metric_name} 주의 상한", value=st.session_state.thresholds[metric_key]['caution_high'], key=f"{metric_key}_ch")
        
        st.info("⚠️ 주의 범위를 벗어난 영역은 자동으로 '위험'으로 판정됩니다.")
        if st.button(f"{metric_name} 임계값 저장", key=f"btn_{metric_key}"):
            st.session_state.thresholds[metric_key] = {
                'normal_low': n_low, 'normal_high': n_high,
                'caution_low': c_low, 'caution_high': c_high
            }
            st.success("임계값이 업데이트되었습니다.")

# -------------------------------------------------------------------
# MAIN TITLE & NAVIGATION (4 PAGES)
# -------------------------------------------------------------------
st.title("🐟🌿 AI 아쿠아포닉스 통합 대시보드")

pages = ["통합 개요 (Overview)", "어류 모니터링 (Fish)", "식물 모니터링 (Plant)", "시스템 관리 (Admin)"]
selected_page = st.sidebar.radio("페이지 선택", pages)
st.sidebar.markdown("---")
st.sidebar.caption("운영 목적: 내부 기능 제어 & 상태 모니터링")

# 샘플 데이터 생성
@st.cache_data
def get_time_series_data():
    dates = pd.date_range(end=datetime.datetime.now(), periods=48, freq='h')
    return pd.DataFrame({
        '시간': dates,
        '수온 (°C)': np.random.normal(24.1, 0.4, 48),
        'pH': np.random.normal(6.9, 0.1, 48),
        '토양 수분 (%)': np.random.normal(68.0, 2.0, 48),
        'EC (mS/cm)': np.random.normal(1.4, 0.05, 48)
    }).set_index('시간')

ts_data = get_time_series_data()

# -------------------------------------------------------------------
# PAGE 1: OVERVIEW (통합 개요)
# -------------------------------------------------------------------
if selected_page == "통합 개요 (Overview)":
    st.header("📊 통합 개요 (Overview)")
    st.markdown("---")
    
    # 1. 시스템 연결 상태 (Green/Red Dot)
    st.subheader("🖥️ 시스템 연결 상태")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<span class="status-dot-green"></span> **ESP32 (어류 수조)**: 정상', unsafe_allow_html=True)
    with c2:
        st.markdown('<span class="status-dot-green"></span> **ESP32 (식물 작물)**: 정상', unsafe_allow_html=True)
    with c3:
        st.markdown('<span class="status-dot-green"></span> **카메라 스트림**: 정상', unsafe_allow_html=True)
    with c4:
        st.markdown('<span class="status-dot-green"></span> **MQTT 브로커**: 연결됨', unsafe_allow_html=True)
        
    st.markdown("---")
    
    # 2. 핵심 요약 카드
    st.subheader("📌 핵심 요약 지표")
    col_f1, col_f2, col_p1, col_p2 = st.columns(4)
    
    curr_temp = ts_data['수온 (°C)'].iloc[-1]
    temp_status, temp_icon = get_tier_status(curr_temp, 'water_temp')
    col_f1.metric("어류 수온", f"{curr_temp:.1f} °C", f"상태: {temp_status} {temp_icon}")
    
    curr_ph = ts_data['pH'].iloc[-1]
    ph_status, ph_icon = get_tier_status(curr_ph, 'ph')
    col_f2.metric("어류 수질 pH", f"{curr_ph:.2f}", f"상태: {ph_status} {ph_icon}")
    
    curr_sm = ts_data['토양 수분 (%)'].iloc[-1]
    sm_status, sm_icon = get_tier_status(curr_sm, 'soil_moisture')
    col_p1.metric("식물 토양수분", f"{curr_sm:.1f} %", f"상태: {sm_status} {sm_icon}")
    
    curr_ec = ts_data['EC (mS/cm)'].iloc[-1]
    ec_status, ec_icon = get_tier_status(curr_ec, 'ec')
    col_p2.metric("식물 근권 EC", f"{curr_ec:.2f} mS/cm", f"상태: {ec_status} {ec_icon}")

    st.markdown("---")
    
    # 3. 최근 통합 알림 리스트
    st.subheader("🚨 최근 통합 알림 히스토리")
    overview_alerts = pd.DataFrame([
        {"시각": "14:32", "이상 종류": "센서-수온", "상세": "27.3°C (위험)", "관련 개체": "-"},
        {"시각": "15:10", "이상 종류": "개체-활동량", "상세": "저활동, 평소 대비 -62%", "관련 개체": "어류 ID 3"},
        {"시각": "11:20", "이상 종류": "개체-병해충", "상세": "노균병 감지 (신뢰도 0.87)", "관련 개체": "식물 ID 2"},
        {"시각": "13:47", "이상 종류": "제어-양액보류", "상세": "분변 탱크 액비 미준비로 공급 보류", "관련 개체": "-"}
    ])
    st.dataframe(overview_alerts, use_container_width=True)

# -------------------------------------------------------------------
# PAGE 2: FISH (어류 페이지)
# -------------------------------------------------------------------
elif selected_page == "어류 모니터링 (Fish)":
    st.header("🐟 어류 모니터링")
    st.markdown("---")
    
    # Section 1: 실시간 지표 (3단계 색상 + 임계값 설정)
    st.subheader("1. 실시간 지표")
    col1, col2 = st.columns(2)
    
    with col1:
        v_temp = ts_data['수온 (°C)'].iloc[-1]
        st_temp, ic_temp = get_tier_status(v_temp, 'water_temp')
        st.metric("수온 (Water Temp)", f"{v_temp:.1f} °C", f"등급: {st_temp} {ic_temp}")
        render_threshold_inputs('water_temp', '수온')
        st.line_chart(ts_data['수온 (°C)'], height=150)
        
    with col2:
        v_ph = ts_data['pH'].iloc[-1]
        st_ph, ic_ph = get_tier_status(v_ph, 'ph')
        st.metric("수질 pH", f"{v_ph:.2f}", f"등급: {st_ph} {ic_ph}")
        render_threshold_inputs('ph', '수질 pH')
        st.line_chart(ts_data['pH'], height=150)
        
    col3, col4 = st.columns(2)
    with col3:
        st.metric("암모니아 (수동 입력)", f"{st.session_state.manual_inputs['ammonia']} mg/L", f"측정 시각: {st.session_state.manual_inputs['ammonia_ts']}")
        with st.popover("수동 입력"):
            st.session_state.manual_inputs['ammonia'] = st.number_input("암모니아 (mg/L)", value=st.session_state.manual_inputs['ammonia'])
            st.session_state.manual_inputs['ammonia_ts'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with col4:
        st.metric("용존산소량 (DO - 수동 입력)", f"{st.session_state.manual_inputs['do']} mg/L", f"측정 시각: {st.session_state.manual_inputs['do_ts']}")
        with st.popover("수동 입력"):
            st.session_state.manual_inputs['do'] = st.number_input("DO (mg/L)", value=st.session_state.manual_inputs['do'])
            st.session_state.manual_inputs['do_ts'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    st.markdown("---")
    
    # Section 2: 카메라
    st.subheader("2. 어류 카메라 스트림")
    c_cam1, c_cam2 = st.columns([3, 1])
    with c_cam1:
        st.image("https://via.placeholder.com/600x300.png?text=Fish+Tank+Live+Camera+Feed", caption="최근 캡처 이미지 (1장)")
    with c_cam2:
        st.number_input("자동 갱신 주기 (초)", min_value=1, value=5, step=1, help="숫자 입력 가능, 기본값 추후 확정")
        
    st.markdown("---")
    
    # Section 3: 개체 목록 & 활동량 / 병해충
    st.subheader("3. 어류 개체 목록 & AI 알림")
    
    with st.expander("⚙️ 활동량 경보 임계값 설정"):
        c_act1, c_act2 = st.columns(2)
        c_act1.number_input("저활동 감지 하락률 (%)", value=30.0, key="act_drop")
        c_act2.number_input("과활동 감지 상승률 (%)", value=40.0, key="act_rise")
        st.caption("이동평균 대비 변화율 기준 (기준 수치는 추후 입력)")

    fish_df = pd.DataFrame([
        {"개체 ID": "Fish_01", "상태": "정상 🟢", "활동량": "정상"},
        {"개체 ID": "Fish_02", "상태": "이상 🔴", "활동량": "저활동 경보 (-35%)"},
        {"개체 ID": "Fish_03", "상태": "정상 🟢", "활동량": "정상"},
    ])
    st.dataframe(fish_df, use_container_width=True)
    
    # 유동적 병명 리스트
    st.write("**감지 가능 병명 목록 (동적 태그 리스트):**")
    tag_cols = st.columns(len(st.session_state.disease_tags_fish) + 1)
    for idx, tag in enumerate(st.session_state.disease_tags_fish):
        tag_cols[idx].info(f"🏷️ {tag}")
    
    with tag_cols[-1]:
        new_tag = st.text_input("새 병명 추가", key="new_fish_tag", label_visibility="collapsed", placeholder="+ 병명 추가")
        if st.button("추가", key="add_fish_tag_btn"):
            if new_tag and new_tag not in st.session_state.disease_tags_fish:
                st.session_state.disease_tags_fish.append(new_tag)
                st.rerun()

    st.markdown("---")
    
    # Section 4: 사료 (배급 사료 잔존량)
    st.subheader("4. 배급 사료 잔존량")
    st.markdown('<span class="relative-label">⚠️ 정확한 무게(g) 아님 (픽셀 면적 기준 상대값)</span>', unsafe_allow_html=True)
    st.write("")
    
    c_f1, c_f2 = st.columns([2, 1])
    with c_f1:
        st.write("**회차별 소모 감소 추이 (급여 시 100% 리셋)**")
        decay_df = pd.DataFrame({
            '경과시간(초)': np.arange(0, 120, 10),
            '1회차 배급 소모': 100 * np.exp(-0.03 * np.arange(0, 120, 10)),
            '2회차 배급 소모': 100 * np.exp(-0.015 * np.arange(0, 120, 10))
        }).set_index('경과시간(초)')
        st.line_chart(decay_df)
        
    with c_f2:
        st.metric("현재 잔존 비율", "35 %")
        st.write("추천 급여량: **25g**")
        st.caption("ℹ️ 자동 급이 아님, 참고값")
        st.text("최근 급여 시각: 12:00:00")
        st.text("다음 예상 급여: 16:00:00")

    with st.expander("⚙️ 적응형 급여 로직 설정 (6개 수치 입력)"):
        st.caption("수치 미정: 입력 필드 배치 완료")
        cf1, cf2, cf3 = st.columns(3)
        cf1.number_input("N 초 (소모 판단 시간)", value=60)
        cf2.number_input("임계 소모율 (%)", value=80.0)
        cf3.number_input("증가폭 α (%)", value=10.0)
        
        cf4, cf5, cf6 = st.columns(3)
        cf4.number_input("감소폭 α (%)", value=10.0)
        cf5.number_input("1회 최대 급여량 상한", value=100.0)
        cf6.number_input("최소 재급여 간격 (분)", value=30)

    st.markdown("---")
    
    # Section 5: 탱크
    st.subheader("5. 탱크 및 에어 공급 상태")
    ct1, ct2, ct3 = st.columns(3)
    
    with ct1:
        st.write("**분변 탱크 수위**")
        st.success("배지 상태: 정상")
        st.caption("⚠️ 플로트 스위치 감지 (낮음/정상 2단계만 표기)")
    with ct2:
        st.write("**저장 탱크 수위**")
        st.success("배지 상태: 정상")
        st.caption("⚠️️ 플로트 스위치 감지 (낮음/정상 2단계만 표기)")
    with ct3:
        st.write("**공기 공급 경과 시간**")
        st.info("14시간 경과 (기준 12~24시간)")
        st.caption("⚠️ 에어펌프 가동 시간 기준 (액비화 진행률 명칭 사용 금지)")

    st.markdown("---")
    
    # Section 6: 제어 패널
    st.subheader("6. 제어 패널 (MQTT 실통신 제어)")
    cp1, cp2, cp3, cp4 = st.columns(4)
    
    with cp1:
        st.toggle("히터 (Heater)", value=True, key="sw_heater")
        st.radio("히터 모드", ["자동", "수동"], key="mode_heater", horizontal=True)
    with cp2:
        st.toggle("본수조 에어펌프", value=True, key="sw_air1")
        st.radio("본수조 에어 모드", ["자동", "수동"], key="mode_air1", horizontal=True)
    with cp3:
        st.toggle("분변탱크 에어펌프", value=False, key="sw_air2")
        st.radio("분변 에어 모드", ["자동", "수동"], key="mode_air2", horizontal=True)
    with cp4:
        st.toggle("환수 펌프", value=False, key="sw_water")
        st.radio("환수 모드", ["자동", "수동"], key="mode_water", horizontal=True)

    if st.button("📡 라즈베리파이/ESP32로 MQTT 제어 명령 즉시 전송", type="primary"):
        st.success("MQTT 제어 파이프라인으로 트리가 발송되었습니다.")

# -------------------------------------------------------------------
# PAGE 3: PLANT (식물 페이지)
# -------------------------------------------------------------------
elif selected_page == "식물 모니터링 (Plant)":
    st.header("🌱 식물 모니터링")
    st.markdown("---")
    

    
    st.markdown("---")
    
    # 실시간 지표
    st.subheader("1. 식물 생육 환경 센서 (3단계 카드)")
    p_col1, p_col2, p_col3 = st.columns(3)
    
    with p_col1:
        v_sm = ts_data['토양 수분 (%)'].iloc[-1]
        st_sm, ic_sm = get_tier_status(v_sm, 'soil_moisture')
        st.metric("토양 수분", f"{v_sm:.1f} %", f"등급: {st_sm} {ic_sm}")
        render_threshold_inputs('soil_moisture', '토양 수분')
        
    with p_col2:
        v_ec = ts_data['EC (mS/cm)'].iloc[-1]
        st_ec, ic_ec = get_tier_status(v_ec, 'ec')
        st.metric("근권 EC", f"{v_ec:.2f} mS/cm", f"등급: {st_ec} {ic_ec}")
        render_threshold_inputs('ec', '근권 EC')
        
    with p_col3:
        st.metric("기온 (DHT22)", "25.4 °C", "등급: 정상 🟢")
        st.caption("고온 경보 및 환기 연동용")

    st.markdown("---")
    
    # 식물 카메라 & YOLOv8
    st.subheader("2. 식물 병해충 스캔 카메라")
    st.image("https://via.placeholder.com/600x250.png?text=YOLOv8+Plant+Disease+Camera+Feed", caption="YOLOv8 실시간 식물 진단 스트림")
    
    st.write("**감지 가능 병해충 목록 (동적 태그 리스트):**")
    ptag_cols = st.columns(len(st.session_state.disease_tags_plant) + 1)
    for idx, tag in enumerate(st.session_state.disease_tags_plant):
        ptag_cols[idx].warning(f"🐛 {tag}")
    
    with ptag_cols[-1]:
        p_new_tag = st.text_input("새 병해충 추가", key="new_plant_tag", label_visibility="collapsed", placeholder="+ 병해충 추가")
        if st.button("추가", key="add_plant_tag_btn"):
            if p_new_tag and p_new_tag not in st.session_state.disease_tags_plant:
                st.session_state.disease_tags_plant.append(p_new_tag)
                st.rerun()

    st.markdown("---")
    
    # 식물 개체(뿌리)별 추적 목록
    st.subheader("3. 개체(뿌리)별 생육 추적 (단일 화분 6뿌리 파종)")
    st.markdown('<span class="relative-label">⚠️ 실측 면적(cm²) 아님 · 추이 비교용</span>', unsafe_allow_html=True)
    st.write("")
    
    plant_ind_df = pd.DataFrame([
        {"개체 ID": "Plant_P1", "상태 배지": "정상 🟢", "잎 면적 추이 (픽셀)": "1420 px", "성장 정체 경보": "정상"},
        {"개체 ID": "Plant_P2", "상태 배지": "이상 🔴", "잎 면적 추이 (픽셀)": "820 px", "성장 정체 경보": "급감 경보 (-58%)"},
        {"개체 ID": "Plant_P3", "상태 배지": "정상 🟢", "잎 면적 추이 (픽셀)": "1390 px", "성장 정체 경보": "정상"},
        {"개체 ID": "Plant_P4", "상태 배지": "정상 🟢", "잎 면적 추이 (픽셀)": "1510 px", "성장 정체 경보": "정상"},
        {"개체 ID": "Plant_P5", "상태 배지": "정상 🟢", "잎 면적 추이 (픽셀)": "1400 px", "성장 정체 경보": "정상"},
        {"개체 ID": "Plant_P6", "상태 배지": "정상 🟢", "잎 면적 추이 (픽셀)": "1450 px", "성장 정체 경보": "정상"},
    ])
    st.dataframe(plant_ind_df, use_container_width=True)

    st.markdown("---")
    
    # 제어 패널
    st.subheader("4. 식물 자동 제어 패널")
    pc1, pc2, pc3 = st.columns(3)
    with pc1:
        st.toggle("급수 펌프", value=False)
        st.caption("토양수분 < 하한 시 자동 트리거")
    with pc2:
        st.toggle("양액(분변 액비) 펌프", value=False)
        st.caption("근권 EC < 하한 시 트리거 (분변 탱크 수위/액비화 충족 선행조건)")
    with pc3:
        st.toggle("보광등 (LED)", value=True)
        st.caption("광량 부족 시 자동 점등")

# -------------------------------------------------------------------
# PAGE 4: ADMIN (시스템 관리)
# -------------------------------------------------------------------
elif selected_page == "시스템 관리 (Admin)":
    st.header("⚙️ 시스템 관리 (Admin)")
    st.markdown("---")
    
    # Section 1: 구체적 Alert Type 로그
    st.subheader("1. 상세 시스템 로그 (Specific Alert Types)")
    
    logs_df = pd.DataFrame([
        {"시각": "2026-08-31 14:32:01", "이상 종류 (alert_type)": "센서-수온", "상세 내용": "27.3°C (위험 범위 초과)", "관련 개체": "-"},
        {"시각": "2026-08-31 15:10:12", "이상 종류 (alert_type)": "개체-활동량", "상세 내용": "저활동, 평소 이동평균 대비 -62%", "관련 개체": "Fish ID 3"},
        {"시각": "2026-08-31 11:20:45", "이상 종류 (alert_type)": "개체-병해충", "상세 내용": "노균병 감지 (신뢰도 0.87)", "관련 개체": "Plant ID 2"},
        {"시각": "2026-08-31 13:47:30", "이상 종류 (alert_type)": "제어-양액보류", "상세 내용": "분변 탱크 액비 미준비로 공급 보류", "관련 개체": "-"},
        {"시각": "2026-08-31 15:32:10", "이상 종류 (alert_type)": "센서-토양수분", "상세 내용": "18% (위험, 하한 미달)", "관련 개체": "-"}
    ])
    
    st.dataframe(logs_df, use_container_width=True)
    
    st.markdown("---")
    
    # Section 2: CSV 다운로드
    st.subheader("2. 데이터 백업 & CSV Export")
    csv_bytes = logs_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 센서 및 경보 로그 CSV 다운로드",
        data=csv_bytes,
        file_name=f"aquaponics_system_log_{datetime.date.today()}.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    
    # Section 3: 외부 알림 연동 플레이스홀더
    st.subheader("3. 외부 알림 연동 (External Notification)")
    st.info("ℹ️ 세부 연동 방식(이메일/SMS 등)은 교수님과 협의 후 결정 예정입니다. (현재 플레이스홀더 구조 구축 완료)")
    
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        st.text_input("수신자 이메일 주소", value="admin@smartfarm.ac.kr")
    with col_n2:
        st.selectbox("알림 발송 임계 조건", ["'위험' 등급 발생 시 즉시 발송", "'주의' 이상 발생 시 발송"])
    st.checkbox("로그 발생 시 외부 알림 동기 발송 활성화", value=False)
