import streamlit as st
import pandas as pd
from datetime import date, datetime
import uuid
import json
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe

# ==========================================
# 🔐 ユーザー認証設定（ここを自由に書き換えてください）
# ==========================================

# ユーザー名: パスワード の組み合わせ
USER_CREDENTIALS = {
    "佐藤": "1111",
    "鈴木": "2222",
    "田中": "3333",
    "管理者": "admin"
}

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

STATUS_OPTIONS = ["未着手", "作業中", "完了"]
SUBMISSION_METHODS = ["Teams", "Classroom", "Moodle", "手渡し", "その他"]

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
        
        ws_tt = sheet.worksheet("Timetable")
        df_tt = get_as_dataframe(ws_tt, evaluate_formulas=True).iloc[:4, :6]
        if "Unnamed: 0" in df_tt.columns: df_tt.set_index("Unnamed: 0", inplace=True)
        if df_tt.shape != (4, 5): df_tt = pd.DataFrame("", index=TIMETABLE_ROWS, columns=TIMETABLE_COLS)
        else:
            df_tt.index = TIMETABLE_ROWS
            df_tt.columns = TIMETABLE_COLS
            df_tt = df_tt.fillna("")
            
        ws_hw = sheet.worksheet("Homework")
        df_hw = get_as_dataframe(ws_hw, evaluate_formulas=True).dropna(how='all')
        
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
        if mask.any(): df.loc[mask, 'status'] = new_status
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
# UI ヘルパー
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
        <div style="display:flex; justify-content:space-between;">
            <div><b>{homework['subject']}</b></div>
            <div>{badge}</div>
        </div>
        <div style="margin:10px 0;">{homework['content']}</div>
        <div style="font-size:0.8em; color:gray;">
            📅 {homework['due_date']} | 📤 {homework['method']}
        </div>
    </div>
    """

def render_class_card(period, subject, is_continuation=False):
    if subject and str(subject).strip():
        if is_continuation:
            return f"""<div style="background:white; padding:15px; border-radius:12px; border-top: 5px solid #9fa8da; box-shadow:0 4px 6px rgba(0,0,0,0.05); text-align:center; opacity: 0.7;"><div style="color:gray; font-size:0.8rem;">{period}</div><div style="font-weight:bold; color:#5c6bc0;">↓ 継続</div></div>"""
        else:
            return f"""<div style="background:white; padding:15px; border-radius:12px; border-top: 5px solid #5c6bc0; box-shadow:0 4px 6px rgba(0,0,0,0.05); text-align:center;"><div style="color:gray; font-size:0.8rem;">{period}</div><div style="font-weight:bold; color:#1a237e;">{subject}</div></div>"""
    else:
        return f"""<div style="background:#f1f3f4; padding:15px; border-radius:12px; text-align:center; opacity:0.6;"><div style="color:gray; font-size:0.8rem;">{period}</div><div>-</div></div>"""

st.set_page_config(page_title="My Campus", page_icon="🎓", layout="wide")

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
    .metric-container { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 15px; text-align: center; }
    .metric-value { font-size: 2.5rem; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 🔑 ログイン処理
# ==========================================

if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None
if 'is_guest' not in st.session_state:
    st.session_state.is_guest = False

def login():
    st.markdown("<h1 style='text-align: center;'>🎓 My Campus Login</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("ユーザー名", placeholder="ユーザー名を入力してください")
            password = st.text_input("パスワード", type="password", placeholder="パスワードを入力してください")
            submitted = st.form_submit_button("ログイン", use_container_width=True)
            
            if submitted:
                if username.strip() == "":
                    st.error("ユーザー名を入力してください")
                elif USER_CREDENTIALS.get(username) == password:
                    st.session_state.logged_in_user = username
                    st.session_state.is_guest = False
                    st.success("ログイン成功！")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("ユーザー名またはパスワードが間違っています")
        
        st.divider()
        st.markdown("<p style='text-align: center; color: gray;'>または</p>", unsafe_allow_html=True)
        
        if st.button("👁️ ゲストとして閲覧", use_container_width=True):
            st.session_state.logged_in_user = "ゲスト"
            st.session_state.is_guest = True
            st.info("ゲストモードでログインしました（閲覧のみ）")
            time.sleep(0.5)
            st.rerun()

# ログインしていない場合はログイン画面を表示して処理終了
if st.session_state.logged_in_user is None:
    login()
    st.stop()  # ここでスクリプトを止める

# ==========================================
# 以下、ログイン後のメインアプリ
# ==========================================

current_user = st.session_state.logged_in_user

# --- サイドバー ---
with st.sidebar:
    if st.session_state.is_guest:
        st.markdown("### 👁️ ゲスト（閲覧のみ）")
        st.info("閲覧モードです。編集するにはログインしてください。")
    else:
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

# --- データ読み込み ---
if "init" not in st.session_state:
    with st.spinner(f'{current_user} さんのデータを読み込み中...'):
        loaded = load_data(current_user)
    if loaded:
        st.session_state.timetable_data = loaded['timetable']
        st.session_state.homework_list = loaded['homework']
    else:
        st.session_state.timetable_data = pd.DataFrame("", index=TIMETABLE_ROWS, columns=TIMETABLE_COLS)
        st.session_state.homework_list = []
    st.session_state.init = True

# --- サイドバー統計 ---
with st.sidebar:
    incomplete_tasks = [hw for hw in st.session_state.homework_list if hw['status'] != '完了']
    urgent_tasks = [hw for hw in incomplete_tasks if (hw['due_date'] - date.today()).days <= 1]
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-label">未完了タスク</div>
        <div class="metric-value">{len(incomplete_tasks)}</div>
    </div>
    """, unsafe_allow_html=True)
    if urgent_tasks: st.error(f"🔥 **{len(urgent_tasks)}件** の期限が迫っています！")


# --- メインコンテンツ ---
st.title(f"お疲れ様です、{current_user} さん 👋")

tab_schedule, tab_homework = st.tabs(["📅 時間割", "📝 宿題管理"])

with tab_schedule:
    today_weekday = WEEKDAYS_JP[datetime.now().weekday()]
    today_date = datetime.now().strftime('%m/%d')
    mode = st.radio("表示モード", ["今日の予定", "時間割の編集"], label_visibility="collapsed", horizontal=True)
    
    if mode == "今日の予定":
        st.subheader(f"今日の授業 ({today_date} {today_weekday})")
        if today_weekday in st.session_state.timetable_data.columns:
            schedule = st.session_state.timetable_data[today_weekday]
            has_class = False
            cols = st.columns(len(schedule))
            previous_subject = None
            for idx, (period, subject) in enumerate(schedule.items()):
                with cols[idx]:
                    is_continuation = (subject == previous_subject and subject and str(subject).strip())
                    st.markdown(render_class_card(period, subject, is_continuation), unsafe_allow_html=True)
                    if subject and str(subject).strip(): has_class = True
                    previous_subject = subject
            if not has_class: st.info("本日の授業はありません")
        else: st.success("今日は休日です")
    else:
        if st.session_state.is_guest:
            st.warning("⚠️ ゲストユーザーは時間割を編集できません")
            st.dataframe(st.session_state.timetable_data, use_container_width=True)
        else:
            st.markdown("#### ✏️ 時間割の編集")
            edited_df = st.data_editor(st.session_state.timetable_data, use_container_width=True, num_rows="fixed")
            if st.button("時間割を保存して共有"):
                save_timetable(edited_df)
                st.session_state.timetable_data = edited_df
                st.success("保存しました！")

with tab_homework:
    if not st.session_state.is_guest:
        with st.expander("✨ タスクを追加（全員に共有されます）", expanded=False):
            with st.form("add_task", clear_on_submit=True):
                col1, col2 = st.columns([2, 1])
                with col1: subject = st.selectbox("科目（必須）", SUBJECT_LIST, index=0)
                with col2: due_date = st.date_input("期限（必須）", date.today())
                content = st.text_area("内容・メモ", placeholder="詳細を入力...", height=80)
                st.write("📤 提出方法")
                method = st.radio("提出方法", SUBMISSION_METHODS, horizontal=True, label_visibility="collapsed")
                col_spacer, col_submit = st.columns([3, 1])
                with col_submit: submit_clicked = st.form_submit_button("追加", type="primary", use_container_width=True)
                
                if submit_clicked:
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
                    else: st.error("内容を入力してください")
    else:
        st.info("👁️ ゲストモードでは宿題の追加・編集はできません（閲覧のみ）")

    st.write("")
    filter_status = st.multiselect("ステータスで絞り込み", STATUS_OPTIONS, default=["未着手", "作業中"])
    if st.session_state.homework_list:
        sorted_homework = sorted(st.session_state.homework_list, key=lambda x: (x['status'] == '完了', x['due_date']))
        for hw in sorted_homework:
            if hw['status'] in filter_status:
                col_main, col_action = st.columns([4, 1])
                with col_main: st.markdown(render_homework_card(hw), unsafe_allow_html=True)
                with col_action:
                    st.write("")
                    if st.session_state.is_guest:
                        st.markdown(f"<div style='text-align:center; color:gray; font-size:0.9em;'>{hw['status']}</div>", unsafe_allow_html=True)
                    else:
                        if hw['status'] != "完了":
                            if st.button("✅ 完了", key=f"btn_{hw['id']}", use_container_width=True, type="primary"):
                                if update_user_status(hw['id'], current_user, "完了"):
                                    del st.session_state.init
                                    st.rerun()
                        else:
                            st.markdown("<div style='text-align:center; color:green; font-weight:bold;'>✓</div>", unsafe_allow_html=True)
    else: st.info("宿題はありません")