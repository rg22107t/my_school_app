import streamlit as st
import pandas as pd
from datetime import date, datetime
import json
import time
import uuid
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe

# ==========================================
# 🔐 ユーザー認証設定
# ==========================================
USER_CREDENTIALS = {
    "橋田": "1211",
    "ま": "1211",
}

# ==========================================
# 定数定義
# ==========================================
TIMETABLE_ROWS = ["1/2限", "3/4限", "5/6限", "7/8限"]
TIMETABLE_COLS = ["月", "火", "水", "木", "金"]
WEEKDAY_MAP = {0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 5: "土", 6: "日"}

STATUS_OPTIONS = ["未着手", "作業中", "完了"]
SUBMISSION_METHODS = ["Teams", "Classroom", "Moodle", "手渡し", "その他"]

# ==========================================
# ページ設定 & CSS
# ==========================================
# 変更点1: layout="wide" を削除し、デフォルト(centered)にすることで横幅を抑える
st.set_page_config(page_title="My Campus", page_icon="🎓")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; color: #333; }
    .stApp { background-color: #f8f9fc; }
    
    /* ------------------------------------------
       タブのスタイル (下線を削除・ボタン風)
       ------------------------------------------ */
    div[data-baseweb="tab-list"] {
        gap: 8px; /* タブ間の隙間 */
        background-color: transparent;
        margin-bottom: 20px;
        border-bottom: none !important; /* リスト全体の下線を削除 */
    }

    button[data-baseweb="tab"] {
        font-size: 1.1rem !important;
        font-weight: bold !important;
        padding: 0.8rem 1rem !important;
        min-height: 50px !important;
        flex: 1;
        background-color: #ffffff;
        border-radius: 10px !important; /* 角丸にする */
        border: 1px solid #f0f0f0 !important; /* 薄い枠線 */
        border-bottom: none !important; /* 下線を削除 */
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* 選択されているタブ */
    button[data-baseweb="tab"][aria-selected="true"] {
        color: white !important;
        background-color: #1a237e !important; /* 選択時は青背景 */
        border: none !important;
        border-bottom: none !important; /* 下線を削除 */
    }

    /* ------------------------------------------
       カードデザイン
       ------------------------------------------ */
    .custom-card { 
        background: white; 
        border-radius: 12px; 
        padding: 18px; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.08); 
        margin-bottom: 12px; 
        border-left: 6px solid #ccc; 
    }
    .border-red { border-left-color: #e53935; }
    .border-orange { border-left-color: #fb8c00; }
    .border-blue { border-left-color: #1e88e5; }
    .border-green { border-left-color: #43a047; }
    
    /* 授業カード */
    .class-card {
        background: white;
        padding: 20px;
        border-radius: 15px; /* 丸みを強く */
        border-top: 5px solid #5c6bc0;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        text-align: center;
        height: 100%;
        margin-bottom: 15px;
    }
    .class-card-empty {
        background: #f1f3f4;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        color: #bbb;
        margin-bottom: 15px;
    }
    
    /* 統計ボックス */
    .metric-container { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        color: white; 
        padding: 20px; 
        border-radius: 15px; 
        text-align: center; 
    }
    .metric-value { font-size: 2.5rem; font-weight: 700; }
    
    /* 横幅の微調整（スマホでの見た目を最適化） */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 700px; /* PCでも広がりすぎないように制限 */
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# Google Sheets 接続・データ処理
# ==========================================
def get_google_sheets_client():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    json_str = st.secrets["gcp_service_account"]["my_key"]
    creds_dict = json.loads(json_str)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def load_data(current_user):
    try:
        client = get_google_sheets_client()
        sheet = client.open("School_DB")
        
        # 時間割
        ws_tt = sheet.worksheet("Timetable")
        df_tt = get_as_dataframe(ws_tt, evaluate_formulas=True).iloc[:4, :6]
        if "Unnamed: 0" in df_tt.columns: df_tt.set_index("Unnamed: 0", inplace=True)
        
        if df_tt.shape != (4, 5):
            df_tt = pd.DataFrame("", index=TIMETABLE_ROWS, columns=TIMETABLE_COLS)
        else:
            df_tt.index = TIMETABLE_ROWS
            df_tt.columns = TIMETABLE_COLS
            df_tt = df_tt.fillna("")
            
        # 宿題
        ws_hw = sheet.worksheet("Homework")
        df_hw = get_as_dataframe(ws_hw, evaluate_formulas=True).dropna(how='all')
        
        # 進捗
        try: ws_prog = sheet.worksheet("Progress")
        except:
            ws_prog = sheet.add_worksheet(title="Progress", rows="1000", cols="3")
            ws_prog.update('A1', [['task_id', 'user', 'status']])
        df_prog = get_as_dataframe(ws_prog, evaluate_formulas=True).dropna(how='all')
        
        homework_list = []
        if not df_hw.empty:
            my_progress = {}
            if not df_prog.empty and 'user' in df_prog.columns:
                my_df = df_prog[df_prog['user'] == current_user]
                my_progress = dict(zip(my_df['task_id'].astype(str), my_df['status']))
            
            for _, row in df_hw.iterrows():
                if pd.isna(row['id']) or str(row['id']) == "": continue
                tid = str(row['id'])
                try:
                    d_str = str(row['due_date']).split(' ')[0]
                    due_date = datetime.strptime(d_str, '%Y-%m-%d').date()
                except: due_date = date.today()
                
                current_status = my_progress.get(tid, "未着手")
                homework_list.append({
                    "id": tid,
                    "subject": str(row['subject']),
                    "content": str(row['content']),
                    "due_date": due_date,
                    "method": str(row['method']),
                    "status": current_status 
                })
        return {'timetable': df_tt, 'homework': homework_list}
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return None

def add_new_task(new_task_data):
    try:
        client = get_google_sheets_client()
        sheet = client.open("School_DB")
        ws_hw = sheet.worksheet("Homework")
        df = get_as_dataframe(ws_hw).dropna(how='all')
        
        new_row = pd.DataFrame([{
            'id': new_task_data['id'],
            'subject': new_task_data['subject'],
            'content': new_task_data['content'],
            'due_date': str(new_task_data['due_date']),
            'method': new_task_data['method'],
            'priority': '中', 
            'status': 'ignored'
        }])
        
        df_export = pd.concat([df, new_row], ignore_index=True)
        set_with_dataframe(ws_hw, df_export)
        return True
    except Exception as e:
        st.error(f"保存エラー: {e}")
        return False

def update_user_status(task_id, user_name, new_status):
    try:
        client = get_google_sheets_client()
        sheet = client.open("School_DB")
        ws_prog = sheet.worksheet("Progress")
        df = get_as_dataframe(ws_prog).dropna(how='all')
        
        if 'task_id' not in df.columns: df = pd.DataFrame(columns=['task_id', 'user', 'status'])
        
        mask = (df['task_id'].astype(str) == str(task_id)) & (df['user'] == user_name)
        if mask.any():
            df.loc[mask, 'status'] = new_status
        else:
            new_row = pd.DataFrame([{'task_id': str(task_id), 'user': user_name, 'status': new_status}])
            df = pd.concat([df, new_row], ignore_index=True)
            
        set_with_dataframe(ws_prog, df)
        return True
    except Exception as e:
        st.error(f"ステータス更新エラー: {e}")
        return False

def save_timetable(timetable_df):
    try:
        client = get_google_sheets_client()
        sheet = client.open("School_DB")
        ws_tt = sheet.worksheet("Timetable")
        ws_tt.clear()
        set_with_dataframe(ws_tt, timetable_df, include_index=True)
    except Exception as e:
        st.error(f"時間割保存エラー: {e}")

# ==========================================
# UI レンダリング関数
# ==========================================
def get_border_and_badge(homework, days_until_due):
    if homework['status'] == "完了": return "border-green", '<span style="color:green">✅ 完了</span>'
    elif days_until_due < 0: return "border-red", f'<span style="color:red">🚨 {abs(days_until_due)}日遅れ</span>'
    elif days_until_due == 0: return "border-orange", '<span style="color:orange">🔥 今日まで</span>'
    else: return "border-blue", f'<span style="color:blue">⏱ あと{days_until_due}日</span>'

def render_homework_card(homework):
    days_until_due = (homework['due_date'] - date.today()).days
    border, badge = get_border_and_badge(homework, days_until_due)
    return f"""
    <div class="custom-card {border}">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-weight:bold; font-size:1.1rem;">{homework['subject']}</div>
            <div>{badge}</div>
        </div>
        <div style="margin:8px 0; color:#444; font-size:1rem;">{homework['content']}</div>
        <div style="font-size:0.85em; color:gray; display:flex; gap:10px;">
            <span>📅 {homework['due_date']}</span>
            <span>📤 {homework['method']}</span>
        </div>
    </div>
    """

def render_class_card_by_day(period, subject):
    """曜日別表示用のカード"""
    if subject and str(subject).strip():
        return f"""
        <div class="class-card">
            <div style="color:gray; font-size:0.85rem; margin-bottom:4px;">{period}</div>
            <div style="font-weight:bold; color:#1a237e; font-size:1.2rem;">{subject}</div>
        </div>
        """
    else:
        return f"""
        <div class="class-card-empty">
            <div style="font-size:0.85rem;">{period}</div>
            <div>-</div>
        </div>
        """

# ==========================================
# 🔑 ログイン処理
# ==========================================
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None
if 'is_guest' not in st.session_state:
    st.session_state.is_guest = False

def login_screen():
    st.markdown("<h1 style='text-align: center;'>🎓 My Campus Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("ユーザー名")
            password = st.text_input("パスワード", type="password")
            submitted = st.form_submit_button("ログイン", use_container_width=True)
            
            if submitted:
                if USER_CREDENTIALS.get(username) == password:
                    st.session_state.logged_in_user = username
                    st.session_state.is_guest = False
                    st.success("ログイン成功")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("認証失敗")
        
        st.markdown("<div style='text-align:center; margin:10px 0; color:gray;'>または</div>", unsafe_allow_html=True)
        if st.button("👁️ ゲストとして閲覧", use_container_width=True):
            st.session_state.logged_in_user = "ゲスト"
            st.session_state.is_guest = True
            st.rerun()

if st.session_state.logged_in_user is None:
    login_screen()
    st.stop()

# ==========================================
# メインアプリ
# ==========================================
current_user = st.session_state.logged_in_user

# サイドバー
with st.sidebar:
    st.markdown(f"### 👤 {current_user}")
    if st.button("🚪 ログアウト"):
        st.session_state.logged_in_user = None
        st.session_state.is_guest = False
        if "init" in st.session_state: del st.session_state.init
        st.rerun()
    st.divider()
    if st.button("🔄 データを更新"):
        if "init" in st.session_state: del st.session_state.init
        st.rerun()

# データ読み込み
if "init" not in st.session_state:
    with st.spinner('データを読み込み中...'):
        loaded = load_data(current_user)
    if loaded:
        st.session_state.timetable_data = loaded['timetable']
        st.session_state.homework_list = loaded['homework']
    else:
        st.session_state.timetable_data = pd.DataFrame("", index=TIMETABLE_ROWS, columns=TIMETABLE_COLS)
        st.session_state.homework_list = []
    st.session_state.init = True

# 統計表示
with st.sidebar:
    incomplete = [hw for hw in st.session_state.homework_list if hw['status'] != '完了']
    urgent = [hw for hw in incomplete if (hw['due_date'] - date.today()).days <= 1]
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-label">未完了タスク</div>
        <div class="metric-value">{len(incomplete)}</div>
    </div>
    """, unsafe_allow_html=True)
    if urgent: st.error(f"🔥 {len(urgent)}件の期限が迫っています")

# ==========================================
# メインコンテンツ表示
# ==========================================

st.markdown(f"""
<h3>お疲れ様です、<br>
<span style='font-size: 1.5em; color: #1a237e;'>{current_user} さん</span> 👋</h3>
""", unsafe_allow_html=True)

# メインタブ（大きく表示）
tab_schedule, tab_homework = st.tabs(["📅 時間割", "📝 宿題管理"])

# --- 時間割タブ ---
with tab_schedule:
    mode = st.radio("モード", ["閲覧", "編集"], horizontal=True, label_visibility="collapsed")
    
    if mode == "閲覧":
        # 今日の曜日を取得 (0=月...6=日)
        today_idx = datetime.now().weekday()
        if today_idx > 4: today_idx = 0
            
        # 曜日の順序並べ替え
        ordered_indices = []
        for i in range(5):
            idx = (today_idx + i) % 5
            ordered_indices.append(idx)
        
        # タブのラベル作成
        tab_labels = []
        for idx in ordered_indices:
            day_char = TIMETABLE_COLS[idx]
            if idx == today_idx:
                tab_labels.append(f"{day_char} (今日)")
            else:
                tab_labels.append(day_char)
        
        # 曜日タブ表示
        day_tabs = st.tabs(tab_labels)
        
        for i, day_tab in enumerate(day_tabs):
            with day_tab:
                original_idx = ordered_indices[i]
                day_name = TIMETABLE_COLS[original_idx]
                
                if day_name in st.session_state.timetable_data.columns:
                    col_data = st.session_state.timetable_data[day_name]
                    for period in TIMETABLE_ROWS:
                        subject = col_data.get(period, "")
                        st.markdown(render_class_card_by_day(period, subject), unsafe_allow_html=True)
                else:
                    st.info("データがありません")
                    
    else: # 編集モード
        if st.session_state.is_guest:
            st.warning("ゲストは編集できません")
            st.dataframe(st.session_state.timetable_data, use_container_width=True)
        else:
            st.markdown("#### ✏️ 時間割の編集")
            edited_df = st.data_editor(st.session_state.timetable_data, use_container_width=True)
            if st.button("保存して共有"):
                save_timetable(edited_df)
                st.session_state.timetable_data = edited_df
                st.success("保存しました")

# --- 宿題タブ ---
with tab_homework:
    if not st.session_state.is_guest:
        with st.expander("✨ タスクを追加", expanded=False):
            with st.form("add_task", clear_on_submit=True):
                c1, c2 = st.columns([2, 1])
                with c1:
                    subject = st.text_input("科目名（必須）", placeholder="例：応用数学A")
                with c2:
                    due_date = st.date_input("期限（必須）", date.today())
                
                content = st.text_area("内容・メモ", height=100, placeholder="教科書 P20〜30 など")
                method = st.radio("提出方法", SUBMISSION_METHODS, horizontal=True)
                
                if st.form_submit_button("追加", type="primary", use_container_width=True):
                    if content and subject:
                        new_task = {
                            "id": str(uuid.uuid4()),
                            "subject": subject,
                            "content": content,
                            "due_date": due_date,
                            "method": method
                        }
                        if add_new_task(new_task):
                            st.success("追加しました")
                            del st.session_state.init
                            st.rerun()
                    else:
                        st.error("科目名と内容を入力してください")
    
    st.write("")
    
    t_inc, t_com = st.tabs(["未完了", "完了済み"])
    
    with t_inc:
        tasks = [h for h in st.session_state.homework_list if h['status'] != '完了']
        if tasks:
            for hw in sorted(tasks, key=lambda x: x['due_date']):
                c1, c2 = st.columns([5, 1])
                c1.markdown(render_homework_card(hw), unsafe_allow_html=True)
                if not st.session_state.is_guest:
                    if c2.button("完了", key=f"done_{hw['id']}", use_container_width=True):
                        update_user_status(hw['id'], current_user, "完了")
                        st.rerun()
        else:
            st.info("未完了のタスクはありません 🎉")
            
    with t_com:
        tasks = [h for h in st.session_state.homework_list if h['status'] == '完了']
        if tasks:
            for hw in sorted(tasks, key=lambda x: x['due_date'], reverse=True):
                st.markdown(render_homework_card(hw), unsafe_allow_html=True)
        else:
            st.info("完了したタスクはありません")