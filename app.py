import streamlit as st
import pandas as pd
from datetime import date, datetime
import uuid
import json
import os

# ==========================================
# 1. 基本設定 & データ管理
# ==========================================
DATA_FILE = "school_data_v2.json"

st.set_page_config(
    page_title="マイキャンパス | スマートマネージャー",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 科目リスト ---
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

# --- データ保存・読込ロジック ---
def save_data():
    try:
        data = {
            'timetable': st.session_state.timetable_data.to_dict(),
            'homework': [
                {**h, 'due_date': h['due_date'].isoformat()} if isinstance(h['due_date'], (date, datetime)) else h
                for h in st.session_state.homework_list
            ]
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存エラー: {e}")

def load_data():
    if not os.path.exists(DATA_FILE): return None
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        hw_list = []
        for h in data.get('homework', []):
            try: h['due_date'] = date.fromisoformat(h['due_date'])
            except: h['due_date'] = date.today()
            hw_list.append(h)
            
        return {'timetable': pd.DataFrame.from_dict(data.get('timetable', {})), 'homework': hw_list}
    except: return None

# --- 初期化 ---
if "init" not in st.session_state:
    loaded = load_data()
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
# 2. デザイン定義 (カスタムCSS)
# ==========================================
st.markdown("""
<style>
    /* 全体のフォントと背景 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans JP', sans-serif;
        color: #333;
    }
    .stApp {
        background-color: #f8f9fc;
    }

    /* タイトル周り */
    h1 { color: #1a237e; font-weight: 700; letter-spacing: -1px; }
    h3 { color: #283593; font-weight: 600; }
    
    /* カードデザイン */
    .custom-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border-left: 5px solid #ccc;
        transition: transform 0.2s;
    }
    .custom-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }
    
    /* ステータス別のボーダー色 */
    .border-red { border-left-color: #e53935; }
    .border-orange { border-left-color: #fb8c00; }
    .border-blue { border-left-color: #1e88e5; }
    .border-green { border-left-color: #43a047; }
    
    /* バッジ */
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
    
    /* メトリックカード */
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(118, 75, 162, 0.4);
    }
    .metric-label { font-size: 0.9rem; opacity: 0.9; }
    .metric-value { font-size: 2.5rem; font-weight: 700; }
    
    /* 入力フォームの微調整 */
    div[data-testid="stExpander"] {
        border: none;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border-radius: 12px;
        background: white;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. サイドバー (ダッシュボード)
# ==========================================
with st.sidebar:
    st.markdown("### 🎓 マイキャンパス")
    
    # 統計情報の計算
    incomplete = [h for h in st.session_state.homework_list if h['status'] != '完了']
    urgent = [h for h in incomplete if (h['due_date'] - date.today()).days <= 1]
    
    # スタイリッシュなメトリック表示
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-label">未完了タスク</div>
        <div class="metric-value">{len(incomplete)}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("") # スペーサー
    
    if urgent:
        st.error(f"🔥 **{len(urgent)}件** の課題が期限間近です！")
    
    st.divider()
    
    # 進捗バー
    total = len(st.session_state.homework_list)
    if total > 0:
        progress = 1.0 - (len(incomplete) / total)
        st.caption(f"全タスク完了率: {int(progress*100)}%")
        st.progress(progress)
    
    st.write("")
    with st.expander("🛠 データ管理"):
        if st.button("今すぐ保存"):
            save_data()
            st.success("保存しました")

# ==========================================
# 4. メインコンテンツ
# ==========================================
# ヘッダーエリア
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("おかえりなさい 👋")
    st.markdown(f"今日: **{date.today().strftime('%Y/%m/%d')}**")

st.write("")

# タブデザイン
tab_schedule, tab_homework = st.tabs(["📅 スマート時間割", "📝 タスク管理"])

# ------------------------------------------
# TAB 1: 時間割 (スマート表示)
# ------------------------------------------
with tab_schedule:
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    today_jp = weekdays[datetime.now().weekday()]
    
    # モード切替を洗練されたUIに
    col_mode, _ = st.columns([2, 5])
    with col_mode:
        mode = st.radio("表示モード", ["今日の授業", "週間編集"], label_visibility="collapsed", horizontal=True)
    
    if mode == "今日の授業":
        st.subheader(f"📅 今日の授業 ({today_jp})")
        
        if today_jp in st.session_state.timetable_data.columns:
            schedule = st.session_state.timetable_data[today_jp]
            has_class = False
            
            # グリッドレイアウトで授業カードを表示
            cols = st.columns(len(schedule))
            for idx, (period, subj) in enumerate(schedule.items()):
                if subj and subj.strip():
                    has_class = True
                    with st.container():
                        st.markdown(f"""
                        <div style="background:white; padding:15px; border-radius:12px; border-top: 5px solid #5c6bc0; box-shadow:0 4px 6px rgba(0,0,0,0.05); height:100%; text-align:center;">
                            <div style="color:gray; font-size:0.8rem; margin-bottom:5px;">{period}</div>
                            <div style="font-weight:bold; font-size:1.1rem; color:#1a237e;">{subj}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    # 空きコマ表示
                    st.markdown(f"""
                    <div style="background:#f1f3f4; padding:15px; border-radius:12px; height:100%; text-align:center; opacity:0.6;">
                        <div style="color:gray; font-size:0.8rem;">{period}</div>
                        <div style="font-size:0.9rem;">空きコマ</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            if not has_class:
                st.info("今日は授業がありません。自習や研究に集中しましょう！")
        else:
            st.success("休日はリフレッシュしましょう！ ☕")
            
    else:
        st.markdown("#### ✏️ 週間スケジュールの編集")
        st.markdown("セルをダブルクリックして科目を編集します。")
        edited_df = st.data_editor(
            st.session_state.timetable_data,
            column_config={c: st.column_config.SelectboxColumn(c, options=SUBJECT_LIST) for c in ["月", "火", "水", "木", "金"]},
            use_container_width=True,
            height=300
        )
        if not edited_df.equals(st.session_state.timetable_data):
            st.session_state.timetable_data = edited_df
            save_data()

# ------------------------------------------
# TAB 2: 宿題管理 (モダンリスト)
# ------------------------------------------
with tab_homework:
    # 新規登録フォーム（アコーディオン）
    with st.expander("✨ 新しいタスクを追加する", expanded=False):
        with st.form("add_task", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            subj = c1.selectbox("科目", SUBJECT_LIST)
            prio = c2.selectbox("優先度", ["高", "中", "低"])
            meth = c3.selectbox("提出方法", ["Teams", "Classroom", "Moodle", "手渡し", "その他"])
            
            content = st.text_input("課題の内容 (例: p.30 演習問題)")
            dd = st.date_input("提出期限", date.today())
            
            if st.form_submit_button("タスクを作成"):
                if not content:
                    st.warning("内容を入力してください")
                else:
                    st.session_state.homework_list.append({
                        "id": str(uuid.uuid4()),
                        "subject": subj, "content": content,
                        "due_date": dd, "method": meth,
                        "priority": prio, "status": "未着手"
                    })
                    save_data()
                    st.rerun()

    st.write("")
    
    # フィルタリング機能
    c_filter, _ = st.columns([2, 3])
    with c_filter:
        status_filter = st.multiselect("状態フィルター", ["未着手", "作業中", "完了"], default=["未着手", "作業中"])

    # リスト表示ロジック
    if not st.session_state.homework_list:
        st.info("タスクはありません。素晴らしい！ 🎉")
    else:
        # ソート: 完了 > 期限 > 優先度
        prio_map = {"高": 0, "中": 1, "低": 2}
        sorted_hw = sorted(
            st.session_state.homework_list,
            key=lambda x: (x['status'] == '完了', x['due_date'], prio_map[x['priority']])
        )
        
        for hw in sorted_hw:
            if hw['status'] in status_filter:
                days_left = (hw['due_date'] - date.today()).days
                
                # スタイル分岐
                if hw['status'] == "完了":
                    border_class = "border-green"
                    status_badge = '<span style="color:#43a047; font-weight:bold;">✅ 完了</span>'
                    bg_style = "opacity: 0.7;"
                elif days_left < 0:
                    border_class = "border-red"
                    status_badge = f'<span style="color:#e53935; font-weight:bold;">🚨 {abs(days_left)}日遅延</span>'
                    bg_style = ""
                elif days_left == 0:
                    border_class = "border-orange"
                    status_badge = '<span style="color:#fb8c00; font-weight:bold;">🔥 今日まで</span>'
                    bg_style = ""
                else:
                    border_class = "border-blue"
                    status_badge = f'<span style="color:#1e88e5; font-weight:bold;">⏱ あと{days_left}日</span>'
                    bg_style = ""

                # 高級カードUIのレンダリング
                with st.container():
                    c_main, c_action = st.columns([5, 1])
                    
                    with c_main:
                        st.markdown(f"""
                        <div class="custom-card {border_class}" style="{bg_style}">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                <div>
                                    <span class="badge badge-prio-{hw['priority']}">{hw['priority']}</span>
                                    <span style="font-weight:bold; font-size:1.1rem; margin-left:8px;">{hw['subject']}</span>
                                </div>
                                <div style="font-size:0.9rem;">{status_badge}</div>
                            </div>
                            <div style="font-size:1rem; margin-bottom:10px;">{hw['content']}</div>
                            <div style="font-size:0.8rem; color:#666; display:flex; gap:15px;">
                                <span>📅 期限: <b>{hw['due_date']}</b></span>
                                <span>📤 提出: <b>{hw['method']}</b></span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # アクションボタン（シンプルに配置）
                    with c_action:
                        st.write("") # 上部余白
                        current_idx = ["未着手", "作業中", "完了"].index(hw['status'])
                        new_status = st.selectbox(
                            "状態", ["未着手", "作業中", "完了"], 
                            index=current_idx, 
                            key=f"sel_{hw['id']}", 
                            label_visibility="collapsed"
                        )
                        
                        if st.button("🗑", key=f"del_{hw['id']}", help="削除"):
                            st.session_state.homework_list = [x for x in st.session_state.homework_list if x['id'] != hw['id']]
                            save_data()
                            st.rerun()
                        
                        # ステータス変更検知
                        if new_status != hw['status']:
                            hw['status'] = new_status
                            save_data()
                            st.rerun()