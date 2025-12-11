import streamlit as st
import pandas as pd
from datetime import date, datetime
import uuid
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe

# ==========================================
# 1. 基本設定 & Google Sheets 接続設定
# ==========================================

st.set_page_config(
    page_title="My Campus | 共有アプリ",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 科目リスト（選択入力の際の候補として使用）
SUBJECT_LIST = [
    "現代社会論", "保健・体育4", "ドイツ語", "中国語", "応用数学A", "応用数学B",
    "物理学A", "物理学B", "計測工学", "技術英語", "電子回路2", "電気回路3",
    "電磁気学2", "電気電子材料3", "半導体工学2", "コンピュータ工学基礎", "制御工学1",
    "エレクトロニクス実験2", "法律", "経済", "哲学", "心理学", "現代物理学概論",
    "英語A", "英語B", "制御工学2", "電気機器", "電力技術", "パワーエレクトロニクス",
    "信号処理", "電気化学", "センサー工学", "ワイヤレス技術", "エレクトロニクス実験3",
    "卒業研究", "応用専門概論", "応用専門PBL1", "応用専門PBL2", "物質プロセス基礎",
    "生活と物質", "社会と環境", "物質デザイン概論", "防災工学", "エルゴノミクス",
    "インターンシップ", "食品エンジニアリング", "コスメティックス", "バイオテクノロジー",
    "高純度化技術", "環境モニタリング", "エネルギー変換デバイス", "食と健康のセンサ",
    "環境対応デバイス", "社会基盤構造", "環境衛生工学", "維持管理工学", "水環境工学",
    "環境デザイン論", "インクルーシブデザイン", "空間情報学", "環境行動", "その他"
]

# --- Google Sheets 接続関数 ---

def get_connection():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    # secretsから認証情報を取得
    json_str = st.secrets["gcp_service_account"]["my_key"]
    creds_dict = json.loads(json_str)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

# --- データの読み込み ---

def load_data_from_sheets():
    try:
        client = get_connection()
        # スプレッドシートを開く
        sheet = client.open("School_DB")

        # --- 宿題データの読み込み ---
        ws_hw = sheet.worksheet("Homework")
        df_hw = get_as_dataframe(ws_hw, evaluate_formulas=True).dropna(how='all')
        
        homework_list = []
        if not df_hw.empty:
            for _, row in df_hw.iterrows():
                try:
                    if pd.isna(row['id']) or str(row['id']) == "": continue
                    d_str = str(row['due_date']).split(' ')[0]
                    try: d_obj = datetime.strptime(d_str, '%Y-%m-%d').date()
                    except: d_obj = date.today()

                    homework_list.append({
                        "id": str(row['id']),
                        "subject": str(row['subject']),
                        "content": str(row['content']),
                        "due_date": d_obj,
                        "method": str(row['method']),
                        "priority": str(row['priority']),
                        "status": str(row['status'])
                    })
                except: continue
        
        # --- 時間割データの読み込み ---
        ws_tt = sheet.worksheet("Timetable")
        df_tt = get_as_dataframe(ws_tt, evaluate_formulas=True)
        # 必要な範囲のみ取得（4時限×5曜日想定）
        df_tt = df_tt.iloc[:4, :6]
        if "Unnamed: 0" in df_tt.columns: df_tt.set_index("Unnamed: 0", inplace=True)
        
        rows = ["1/2限", "3/4限", "5/6限", "7/8限"]
        cols = ["月", "火", "水", "木", "金"]
        
        # データ形状が合わない場合は初期化
        if df_tt.shape != (4, 5): 
            df_tt = pd.DataFrame("", index=rows, columns=cols)
        else:
            df_tt.index = rows
            df_tt.columns = cols
            df_tt = df_tt.fillna("")

        return {'timetable': df_tt, 'homework': homework_list}
    except Exception as e:
        st.error(f"接続エラー: {e}")
        return None

# --- データの保存 ---

def save_data_to_sheets(timetable_df, homework_list):
    try:
        client = get_connection()
        sheet = client.open("School_DB")

        ws_hw = sheet.worksheet("Homework")
        ws_hw.clear()
        if homework_list:
            df_export = pd.DataFrame(homework_list)
            df_export['due_date'] = df_export['due_date'].astype(str)
            set_with_dataframe(ws_hw, df_export)
        else:
            ws_hw.update('A1', [['id', 'subject', 'content', 'due_date', 'method', 'priority', 'status']])

        ws_tt = sheet.worksheet("Timetable")
        ws_tt.clear()
        set_with_dataframe(ws_tt, timetable_df, include_index=True)
    except Exception as e:
        st.error(f"保存エラー: {e}")

# --- 初期化 ---

if "init" not in st.session_state:
    with st.spinner('Google Sheetsからデータを読み込み中...'):
        loaded = load_data_from_sheets()

    if loaded:
        st.session_state.timetable_data = loaded['timetable']
        st.session_state.homework_list = loaded['homework']
    else:
        rows = ["1/2限", "3/4限", "5/6限", "7/8限"]
        cols = ["月", "火", "水", "木", "金"]
        st.session_state.timetable_data = pd.DataFrame("", index=rows, columns=cols)
        st.session_state.homework_list = []
    st.session_state.init = True

# ==========================================
# 2. デザイン定義 (CSS)
# ==========================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; color: #333; }
    .stApp { background-color: #f8f9fc; }
    .custom-card { background: white; border-radius: 16px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 15px; border-left: 5px solid #ccc; }
    .border-red { border-left-color: #e53935; }
    .border-orange { border-left-color: #fb8c00; }
    .border-blue { border-left-color: #1e88e5; }
    .border-green { border-left-color: #43a047; }
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; display: inline-block; }
    .badge-prio-高 { background: #ffebee; color: #c62828; }
    .badge-prio-中 { background: #e3f2fd; color: #1565c0; }
    .badge-prio-低 { background: #f1f8e9; color: #33691e; }
    .metric-container { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 15px; text-align: center; }
    .metric-value { font-size: 2.5rem; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. サイドバー
# ==========================================

with st.sidebar:
    st.markdown("### 🎓 My Campus")

    if st.button("🔄 データを更新"):
        del st.session_state.init
        st.rerun()

    incomplete = [h for h in st.session_state.homework_list if h['status'] != '完了']
    urgent = [h for h in incomplete if (h['due_date'] - date.today()).days <= 1]

    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-label">未完了タスク</div>
        <div class="metric-value">{len(incomplete)}</div>
    </div>
    """, unsafe_allow_html=True)

    if urgent:
        st.error(f"🔥 **{len(urgent)}件** の期限が迫っています！")

# ==========================================
# 4. メインコンテンツ
# ==========================================

st.title("お疲れ様です 👋")
st.caption("Google Sheets連携中: データはリアルタイムで共有されます")

tab_schedule, tab_homework = st.tabs(["📅 時間割", "📝 宿題管理"])

# --- TAB 1: 時間割 ---

with tab_schedule:
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    today_jp = weekdays[datetime.now().weekday()]

    mode = st.radio("表示モード", ["今日の予定", "時間割の編集"], label_visibility="collapsed", horizontal=True)

    if mode == "今日の予定":
        st.subheader(f"📅 今日の授業 ({today_jp})")
        if today_jp in st.session_state.timetable_data.columns:
            schedule = st.session_state.timetable_data[today_jp]
            has_class = False
            cols = st.columns(len(schedule))
            for idx, (period, subj) in enumerate(schedule.items()):
                with cols[idx]:
                    if subj and str(subj).strip():
                        has_class = True
                        st.markdown(f"""
                        <div style="background:white; padding:15px; border-radius:12px; border-top: 5px solid #5c6bc0; box-shadow:0 4px 6px rgba(0,0,0,0.05); text-align:center;">
                            <div style="color:gray; font-size:0.8rem;">{period}</div>
                            <div style="font-weight:bold; color:#1a237e;">{subj}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background:#f1f3f4; padding:15px; border-radius:12px; text-align:center; opacity:0.6;">
                            <div style="color:gray; font-size:0.8rem;">{period}</div>
                            <div>-</div>
                        </div>
                        """, unsafe_allow_html=True)
            if not has_class: st.info("本日の授業はありません")
        else: st.success("今日は休日です")
    else:
        st.markdown("#### ✏️ 時間割の編集")
        st.info("セルをダブルクリックして科目を直接入力できます。")
        # ★修正点: SelectboxColumnを削除し、自由入力(デフォルト)に変更しました
        edited_df = st.data_editor(
            st.session_state.timetable_data,
            use_container_width=True,
            height=300
        )
        if st.button("時間割を保存して共有"):
            st.session_state.timetable_data = edited_df
            save_data_to_sheets(st.session_state.timetable_data, st.session_state.homework_list)
            st.success("保存しました！")

# --- TAB 2: 宿題管理 ---

with tab_homework:
    with st.expander("✨ タスクを追加", expanded=False):
        with st.form("add_task", clear_on_submit=True):
            # ★修正点: 科目の入力方法を選択できるように変更
            use_manual_input = st.toggle("科目を直接入力する", value=False)
            
            c1, c2, c3 = st.columns([2, 1, 1])
            
            with c1:
                if use_manual_input:
                    subj = st.text_input("科目名")
                else:
                    subj = st.selectbox("科目を選択", SUBJECT_LIST)
            
            prio = c2.selectbox("優先度", ["高", "中", "低"])
            meth = c3.selectbox("提出方法", ["Teams", "Classroom", "Moodle", "手渡し", "その他"])
            content = st.text_input("内容")
            dd = st.date_input("期限", date.today())

            if st.form_submit_button("追加"):
                if content and subj:
                    st.session_state.homework_list.append({
                        "id": str(uuid.uuid4()),
                        "subject": subj, "content": content,
                        "due_date": dd, "method": meth,
                        "priority": prio, "status": "未着手"
                    })
                    save_data_to_sheets(st.session_state.timetable_data, st.session_state.homework_list)
                    st.success("追加しました")
                    st.rerun()
                else:
                    st.error("科目と内容は必須です")

    st.write("")
    filter_status = st.multiselect("ステータスで絞り込み", ["未着手", "作業中", "完了"], default=["未着手", "作業中"])

    if st.session_state.homework_list:
        prio_map = {"高": 0, "中": 1, "低": 2}
        sorted_hw = sorted(st.session_state.homework_list, key=lambda x: (x['status']=='完了', x['due_date'], prio_map[x['priority']]))
        
        for hw in sorted_hw:
            if hw['status'] in filter_status:
                days = (hw['due_date'] - date.today()).days
                if hw['status'] == "完了":
                    border, badge = "border-green", '<span style="color:green">✅ 完了</span>'
                elif days < 0:
                    border, badge = "border-red", f'<span style="color:red">🚨 {abs(days)}日遅れ</span>'
                elif days == 0:
                    border, badge = "border-orange", '<span style="color:orange">🔥 今日まで</span>'
                else:
                    border, badge = "border-blue", f'<span style="color:blue">⏱ あと{days}日</span>'

                with st.container():
                    c_main, c_act = st.columns([5, 1])
                    with c_main:
                        st.markdown(f"""
                        <div class="custom-card {border}">
                            <div style="display:flex; justify-content:space-between;">
                                <div><span class="badge badge-prio-{hw['priority']}">{hw['priority']}</span> <b>{hw['subject']}</b></div>
                                <div>{badge}</div>
                            </div>
                            <div style="margin:10px 0;">{hw['content']}</div>
                            <div style="font-size:0.8em; color:gray;">📅 {hw['due_date']} | 📤 {hw['method']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_act:
                        st.write("")
                        idx = ["未着手", "作業中", "完了"].index(hw['status'])
                        new_stat = st.selectbox("状態変更", ["未着手", "作業中", "完了"], index=idx, key=f"s_{hw['id']}", label_visibility="collapsed")
                        if st.button("🗑", key=f"d_{hw['id']}"):
                            st.session_state.homework_list = [x for x in st.session_state.homework_list if x['id'] != hw['id']]
                            save_data_to_sheets(st.session_state.timetable_data, st.session_state.homework_list)
                            st.rerun()
                        if new_stat != hw['status']:
                            hw['status'] = new_stat
                            save_data_to_sheets(st.session_state.timetable_data, st.session_state.homework_list)
                            st.rerun()