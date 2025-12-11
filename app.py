import streamlit as st
import pandas as pd
from datetime import date, datetime
import uuid
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe


# ==========================================
# 定数定義
# ==========================================

SUBJECT_LIST = [
    "現代社会論", "保健・体育4", "実験実習", "ドイツ語", "中国語", "応用数学A", "応用数学B",
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

TIMETABLE_ROWS = ["1/2限", "3/4限", "5/6限", "7/8限"]
TIMETABLE_COLS = ["月", "火", "水", "木", "金"]
WEEKDAYS_JP = ["月", "火", "水", "木", "金", "土", "日"]

PRIORITY_ORDER = {"高": 0, "中": 1, "低": 2}
STATUS_OPTIONS = ["未着手", "作業中", "完了"]
SUBMISSION_METHODS = ["Teams", "Classroom", "Moodle", "手渡し", "その他"]


# ==========================================
# Google Sheets 接続
# ==========================================

def get_google_sheets_client():
    """Google Sheetsへの接続クライアントを取得"""
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    json_str = st.secrets["gcp_service_account"]["my_key"]
    creds_dict = json.loads(json_str)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)


def parse_homework_row(row):
    """宿題データの1行をパース"""
    if pd.isna(row['id']) or str(row['id']) == "":
        return None
    
    # 日付のパース
    date_str = str(row['due_date']).split(' ')[0]
    try:
        due_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        due_date = date.today()
    
    return {
        "id": str(row['id']),
        "subject": str(row['subject']),
        "content": str(row['content']),
        "due_date": due_date,
        "method": str(row['method']),
        "priority": str(row['priority']),
        "status": str(row['status'])
    }


def load_homework_data(sheet):
    """宿題データをGoogle Sheetsから読み込む"""
    ws = sheet.worksheet("Homework")
    df = get_as_dataframe(ws, evaluate_formulas=True).dropna(how='all')
    
    homework_list = []
    if not df.empty:
        for _, row in df.iterrows():
            try:
                homework = parse_homework_row(row)
                if homework:
                    homework_list.append(homework)
            except:
                continue
    
    return homework_list


def load_timetable_data(sheet):
    """時間割データをGoogle Sheetsから読み込む"""
    ws = sheet.worksheet("Timetable")
    df = get_as_dataframe(ws, evaluate_formulas=True)
    df = df.iloc[:4, :6]
    
    if "Unnamed: 0" in df.columns:
        df.set_index("Unnamed: 0", inplace=True)
    
    # データ形状の確認と初期化
    if df.shape != (4, 5):
        df = pd.DataFrame("", index=TIMETABLE_ROWS, columns=TIMETABLE_COLS)
    else:
        df.index = TIMETABLE_ROWS
        df.columns = TIMETABLE_COLS
        df = df.fillna("")
    
    return df


def load_all_data():
    """すべてのデータをGoogle Sheetsから読み込む"""
    try:
        client = get_google_sheets_client()
        sheet = client.open("School_DB")
        
        return {
            'timetable': load_timetable_data(sheet),
            'homework': load_homework_data(sheet)
        }
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return None


def save_all_data(timetable_df, homework_list):
    """すべてのデータをGoogle Sheetsに保存"""
    try:
        client = get_google_sheets_client()
        sheet = client.open("School_DB")
        
        # 宿題データの保存
        ws_hw = sheet.worksheet("Homework")
        ws_hw.clear()
        
        if homework_list:
            df_export = pd.DataFrame(homework_list)
            df_export['due_date'] = df_export['due_date'].astype(str)
            set_with_dataframe(ws_hw, df_export)
        else:
            header = [['id', 'subject', 'content', 'due_date', 'method', 'priority', 'status']]
            ws_hw.update('A1', header)
        
        # 時間割データの保存
        ws_tt = sheet.worksheet("Timetable")
        ws_tt.clear()
        set_with_dataframe(ws_tt, timetable_df, include_index=True)
        
    except Exception as e:
        st.error(f"データ保存エラー: {e}")


# ==========================================
# UI ヘルパー関数
# ==========================================

def get_border_and_badge(homework, days_until_due):
    """宿題の状態に応じたボーダー色とバッジを取得"""
    if homework['status'] == "完了":
        return "border-green", '<span style="color:green">✅ 完了</span>'
    elif days_until_due < 0:
        return "border-red", f'<span style="color:red">🚨 {abs(days_until_due)}日遅れ</span>'
    elif days_until_due == 0:
        return "border-orange", '<span style="color:orange">🔥 今日まで</span>'
    else:
        return "border-blue", f'<span style="color:blue">⏱ あと{days_until_due}日</span>'


def render_homework_card(homework):
    """宿題カードをレンダリング"""
    days_until_due = (homework['due_date'] - date.today()).days
    border, badge = get_border_and_badge(homework, days_until_due)
    
    return f"""
    <div class="custom-card {border}">
        <div style="display:flex; justify-content:space-between;">
            <div>
                <span class="badge badge-prio-{homework['priority']}">{homework['priority']}</span>
                <b>{homework['subject']}</b>
            </div>
            <div>{badge}</div>
        </div>
        <div style="margin:10px 0;">{homework['content']}</div>
        <div style="font-size:0.8em; color:gray;">
            📅 {homework['due_date']} | 📤 {homework['method']}
        </div>
    </div>
    """


def render_class_card(period, subject):
    """授業カードをレンダリング"""
    if subject and str(subject).strip():
        return f"""
        <div style="background:white; padding:15px; border-radius:12px; 
                    border-top: 5px solid #5c6bc0; box-shadow:0 4px 6px rgba(0,0,0,0.05); 
                    text-align:center;">
            <div style="color:gray; font-size:0.8rem;">{period}</div>
            <div style="font-weight:bold; color:#1a237e;">{subject}</div>
        </div>
        """
    else:
        return f"""
        <div style="background:#f1f3f4; padding:15px; border-radius:12px; 
                    text-align:center; opacity:0.6;">
            <div style="color:gray; font-size:0.8rem;">{period}</div>
            <div>-</div>
        </div>
        """


# ==========================================
# ページ設定
# ==========================================

st.set_page_config(
    page_title="My Campus | 共有アプリ",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================
# スタイル定義
# ==========================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans JP', sans-serif;
        color: #333;
    }
    
    .stApp {
        background-color: #f8f9fc;
    }
    
    .custom-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border-left: 5px solid #ccc;
    }
    
    .border-red { border-left-color: #e53935; }
    .border-orange { border-left-color: #fb8c00; }
    .border-blue { border-left-color: #1e88e5; }
    .border-green { border-left-color: #43a047; }
    
    .badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .badge-prio-高 { background: #ffebee; color: #c62828; }
    .badge-prio-中 { background: #e3f2fd; color: #1565c0; }
    .badge-prio-低 { background: #f1f8e9; color: #33691e; }
    
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# データ初期化
# ==========================================

def initialize_session_state():
    """セッション状態を初期化"""
    if "init" not in st.session_state:
        with st.spinner('Google Sheetsからデータを読み込み中...'):
            loaded = load_all_data()
        
        if loaded:
            st.session_state.timetable_data = loaded['timetable']
            st.session_state.homework_list = loaded['homework']
        else:
            st.session_state.timetable_data = pd.DataFrame(
                "", index=TIMETABLE_ROWS, columns=TIMETABLE_COLS
            )
            st.session_state.homework_list = []
        
        st.session_state.init = True


initialize_session_state()


# ==========================================
# サイドバー
# ==========================================

with st.sidebar:
    st.markdown("### 🎓 My Campus")
    
    if st.button("🔄 データを更新"):
        del st.session_state.init
        st.rerun()
    
    # 統計情報の計算
    incomplete_tasks = [
        hw for hw in st.session_state.homework_list 
        if hw['status'] != '完了'
    ]
    
    urgent_tasks = [
        hw for hw in incomplete_tasks 
        if (hw['due_date'] - date.today()).days <= 1
    ]
    
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-label">未完了タスク</div>
        <div class="metric-value">{len(incomplete_tasks)}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if urgent_tasks:
        st.error(f"🔥 **{len(urgent_tasks)}件** の期限が迫っています！")


# ==========================================
# メインコンテンツ
# ==========================================

st.title("お疲れ様です 👋")
st.caption("Google Sheets連携中: データはリアルタイムで共有されます")

tab_schedule, tab_homework = st.tabs(["📅 時間割", "📝 宿題管理"])


# --- TAB 1: 時間割 ---

with tab_schedule:
    today_weekday = WEEKDAYS_JP[datetime.now().weekday()]
    today_date = datetime.now().strftime('%Y年%m月%d日')
    
    mode = st.radio(
        "表示モード",
        ["今日の予定", "時間割の編集"],
        label_visibility="collapsed",
        horizontal=True
    )
    
    if mode == "今日の予定":
        st.subheader(f"今日の授業 ({today_date} {today_weekday})")
        
        if today_weekday in st.session_state.timetable_data.columns:
            schedule = st.session_state.timetable_data[today_weekday]
            has_class = False
            cols = st.columns(len(schedule))
            
            for idx, (period, subject) in enumerate(schedule.items()):
                with cols[idx]:
                    st.markdown(
                        render_class_card(period, subject),
                        unsafe_allow_html=True
                    )
                    if subject and str(subject).strip():
                        has_class = True
            
            if not has_class:
                st.info("本日の授業はありません")
        else:
            st.success("今日は休日です")
    
    else:  # 編集モード
        st.markdown("#### ✏️ 時間割の編集")
        st.info("セルをダブルクリックして科目を直接入力できます。")
        
        edited_df = st.data_editor(
            st.session_state.timetable_data,
            use_container_width=True,
            num_rows="fixed"
        )
        
        if st.button("時間割を保存して共有"):
            st.session_state.timetable_data = edited_df
            save_all_data(st.session_state.timetable_data, st.session_state.homework_list)
            st.success("保存しました！")


# --- TAB 2: 宿題管理 ---

with tab_homework:
    # タスク追加フォーム
    with st.expander("✨ タスクを追加", expanded=False):
        with st.form("add_task", clear_on_submit=True):
            use_manual_input = st.toggle("科目を直接入力する", value=False)
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                if use_manual_input:
                    subject = st.text_input("科目名")
                else:
                    subject = st.selectbox("科目を選択", SUBJECT_LIST)
            
            priority = col2.selectbox("優先度", ["高", "中", "低"])
            method = col3.selectbox("提出方法", SUBMISSION_METHODS)
            
            content = st.text_input("内容")
            due_date = st.date_input("期限", date.today())
            
            if st.form_submit_button("追加"):
                if content and subject:
                    new_homework = {
                        "id": str(uuid.uuid4()),
                        "subject": subject,
                        "content": content,
                        "due_date": due_date,
                        "method": method,
                        "priority": priority,
                        "status": "未着手"
                    }
                    st.session_state.homework_list.append(new_homework)
                    save_all_data(st.session_state.timetable_data, st.session_state.homework_list)
                    st.success("追加しました")
                    st.rerun()
                else:
                    st.error("科目と内容は必須です")
    
    # フィルタリング
    st.write("")
    filter_status = st.multiselect(
        "ステータスで絞り込み",
        STATUS_OPTIONS,
        default=["未着手", "作業中"]
    )
    
    # 宿題リストの表示
    if st.session_state.homework_list:
        # ソート: 完了→期限→優先度
        sorted_homework = sorted(
            st.session_state.homework_list,
            key=lambda x: (
                x['status'] == '完了',
                x['due_date'],
                PRIORITY_ORDER[x['priority']]
            )
        )
        
        for hw in sorted_homework:
            if hw['status'] in filter_status:
                col_main, col_action = st.columns([5, 1])
                
                with col_main:
                    st.markdown(render_homework_card(hw), unsafe_allow_html=True)
                
                with col_action:
                    st.write("")
                    
                    # ステータス変更
                    current_index = STATUS_OPTIONS.index(hw['status'])
                    new_status = st.selectbox(
                        "状態変更",
                        STATUS_OPTIONS,
                        index=current_index,
                        key=f"status_{hw['id']}",
                        label_visibility="collapsed"
                    )
                    
                    # 削除ボタン
                    if st.button("🗑", key=f"delete_{hw['id']}"):
                        st.session_state.homework_list = [
                            x for x in st.session_state.homework_list 
                            if x['id'] != hw['id']
                        ]
                        save_all_data(st.session_state.timetable_data, st.session_state.homework_list)
                        st.rerun()
                    
                    # ステータスが変更された場合
                    if new_status != hw['status']:
                        hw['status'] = new_status
                        save_all_data(st.session_state.timetable_data, st.session_state.homework_list)
                        st.rerun()
    else:
        st.info("まだ宿題が登録されていません。上のフォームから追加してください。")