# import streamlit as st
# import pandas as pd
# from datetime import date, datetime
# import uuid
# import gspread
# import json
# import calendar
# from oauth2client.service_account import ServiceAccountCredentials
# from gspread_dataframe import get_as_dataframe, set_with_dataframe


# # ==========================================
# # 定数定義
# # ==========================================

# SUBJECT_LIST = [
#     "現代社会論", "保健・体育4", "実験実習", "ドイツ語", "中国語", "応用数学A", "応用数学B",
#     "物理学A", "物理学B", "計測工学", "技術英語", "電子回路2", "電気回路3",
#     "電磁気学2", "電気電子材料3", "半導体工学2", "コンピュータ工学基礎", "制御工学1",
#     "エレクトロニクス実験2", "法律", "経済", "哲学", "心理学", "現代物理学概論",
#     "英語A", "英語B", "制御工学2", "電気機器", "電力技術", "パワーエレクトロニクス",
#     "信号処理", "電気化学", "センサー工学", "ワイヤレス技術", "エレクトロニクス実験3",
#     "卒業研究", "応用専門概論", "応用専門PBL1", "応用専門PBL2", "物質プロセス基礎",
#     "生活と物質", "社会と環境", "物質デザイン概論", "防災工学", "エルゴノミクス",
#     "インターンシップ", "食品エンジニアリング", "コスメティックス", "バイオテクノロジー",
#     "高純度化技術", "環境モニタリング", "エネルギー変換デバイス", "食と健康のセンサ",
#     "環境対応デバイス", "社会基盤構造", "環境衛生工学", "維持管理工学", "水環境工学",
#     "環境デザイン論", "インクルーシブデザイン", "空間情報学", "環境行動", "その他"
# ]

# TIMETABLE_ROWS = ["1/2限", "3/4限", "5/6限", "7/8限"]
# TIMETABLE_COLS = ["月", "火", "水", "木", "金"]
# WEEKDAYS_JP = ["月", "火", "水", "木", "金", "土", "日"]

# PRIORITY_ORDER = {"高": 0, "中": 1, "低": 2}
# STATUS_OPTIONS = ["未着手", "作業中", "完了"]
# SUBMISSION_METHODS = ["Teams", "Classroom", "Moodle", "手渡し", "その他"]


# # ==========================================
# # Google Sheets 接続
# # ==========================================

# def get_google_sheets_client():
#     """Google Sheetsへの接続クライアントを取得"""
#     scope = [
#         'https://spreadsheets.google.com/feeds',
#         'https://www.googleapis.com/auth/drive'
#     ]
#     json_str = st.secrets["gcp_service_account"]["my_key"]
#     creds_dict = json.loads(json_str)
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     return gspread.authorize(creds)


# def parse_homework_row(row):
#     """宿題データの1行をパース"""
#     if pd.isna(row['id']) or str(row['id']) == "":
#         return None
    
#     # 日付のパース
#     date_str = str(row['due_date']).split(' ')[0]
#     try:
#         due_date = datetime.strptime(date_str, '%Y-%m-%d').date()
#     except:
#         due_date = date.today()
    
#     return {
#         "id": str(row['id']),
#         "subject": str(row['subject']),
#         "content": str(row['content']),
#         "due_date": due_date,
#         "method": str(row['method']),
#         "priority": str(row['priority']),
#         "status": str(row['status'])
#     }


# def load_homework_data(sheet):
#     """宿題データをGoogle Sheetsから読み込む"""
#     ws = sheet.worksheet("Homework")
#     df = get_as_dataframe(ws, evaluate_formulas=True).dropna(how='all')
    
#     homework_list = []
#     if not df.empty:
#         for _, row in df.iterrows():
#             try:
#                 homework = parse_homework_row(row)
#                 if homework:
#                     homework_list.append(homework)
#             except:
#                 continue
    
#     return homework_list


# def load_timetable_data(sheet):
#     """時間割データをGoogle Sheetsから読み込む"""
#     ws = sheet.worksheet("Timetable")
#     df = get_as_dataframe(ws, evaluate_formulas=True)
#     df = df.iloc[:4, :6]
    
#     if "Unnamed: 0" in df.columns:
#         df.set_index("Unnamed: 0", inplace=True)
    
#     # データ形状の確認と初期化
#     if df.shape != (4, 5):
#         df = pd.DataFrame("", index=TIMETABLE_ROWS, columns=TIMETABLE_COLS)
#     else:
#         df.index = TIMETABLE_ROWS
#         df.columns = TIMETABLE_COLS
#         df = df.fillna("")
    
#     return df


# def load_all_data():
#     """すべてのデータをGoogle Sheetsから読み込む"""
#     try:
#         client = get_google_sheets_client()
#         sheet = client.open("School_DB")
        
#         return {
#             'timetable': load_timetable_data(sheet),
#             'homework': load_homework_data(sheet)
#         }
#     except Exception as e:
#         st.error(f"データ読み込みエラー: {e}")
#         return None


# def save_all_data(timetable_df, homework_list):
#     """すべてのデータをGoogle Sheetsに保存"""
#     try:
#         client = get_google_sheets_client()
#         sheet = client.open("School_DB")
        
#         # 宿題データの保存
#         ws_hw = sheet.worksheet("Homework")
#         ws_hw.clear()
        
#         if homework_list:
#             df_export = pd.DataFrame(homework_list)
#             df_export['due_date'] = df_export['due_date'].astype(str)
#             set_with_dataframe(ws_hw, df_export)
#         else:
#             header = [['id', 'subject', 'content', 'due_date', 'method', 'priority', 'status']]
#             ws_hw.update('A1', header)
        
#         # 時間割データの保存
#         ws_tt = sheet.worksheet("Timetable")
#         ws_tt.clear()
#         set_with_dataframe(ws_tt, timetable_df, include_index=True)
        
#     except Exception as e:
#         st.error(f"データ保存エラー: {e}")


# # ==========================================
# # UI ヘルパー関数
# # ==========================================

# def get_border_and_badge(homework, days_until_due):
#     """宿題の状態に応じたボーダー色とバッジを取得"""
#     if homework['status'] == "完了":
#         return "border-green", '<span style="color:green">✅ 完了</span>'
#     elif days_until_due < 0:
#         return "border-red", f'<span style="color:red">🚨 {abs(days_until_due)}日遅れ</span>'
#     elif days_until_due == 0:
#         return "border-orange", '<span style="color:orange">🔥 今日まで</span>'
#     else:
#         return "border-blue", f'<span style="color:blue">⏱ あと{days_until_due}日</span>'


# def render_homework_card(homework):
#     """宿題カードをレンダリング"""
#     days_until_due = (homework['due_date'] - date.today()).days
#     border, badge = get_border_and_badge(homework, days_until_due)
    
#     return f"""
#     <div class="custom-card {border}">
#         <div style="display:flex; justify-content:space-between;">
#             <div>
#                 <b>{homework['subject']}</b>
#             </div>
#             <div>{badge}</div>
#         </div>
#         <div style="margin:10px 0;">{homework['content']}</div>
#         <div style="font-size:0.8em; color:gray;">
#             📅 {homework['due_date']} | 📤 {homework['method']}
#         </div>
#     </div>
#     """


# def render_class_card(period, subject, is_continuation=False):
#     """授業カードをレンダリング"""
#     if subject and str(subject).strip():
#         # 継続授業の場合は薄い表示
#         if is_continuation:
#             return f"""
#             <div style="background:white; padding:15px; border-radius:12px; 
#                         border-top: 5px solid #9fa8da; box-shadow:0 4px 6px rgba(0,0,0,0.05); 
#                         text-align:center; opacity: 0.7;">
#                 <div style="color:gray; font-size:0.8rem;">{period}</div>
#                 <div style="font-weight:bold; color:#5c6bc0;">↓ 継続</div>
#             </div>
#             """
#         else:
#             return f"""
#             <div style="background:white; padding:15px; border-radius:12px; 
#                         border-top: 5px solid #5c6bc0; box-shadow:0 4px 6px rgba(0,0,0,0.05); 
#                         text-align:center;">
#                 <div style="color:gray; font-size:0.8rem;">{period}</div>
#                 <div style="font-weight:bold; color:#1a237e;">{subject}</div>
#             </div>
#             """
#     else:
#         return f"""
#         <div style="background:#f1f3f4; padding:15px; border-radius:12px; 
#                     text-align:center; opacity:0.6;">
#             <div style="color:gray; font-size:0.8rem;">{period}</div>
#             <div>-</div>
#         </div>
#         """


# # ==========================================
# # ページ設定
# # ==========================================

# st.set_page_config(
#     page_title="My Campus | 共有アプリ",
#     page_icon="🎓",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )


# # ==========================================
# # スタイル定義
# # ==========================================

# st.markdown("""
# <style>
#     @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');
    
#     html, body, [class*="css"] {
#         font-family: 'Noto Sans JP', sans-serif;
#         color: #333;
#     }
    
#     .stApp {
#         background-color: #f8f9fc;
#     }
    
#     .custom-card {
#         background: white;
#         border-radius: 16px;
#         padding: 20px;
#         box-shadow: 0 4px 15px rgba(0,0,0,0.05);
#         margin-bottom: 15px;
#         border-left: 5px solid #ccc;
#     }
    
#     .border-red { border-left-color: #e53935; }
#     .border-orange { border-left-color: #fb8c00; }
#     .border-blue { border-left-color: #1e88e5; }
#     .border-green { border-left-color: #43a047; }
    
#     .badge {
#         padding: 4px 12px;
#         border-radius: 20px;
#         font-size: 0.8rem;
#         font-weight: 600;
#         display: inline-block;
#     }
    
#     .badge-prio-高 { background: #ffebee; color: #c62828; }
#     .badge-prio-中 { background: #e3f2fd; color: #1565c0; }
#     .badge-prio-低 { background: #f1f8e9; color: #33691e; }
    
#     .metric-container {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         color: white;
#         padding: 20px;
#         border-radius: 15px;
#         text-align: center;
#     }
    
#     .metric-value {
#         font-size: 2.5rem;
#         font-weight: 700;
#     }
# </style>
# """, unsafe_allow_html=True)


# # ==========================================
# # データ初期化
# # ==========================================

# def initialize_session_state():
#     """セッション状態を初期化"""
#     if "init" not in st.session_state:
#         with st.spinner('Google Sheetsからデータを読み込み中...'):
#             loaded = load_all_data()
        
#         if loaded:
#             st.session_state.timetable_data = loaded['timetable']
#             st.session_state.homework_list = loaded['homework']
#         else:
#             st.session_state.timetable_data = pd.DataFrame(
#                 "", index=TIMETABLE_ROWS, columns=TIMETABLE_COLS
#             )
#             st.session_state.homework_list = []
        
#         st.session_state.init = True


# initialize_session_state()


# # ==========================================
# # サイドバー
# # ==========================================

# with st.sidebar:
#     st.markdown("### 🎓 My Campus")
    
#     if st.button("🔄 データを更新"):
#         del st.session_state.init
#         st.rerun()
    
#     # 統計情報の計算
#     incomplete_tasks = [
#         hw for hw in st.session_state.homework_list 
#         if hw['status'] != '完了'
#     ]
    
#     urgent_tasks = [
#         hw for hw in incomplete_tasks 
#         if (hw['due_date'] - date.today()).days <= 1
#     ]
    
#     st.markdown(f"""
#     <div class="metric-container">
#         <div class="metric-label">未完了タスク</div>
#         <div class="metric-value">{len(incomplete_tasks)}</div>
#     </div>
#     """, unsafe_allow_html=True)
    
#     if urgent_tasks:
#         st.error(f"🔥 **{len(urgent_tasks)}件** の期限が迫っています！")


# # ==========================================
# # メインコンテンツ
# # ==========================================

# st.title("お疲れ様です 👋")
# st.caption("Google Sheets連携中: データはリアルタイムで共有されます")

# tab_schedule, tab_homework = st.tabs(["📅 時間割", "📝 宿題管理"])


# # --- TAB 1: 時間割 ---

# with tab_schedule:
#     today_weekday = WEEKDAYS_JP[datetime.now().weekday()]
#     today_date = datetime.now().strftime('%m/%d')
    
#     mode = st.radio(
#         "表示モード",
#         ["今日の予定", "時間割の編集"],
#         label_visibility="collapsed",
#         horizontal=True
#     )
    
#     if mode == "今日の予定":
#         st.subheader(f"今日の授業 ({today_date} {today_weekday})")
        
#         if today_weekday in st.session_state.timetable_data.columns:
#             schedule = st.session_state.timetable_data[today_weekday]
#             has_class = False
#             cols = st.columns(len(schedule))
            
#             previous_subject = None
#             for idx, (period, subject) in enumerate(schedule.items()):
#                 with cols[idx]:
#                     # 前の時限と同じ授業かチェック
#                     is_continuation = (subject == previous_subject and 
#                                      subject and str(subject).strip())
                    
#                     st.markdown(
#                         render_class_card(period, subject, is_continuation),
#                         unsafe_allow_html=True
#                     )
#                     if subject and str(subject).strip():
#                         has_class = True
                    
#                     previous_subject = subject
            
#             if not has_class:
#                 st.info("本日の授業はありません")
#         else:
#             st.success("今日は休日です")
    
#     else:  # 編集モード
#         st.markdown("#### ✏️ 時間割の編集")
#         st.info("セルをダブルクリックして科目を直接入力できます。")
        
#         edited_df = st.data_editor(
#             st.session_state.timetable_data,
#             use_container_width=True,
#             num_rows="fixed"
#         )
        
#         if st.button("時間割を保存して共有"):
#             st.session_state.timetable_data = edited_df
#             save_all_data(st.session_state.timetable_data, st.session_state.homework_list)
#             st.success("保存しました！")


# # --- TAB 2: 宿題管理 ---

# with tab_homework:
#     # タスク追加フォーム
#     with st.expander("✨ タスクを追加", expanded=False):
#         with st.form("add_task", clear_on_submit=True):
#             # 科目と期限を横並び
#             col1, col2 = st.columns([2, 1])
            
#             with col1:
#                 # 変更点：セレクトボックスのみにし、手入力ボックスを削除
#                 # デフォルトでリストの最初（現代社会論など）を表示
#                 subject = st.selectbox(
#                     "科目（必須）",
#                     SUBJECT_LIST,
#                     index=0
#                 )
            
#             with col2:
#                 due_date = st.date_input("期限（必須）", date.today())
            
#             # 内容・メモ
#             content = st.text_area(
#                 "内容・メモ",
#                 placeholder="詳細を入力（教科書の範囲、提出物の種類など）",
#                 height=80
#             )
            
#             # 提出方法
#             st.write("📤 提出方法")
#             method = st.radio(
#                 "提出方法",
#                 SUBMISSION_METHODS,
#                 horizontal=True,
#                 label_visibility="collapsed"
#             )
            
#             # メインの追加ボタン
#             col_spacer, col_submit = st.columns([3, 1])
#             with col_submit:
#                 submit_clicked = st.form_submit_button("追加", type="primary", use_container_width=True)
            
#             if submit_clicked:
#                 if content and subject:
#                     new_homework = {
#                         "id": str(uuid.uuid4()),
#                         "subject": subject,
#                         "content": content,
#                         "due_date": due_date,
#                         "method": method,
#                         "priority": "中",  # デフォルト値として保持（表示はしない）
#                         "status": "未着手"
#                     }
#                     st.session_state.homework_list.append(new_homework)
#                     save_all_data(st.session_state.timetable_data, st.session_state.homework_list)
#                     st.success("追加しました")
#                     st.rerun()
#                 else:
#                     st.error("内容を入力してください")  # 科目は選択式なので実質必須になった
    
#     # フィルタリング
#     st.write("")
#     filter_status = st.multiselect(
#         "ステータスで絞り込み",
#         STATUS_OPTIONS,
#         default=["未着手", "作業中"]
#     )
    
#     # 宿題リストの表示
#     if st.session_state.homework_list:
#         # ソート: 完了→期限のみ
#         sorted_homework = sorted(
#             st.session_state.homework_list,
#             key=lambda x: (
#                 x['status'] == '完了',
#                 x['due_date']
#             )
#         )
        
#         for hw in sorted_homework:
#             if hw['status'] in filter_status:
#                 col_main, col_action = st.columns([5, 1])
                
#                 with col_main:
#                     st.markdown(render_homework_card(hw), unsafe_allow_html=True)
                
#                 with col_action:
#                     st.write("")
                    
#                     # ステータス変更
#                     current_index = STATUS_OPTIONS.index(hw['status'])
#                     new_status = st.selectbox(
#                         "状態変更",
#                         STATUS_OPTIONS,
#                         index=current_index,
#                         key=f"status_{hw['id']}",
#                         label_visibility="collapsed"
#                     )
                    
#                     # 削除ボタン
#                     if st.button("🗑", key=f"delete_{hw['id']}"):
#                         st.session_state.homework_list = [
#                             x for x in st.session_state.homework_list 
#                             if x['id'] != hw['id']
#                         ]
#                         save_all_data(st.session_state.timetable_data, st.session_state.homework_list)
#                         st.rerun()
                    
#                     # ステータスが変更された場合
#                     if new_status != hw['status']:
#                         hw['status'] = new_status
#                         save_all_data(st.session_state.timetable_data, st.session_state.homework_list)
#                         st.rerun()
#     else:
#         st.info("まだ宿題が登録されていません。上のフォームから追加してください。")


import streamlit as st
import pandas as pd
from datetime import date, datetime
import uuid
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe

# ==========================================
# 定数定義
# ==========================================

# ★ここを利用するメンバーの名前に変更してください
USER_LIST = ["ユーザーA", "ユーザーB", "ユーザーC", "ユーザーD"]

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
    """
    全データを読み込み、ユーザー個別のステータスを結合する
    """
    try:
        client = get_google_sheets_client()
        sheet = client.open("School_DB")
        
        # 1. 時間割
        ws_tt = sheet.worksheet("Timetable")
        df_tt = get_as_dataframe(ws_tt, evaluate_formulas=True).iloc[:4, :6]
        if "Unnamed: 0" in df_tt.columns:
            df_tt.set_index("Unnamed: 0", inplace=True)
        if df_tt.shape != (4, 5):
            df_tt = pd.DataFrame("", index=TIMETABLE_ROWS, columns=TIMETABLE_COLS)
        else:
            df_tt.index = TIMETABLE_ROWS
            df_tt.columns = TIMETABLE_COLS
            df_tt = df_tt.fillna("")
            
        # 2. 課題マスターデータ（全員共通）
        ws_hw = sheet.worksheet("Homework")
        df_hw = get_as_dataframe(ws_hw, evaluate_formulas=True).dropna(how='all')
        
        # 3. 進捗データ（個人別） - シートがない場合は自動作成
        try:
            ws_prog = sheet.worksheet("Progress")
        except:
            ws_prog = sheet.add_worksheet(title="Progress", rows="1000", cols="3")
            ws_prog.update('A1', [['task_id', 'user', 'status']])
            
        df_prog = get_as_dataframe(ws_prog, evaluate_formulas=True).dropna(how='all')
        
        homework_list = []
        if not df_hw.empty:
            # 自分の進捗データだけを抽出して辞書化 {task_id: status}
            my_progress = {}
            if not df_prog.empty and 'user' in df_prog.columns:
                my_df = df_prog[df_prog['user'] == current_user]
                my_progress = dict(zip(my_df['task_id'].astype(str), my_df['status']))
            
            for _, row in df_hw.iterrows():
                if pd.isna(row['id']) or str(row['id']) == "":
                    continue
                
                tid = str(row['id'])
                
                # 日付処理
                try:
                    d_str = str(row['due_date']).split(' ')[0]
                    due_date = datetime.strptime(d_str, '%Y-%m-%d').date()
                except:
                    due_date = date.today()
                
                # ★ここがポイント: ステータスは個人の進捗データから取得。なければ「未着手」
                current_status = my_progress.get(tid, "未着手")
                
                homework_list.append({
                    "id": tid,
                    "subject": str(row['subject']),
                    "content": str(row['content']),
                    "due_date": due_date,
                    "method": str(row['method']),
                    "status": current_status 
                })
                
        return {'timetable': df_tt, 'homework': homework_list, 'raw_progress': df_prog}
        
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return None

def add_new_task(new_task_data):
    """新しい課題をHomeworkシートに追加（ステータスは保存しない）"""
    try:
        client = get_google_sheets_client()
        sheet = client.open("School_DB")
        ws_hw = sheet.worksheet("Homework")
        
        # 既存データを取得して追加
        df = get_as_dataframe(ws_hw).dropna(how='all')
        
        # DataFrameに追加用の行を作成
        new_row = pd.DataFrame([{
            'id': new_task_data['id'],
            'subject': new_task_data['subject'],
            'content': new_task_data['content'],
            'due_date': str(new_task_data['due_date']),
            'method': new_task_data['method'],
            'priority': '中', # 互換性のため残す
            'status': 'ignored' # Homeworkシートのstatusは使わない
        }])
        
        df_export = pd.concat([df, new_row], ignore_index=True)
        set_with_dataframe(ws_hw, df_export)
        return True
    except Exception as e:
        st.error(f"保存エラー: {e}")
        return False

def update_user_status(task_id, user_name, new_status):
    """個人の進捗をProgressシートに保存"""
    try:
        client = get_google_sheets_client()
        sheet = client.open("School_DB")
        ws_prog = sheet.worksheet("Progress")
        
        df = get_as_dataframe(ws_prog).dropna(how='all')
        
        # 必要なカラムがあるか確認
        if 'task_id' not in df.columns:
            df = pd.DataFrame(columns=['task_id', 'user', 'status'])
            
        # 既存のレコードを探す
        mask = (df['task_id'].astype(str) == str(task_id)) & (df['user'] == user_name)
        
        if mask.any():
            # 更新
            df.loc[mask, 'status'] = new_status
        else:
            # 新規追加
            new_row = pd.DataFrame([{
                'task_id': str(task_id), 
                'user': user_name, 
                'status': new_status
            }])
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
    if homework['status'] == "完了":
        return "border-green", '<span style="color:green">✅ 完了</span>'
    elif days_until_due < 0:
        return "border-red", f'<span style="color:red">🚨 {abs(days_until_due)}日遅れ</span>'
    elif days_until_due == 0:
        return "border-orange", '<span style="color:orange">🔥 今日まで</span>'
    else:
        return "border-blue", f'<span style="color:blue">⏱ あと{days_until_due}日</span>'

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
            return f"""
            <div style="background:white; padding:15px; border-radius:12px; 
                        border-top: 5px solid #9fa8da; box-shadow:0 4px 6px rgba(0,0,0,0.05); 
                        text-align:center; opacity: 0.7;">
                <div style="color:gray; font-size:0.8rem;">{period}</div>
                <div style="font-weight:bold; color:#5c6bc0;">↓ 継続</div>
            </div>
            """
        else:
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
# ページ設定・スタイル
# ==========================================

st.set_page_config(page_title="My Campus | 共有アプリ", page_icon="🎓", layout="wide")

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
# サイドバー（ユーザー選択・更新）
# ==========================================

with st.sidebar:
    st.markdown("### 🎓 My Campus")
    
    # ★ ここでユーザーを選択します
    current_user = st.selectbox("👤 ユーザーを選択", USER_LIST)
    
    if st.button("🔄 データを更新"):
        if "init" in st.session_state:
            del st.session_state.init
        st.rerun()

# ==========================================
# データ初期化
# ==========================================

def initialize_session_state():
    # ユーザーが変わった場合もリロードする
    if "current_user" in st.session_state and st.session_state.current_user != current_user:
        if "init" in st.session_state:
            del st.session_state.init

    if "init" not in st.session_state:
        with st.spinner(f'{current_user} さんのデータを読み込み中...'):
            loaded = load_data(current_user)
        
        if loaded:
            st.session_state.timetable_data = loaded['timetable']
            st.session_state.homework_list = loaded['homework']
        else:
            st.session_state.timetable_data = pd.DataFrame("", index=TIMETABLE_ROWS, columns=TIMETABLE_COLS)
            st.session_state.homework_list = []
        
        st.session_state.current_user = current_user
        st.session_state.init = True

initialize_session_state()

# サイドバーの残りの統計情報
with st.sidebar:
    incomplete_tasks = [hw for hw in st.session_state.homework_list if hw['status'] != '完了']
    urgent_tasks = [hw for hw in incomplete_tasks if (hw['due_date'] - date.today()).days <= 1]
    
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

st.title(f"こんにちは、{current_user} さん 👋")
st.caption("課題の追加は全員に共有され、ステータスはあなただけのものです。")

tab_schedule, tab_homework = st.tabs(["📅 時間割", "📝 宿題管理"])

# --- TAB 1: 時間割 ---
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
        else:
            st.success("今日は休日です")
    else:
        st.markdown("#### ✏️ 時間割の編集")
        st.info("セルをダブルクリックして科目を直接入力できます。")
        edited_df = st.data_editor(st.session_state.timetable_data, use_container_width=True, num_rows="fixed")
        if st.button("時間割を保存して共有"):
            save_timetable(edited_df)
            st.session_state.timetable_data = edited_df
            st.success("保存しました！")

# --- TAB 2: 宿題管理 ---
with tab_homework:
    # タスク追加フォーム
    with st.expander("✨ タスクを追加（全員に共有されます）", expanded=False):
        with st.form("add_task", clear_on_submit=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                subject = st.selectbox("科目（必須）", SUBJECT_LIST, index=0)
            with col2:
                due_date = st.date_input("期限（必須）", date.today())
            
            content = st.text_area("内容・メモ", placeholder="詳細を入力...", height=80)
            st.write("📤 提出方法")
            method = st.radio("提出方法", SUBMISSION_METHODS, horizontal=True, label_visibility="collapsed")
            
            col_spacer, col_submit = st.columns([3, 1])
            with col_submit:
                submit_clicked = st.form_submit_button("追加", type="primary", use_container_width=True)
            
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
                else:
                    st.error("内容を入力してください")

    st.write("")
    filter_status = st.multiselect("ステータスで絞り込み", STATUS_OPTIONS, default=["未着手", "作業中"])
    
    if st.session_state.homework_list:
        sorted_homework = sorted(
            st.session_state.homework_list,
            key=lambda x: (x['status'] == '完了', x['due_date'])
        )
        
        for hw in sorted_homework:
            if hw['status'] in filter_status:
                col_main, col_action = st.columns([5, 1])
                with col_main:
                    st.markdown(render_homework_card(hw), unsafe_allow_html=True)
                with col_action:
                    st.write("")
                    current_index = STATUS_OPTIONS.index(hw['status'])
                    
                    # ステータス変更時のキーにuserを含めてユニークにする必要は無いが、念のため
                    new_status = st.selectbox(
                        "状態", STATUS_OPTIONS, index=current_index,
                        key=f"status_{hw['id']}", label_visibility="collapsed"
                    )
                    
                    if new_status != hw['status']:
                        # Google Sheets（Progressシート）を更新
                        if update_user_status(hw['id'], current_user, new_status):
                            hw['status'] = new_status
                            st.rerun()
                        else:
                            st.error("更新に失敗しました")
    else:
        st.info("宿題はありません")