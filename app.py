import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import time
import requests
import re

# ==========================================
# 1. 頁面基礎設定與 CSS 美化
# ==========================================
st.set_page_config(
    page_title="539 數據戰情室 PRO",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🍊"
)

# 愛馬仕配色定義
hermes_orange = "#F37021"
black = "#1A1A1A"
text_color = "#333333"

st.markdown(f"""
    <style>
    /* 全局字體：現代無襯線體 */
    html, body, [class*="css"] {{
        font-family: "Helvetica Neue", Helvetica, "PingFang TC", "Microsoft JhengHei", Arial, sans-serif !important;
        color: {text_color};
    }}

    /* 標題設計 */
    h1 {{
        color: {black};
        font-weight: 900 !important;
        letter-spacing: -1px;
        text-align: center;
        border-bottom: 4px solid {hermes_orange};
        padding-bottom: 20px;
        margin-bottom: 30px;
        font-size: 2.5rem !important;
    }}
    
    h2 {{
        border-left: 5px solid {hermes_orange};
        padding-left: 15px;
        margin-top: 30px;
        font-weight: 700 !important;
        color: {black};
    }}
    
    /* 側邊欄優化 */
    section[data-testid="stSidebar"] {{
        background-color: #F8F9FA;
        border-right: 1px solid #E9ECEF;
    }}
    
    /* 側邊欄小球 */
    .sidebar-ball {{
        display: inline-block;
        width: 32px;
        height: 32px;
        line-height: 32px;
        border-radius: 50%;
        background-color: {hermes_orange};
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 14px;
        margin: 3px;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.2);
    }}
    
    /* 狀態標籤 */
    .status-badge {{
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        color: white;
        display: inline-block;
        margin-left: 5px;
    }}
    .status-hot {{ background-color: #FF4B4B; }}
    .status-cold {{ background-color: #4B9EFF; }}
    .status-normal {{ background-color: #888; }}

    /* 指標卡 (Metrics) */
    div[data-testid="metric-container"] {{
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        transition: transform 0.2s;
    }}
    div[data-testid="metric-container"]:hover {{
        transform: translateY(-2px);
        border-color: {hermes_orange};
    }}

    /* 預測大球 */
    .lotto-ball-lg {{
        background: {hermes_orange};
        color: white;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        font-weight: 800;
        box-shadow: 0 4px 10px rgba(243, 112, 33, 0.4);
        margin: 0 8px;
        border: 3px solid #FFF;
    }}
    
    .lotto-ball-grey {{
        background: #6c757d;
        color: white;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        font-weight: 800;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin: 0 8px;
        border: 3px solid #FFF;
    }}
    
    /* 評分大數字 */
    .score-big {{
        font-size: 100px;
        font-weight: 900;
        color: {hermes_orange};
        line-height: 1;
        font-family: 'Arial Black', sans-serif;
    }}
    
    /* 按鈕 */
    .stButton > button {{
        background-color: {black};
        color: #FFFFFF;
        border-radius: 6px;
        border: none;
        font-weight: 600;
        transition: background-color 0.3s;
    }}
    .stButton > button:hover {{
        background-color: {hermes_orange};
        color: #FFF;
    }}
    
    /* 表格 */
    thead tr th {{
        background-color: #F8F9FA !important;
        color: #444 !important;
        font-weight: 700 !important;
        border-bottom: 2px solid {hermes_orange} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>539 頂級數據分析室</h1>", unsafe_allow_html=True)

# ==========================================
# 2. 資料處理與爬蟲核心
# ==========================================
CSV_FILE = '539_data.csv'

@st.cache_data
def load_and_process_data():
    try:
        # 讀取 CSV，確保所有欄位先以字串讀取避免格式跑掉
        df = pd.read_csv(CSV_FILE, encoding='utf-8', dtype=str)
        
        # 欄位對應清洗
        cols_map = {
            '年份': 'Year', '日期': 'Date', '期數': 'Draw_Num',
            '球號 1': 'N1', '球號 1': 'N1',
            '球號 2': 'N2', '球號 2': 'N2',
            '球號 3': 'N3', '球號 3': 'N3',
            '球號 4': 'N4', '球號 4': 'N4',
            '球號 5': 'N5', '球號 5': 'N5',
            '總期數': 'Total_ID'
        }
        
        clean_cols = {}
        for c in df.columns:
            clean_c = c.strip()
            if clean_c in cols_map:
                clean_cols[c] = cols_map[clean_c]
        
        df = df.rename(columns=clean_cols)
        
        # 確保必要欄位存在，轉換數字
        num_cols = ['N1', 'N2', 'N3', 'N4', 'N5']
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 清除無效行
        df = df.dropna(subset=num_cols)
        df = df.reset_index(drop=True)
        
        # 特徵工程
        df['Sum'] = df[num_cols].sum(axis=1)
        df['Big_Count'] = df[num_cols].apply(lambda x: sum(n >= 20 for n in x), axis=1)
        df['Odd_Count'] = df[num_cols].apply(lambda x: sum(n % 2 != 0 for n in x), axis=1)
        
        def check_consecutive(row):
            nums = sorted(row.values)
            diffs = np.diff(nums)
            return 1 if np.any(diffs == 1) else 0
        df['Has_Consecutive'] = df[num_cols].apply(check_consecutive, axis=1)

        return df, num_cols
    except Exception as e:
        st.error(f"讀取資料錯誤: {e}")
        return pd.DataFrame(), []

# 強健版爬蟲更新函數
def update_data_from_web():
    url = "https://www.pilio.idv.tw/lto539/list539APP.asp"
    
    try:
        # 1. 讀取現有 CSV (確保格式一致)
        std_columns = ['總期數', '年份', '日期', '期數', '球號 1', '球號 2', '球號 3', '球號 4', '球號 5', '出牌次數', '數字', '次數高至低']
        try:
            current_csv = pd.read_csv(CSV_FILE, dtype=str)
            current_csv.columns = [c.strip() for c in current_csv.columns]
            
            # 補齊缺失欄位
            for col in std_columns:
                if col not in current_csv.columns:
                    current_csv[col] = ""
            current_csv = current_csv[std_columns] # 排序
            
            # 取得最後日期
            if not current_csv.empty:
                # 排除空行
                valid_csv = current_csv.dropna(subset=['年份', '日期'])
                if not valid_csv.empty:
                    last_row = valid_csv.iloc[-1]
                    d_str = str(last_row['日期']).replace('月', '/').replace('日', '')
                    last_date_str = f"{last_row['年份']}/{d_str}"
                    last_record_date = pd.to_datetime(last_date_str)
                    
                    try:
                        last_total_id = int(last_row['總期數'])
                    except:
                        last_total_id = len(current_csv)
                    try:
                        last_draw_id = int(last_row['期數'])
                    except:
                        last_draw_id = 0
                else:
                    raise ValueError("Empty Data")
            else:
                raise ValueError("Empty CSV")
                
        except:
            # 如果讀取失敗或為空，設初始值
            last_record_date = pd.to_datetime("2000/01/01")
            last_total_id = 0
            last_draw_id = 0
            current_csv = pd.DataFrame(columns=std_columns)

        # 2. 抓取網頁資料
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.encoding = 'big5'
        
        # 強制無表頭讀取
        dfs = pd.read_html(response.text, header=None)
        target_df = None
        for df in dfs:
            if df.shape[1] == 2: # 找兩欄的表格
                sample = df.head(3).to_string()
                if "/" in sample and "," in sample:
                    target_df = df
                    break
        
        if target_df is None:
            return "❌ 抓不到網頁表格，請檢查網站結構"

        # 3. 解析新資料
        new_rows = []
        for index, row in target_df.iterrows():
            try:
                date_raw = str(row[0]) # 第1欄 日期
                nums_raw = str(row[1]) # 第2欄 號碼
                
                date_match = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', date_raw)
                if not date_match: continue
                
                current_date = pd.to_datetime(date_match.group(0))
                
                # 若網頁日期 <= CSV日期，跳過
                if current_date <= last_record_date:
                    continue
                
                # 解析號碼
                nums = [n.strip() for n in nums_raw.replace('，', ',').split(',') if n.strip().isdigit()]
                if len(nums) != 5: continue
                
                new_rows.append({
                    'dt': current_date,
                    '年份': str(current_date.year),
                    '日期': f"{current_date.month}月{current_date.day}日",
                    '球號 1': nums[0], '球號 2': nums[1], '球號 3': nums[2], '球號 4': nums[3], '球號 5': nums[4]
                })
            except:
                continue
        
        if not new_rows:
            return "✅ 資料已是最新"

        # 4. 合併與存檔
        new_rows.sort(key=lambda x: x['dt'])
        
        rows_to_add = []
        for item in new_rows:
            last_total_id += 1
            last_draw_id += 1
            
            row_data = {
                '總期數': str(last_total_id),
                '年份': item['年份'],
                '日期': item['日期'],
                '期數': str(last_draw_id),
                '球號 1': item['球號 1'],
                '球號 2': item['球號 2'],
                '球號 3': item['球號 3'],
                '球號 4': item['球號 4'],
                '球號 5': item['球號 5'],
                '出牌次數': '', '數字': '', '次數高至低': ''
            }
            rows_to_add.append(row_data)
            
        df_new = pd.DataFrame(rows_to_add)
        
        # 確保順序
        df_new = df_new[std_columns]
        
        # 合併
        final_df = pd.concat([current_csv, df_new], ignore_index=True)
        
        # 存檔
        final_df.to_csv(CSV_FILE, index=False, encoding='utf-8')
        st.cache_data.clear()
        
        return f"🎉 成功更新 {len(rows_to_add)} 筆資料！(最新: {new_rows[-1]['年份']}/{new_rows[-1]['日期']})"

    except Exception as e:
        return f"❌ 更新錯誤: {str(e)}"

# ==========================================
# 3. 主程式邏輯
# ==========================================

# 載入資料
df, num_cols = load_and_process_data()

if df.empty:
    st.warning("請確認 '539_data.csv' 檔案是否存在。")
    st.stop()

# 全域變數
total_draws = len(df)
last_draw = df.iloc[-1]
last_nums = last_draw[num_cols].astype(int).tolist()

# --- 側邊欄設計 ---
st.sidebar.markdown(f"<h3 style='text-align:center; color:#555;'>戰情控制台</h3>", unsafe_allow_html=True)

# 更新按鈕
if st.sidebar.button("🔄 線上更新最新開獎"):
    with st.sidebar.status("連線中...", expanded=True) as status:
        msg = update_data_from_web()
        if "成功" in msg:
            status.update(label="更新完成", state="complete", expanded=False)
            st.sidebar.success(msg)
            time.sleep(1)
            st.rerun()
        elif "已是最新" in msg:
            status.update(label="無需更新", state="complete", expanded=False)
            st.sidebar.info(msg)
        else:
            status.update(label="錯誤", state="error")
            st.sidebar.error(msg)

# 最新開獎卡片
last_nums_html = "".join([f"<span class='sidebar-ball'>{n}</span>" for n in last_nums])
st.sidebar.markdown(f"""
<div style="background-color: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center; margin-bottom: 20px; border: 1px solid #eee;">
    <div style="font-size: 11px; color: #999; margin-bottom: 5px;">LATEST DRAW ({last_draw['Date']})</div>
    <div style="display: flex; justify-content: center; flex-wrap: wrap;">{last_nums_html}</div>
</div>
""", unsafe_allow_html=True)

# 資料過濾
with st.sidebar.expander("📅 資料時光機 (篩選年份)", expanded=False):
    all_years = sorted(df['Year'].unique().tolist(), reverse=True)
    selected_years = st.multiselect("選擇年份 (留空則分析所有資料)：", all_years)
    
    if selected_years:
        current_df = df[df['Year'].isin(selected_years)]
        st.caption(f"已篩選 {len(current_df)} 筆資料")
    else:
        current_df = df
        st.caption(f"分析全歷史 {len(df)} 期")

current_total_draws = len(current_df)

# 號碼快搜
st.sidebar.markdown("---")
st.sidebar.markdown("#### 🔍 號碼快搜")
quick_search_num = st.sidebar.number_input("輸入號碼查看狀態", 1, 39, 1, label_visibility="collapsed")

if current_total_draws > 0:
    is_hit = current_df[num_cols].isin([quick_search_num]).any(axis=1)
    if is_hit.sum() > 0:
        # 計算遺漏 (以篩選資料的最後一筆為準)
        last_hit_pos = np.where(is_hit)[0][-1] 
        draws_since = (len(current_df) - 1) - last_hit_pos
        recent_freq = current_df.tail(30)[num_cols].isin([quick_search_num]).any(axis=1).sum()
        
        status_html = ""
        if recent_freq >= 5: status_html = "<span class='status-badge status-hot'>🔥 熱門</span>"
        elif draws_since > 15: status_html = "<span class='status-badge status-cold'>🧊 遺漏</span>"
        else: status_html = "<span class='status-badge status-normal'>一般</span>"
        
        st.sidebar.markdown(f"""
        <div style="font-size: 14px; margin-top: 5px;">
            狀態：{status_html}<br>
            目前遺漏：<b>{draws_since}</b> 期<br>
            近30期開出：<b>{recent_freq}</b> 次
        </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.write("此號碼在選定範圍內未出現")

# 我的關注
st.sidebar.markdown("---")
st.sidebar.markdown("#### ⭐ 我的關注")
watchlist = st.sidebar.multiselect("釘選常追號碼", list(range(1, 40)), default=[1, 8])

if watchlist and current_total_draws > 0:
    st.sidebar.markdown("<div style='font-size:12px; color:#888; margin-bottom:5px;'>近 30 期出現次數</div>", unsafe_allow_html=True)
    for num in watchlist:
        freq = current_df.tail(30)[num_cols].isin([num]).any(axis=1).sum()
        st.sidebar.progress(min(freq / 10, 1.0), text=f"{num} 號：{freq} 次")

st.sidebar.markdown("---")
analysis_range = st.sidebar.slider("趨勢圖表顯示期數", 10, 100, 50)

# ==========================================
# 4. 主要內容分頁
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 號碼健檢",
    "🔮 智能預測", 
    "🗺️ 趨勢地圖", 
    "💾 時光機回測",
    "📊 市場概況"
])

# --- TAB 1: 號碼健檢 ---
with tab1:
    st.markdown("## 號碼健康度檢查")
    col_input, col_score = st.columns([1, 1])
    
    with col_input:
        user_nums = st.multiselect(
            "請選 5 個號碼：",
            options=list(range(1, 40)),
            max_selections=5,
            default=[1, 8, 17, 26, 35]
        )
    
    if len(user_nums) == 5:
        u_nums = sorted(user_nums)
        u_sum = sum(u_nums)
        u_odd = sum(1 for n in u_nums if n % 2 != 0)
        u_consecutive = 1 if np.any(np.diff(u_nums) == 1) else 0
        hist_count = df.apply(lambda row: set(row[num_cols]).issuperset(set(u_nums)), axis=1).sum()
        
        score = 60 
        reasons = []
        
        if 80 <= u_sum <= 120: 
            score += 10
            reasons.append("✅ **總和漂亮**：80-120 是最常開出的黃金區間。")
        else: 
            score -= 10
            reasons.append("⚠️ **總和極端**：數字總和太大或太小，機率較低。")
        
        if u_odd in [2, 3]: 
            score += 10
            reasons.append("✅ **單雙平衡**：單數雙數分佈很平均。")
        else: 
            score -= 10
            reasons.append("⚠️ **單雙失衡**：全單或全雙，屬於極端牌型。")
        
        hot_count = 0
        for n in u_nums:
            recent_hits = current_df.tail(30)[num_cols].isin([n]).any(axis=1).sum()
            if recent_hits >= 5: hot_count += 1
        
        if 1 <= hot_count <= 3: 
            score += 10
            reasons.append("✅ **冷熱適中**：有熱門號帶路，也有冷門號補位。")
        elif hot_count == 0: 
            score -= 5
            reasons.append("❄️ **太冷門了**：選的全是最近不常開的號碼。")
        elif hot_count >= 4: 
            score -= 5
            reasons.append("🔥 **太熱門了**：選的全是最近一直開的號碼。")
        
        if hist_count > 0: 
            score += 5
            reasons.append(f"📜 **歷史認證**：這組牌在歷史上中過 {hist_count} 次頭獎！")
        else:
            reasons.append("🆕 **全新組合**：歷史上從未同時開出過這 5 個號碼。")
        
        score = max(0, min(100, score))
        
        with col_score:
            st.markdown(f"""
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                <div class="score-big">{score}</div>
                <div style="color: #666; font-size: 18px; margin-top: -10px;">AI 綜合評分</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("數字總和", u_sum)
        c2.metric("單雙比例", f"{u_odd}單 {5-u_odd}雙")
        c3.metric("連號狀況", "有連號" if u_consecutive else "無連號")
        c4.metric("歷史頭獎", f"{hist_count} 次")
        
        st.markdown("#### 📝 分析報告")
        for r in reasons:
            st.markdown(f"- {r}")
    else:
        st.info("👈 請選滿 5 個號碼")

# --- TAB 2: 智能預測 ---
with tab2:
    st.markdown("## 🔮 智能預測與補號助手")
    mode = st.radio("模式：", ["🤖 電腦推薦", "🧩 智慧補號"], horizontal=True)
    st.markdown("---")

    if "電腦" in mode:
        st.markdown("### 下期推薦組合")
        w_friend = st.slider("「好朋友」權重 (拖牌)", 0.0, 2.0, 1.2)
        w_miss = st.slider("「冷門補漲」權重 (遺漏)", 0.0, 2.0, 0.3)
        
        scores = {}
        for n in last_nums:
            idx = df[df[num_cols].isin([n]).any(axis=1)].index
            next_idx = idx + 1
            next_idx = next_idx[next_idx < len(df)]
            if len(next_idx) > 0:
                next_nums = df.iloc[next_idx][num_cols].values.flatten()
                val_counts = pd.Series(next_nums).value_counts()
                for num, count in val_counts.items():
                    scores[num] = scores.get(num, 0) + (count * w_friend)

        for num in range(1, 40):
            is_hit = current_df[num_cols].isin([num]).any(axis=1)
            if is_hit.sum() > 0:
                last_hit_pos = np.where(is_hit)[0][-1]
                skip = (len(current_df) - 1) - last_hit_pos
            else:
                skip = len(current_df)
            if 5 <= skip <= 12: 
                scores[num] = scores.get(num, 0) + (50 * w_miss)

        pred_df = pd.DataFrame(list(scores.items()), columns=['號碼', '分數'])
        top_picks = pred_df.sort_values('分數', ascending=False).head(5)['號碼'].tolist()
        
        st.markdown(f"""
        <div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; margin: 30px 0;">
            {''.join([f'<div class="lotto-ball-lg">{n}</div>' for n in top_picks])}
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown("### 🧩 智慧補號")
        fixed_nums = st.multiselect("您已決定的號碼：", options=list(range(1, 40)), max_selections=4)
        
        if len(fixed_nums) > 0:
            needed = 5 - len(fixed_nums)
            mask = df.apply(lambda row: set(row[num_cols]).issuperset(set(fixed_nums)), axis=1)
            matched_rows = df[mask]
            
            if len(matched_rows) > 0:
                all_matched_nums = matched_rows[num_cols].values.flatten()
                candidates = [n for n in all_matched_nums if n not in fixed_nums]
                if len(candidates) > 0:
                    best_matches = pd.Series(candidates).value_counts().head(needed).index.tolist()
                    final_set = sorted(fixed_nums + best_matches)
                    
                    html_str = '<div style="display: flex; gap: 10px; justify-content: center; margin-top: 30px;">'
                    for n in final_set:
                        style = 'lotto-ball-grey' if n in fixed_nums else 'lotto-ball-lg'
                        html_str += f'<div class="{style}">{n}</div>'
                    html_str += '</div>'
                    st.markdown(html_str, unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align:center; color:#888; margin-top:10px;'>灰色：自選 | 橘色：電腦推薦</div>", unsafe_allow_html=True)
                else:
                    st.warning("數據樣本不足")
            else:
                st.warning("歷史上無此組合")
        else:
            st.info("請至少選擇 1 個號碼")

# --- TAB 3: 趨勢地圖 ---
with tab3:
    st.markdown("## 視覺化趨勢")
    viz_type = st.radio("圖表：", ["棋盤熱力圖", "關係圖"], horizontal=True)
    st.markdown("---")

    if "棋盤" in viz_type:
        st.markdown("### 🎲 號碼分佈圖")
        last_n_draws = current_df.tail(analysis_range).reset_index()
        heatmap_data = []
        for idx, row in last_n_draws.iterrows():
            draw_idx = idx + 1 
            for col in num_cols:
                num = row[col]
                heatmap_data.append({'期數': draw_idx, '號碼': int(num), '開出': 1})
        
        hm_df = pd.DataFrame(heatmap_data)
        chart_heatmap = alt.Chart(hm_df).mark_rect(stroke='white', strokeWidth=0.5).encode(
            x=alt.X('期數:O', axis=alt.Axis(labels=False)),
            y=alt.Y('號碼:O'),
            color=alt.value(hermes_orange),
            tooltip=['期數', '號碼']
        ).properties(width='container', height=600)
        st.altair_chart(chart_heatmap, use_container_width=True)
        
    else:
        st.markdown("### 🔗 號碼關聯圖")
        # 取最近 500 期
        recent_corr_df = current_df.tail(500)
        co_matrix = np.zeros((40, 40))
        for _, row in recent_corr_df.iterrows():
            nums = row[num_cols].values
            for n1 in nums:
                for n2 in nums:
                    if n1 != n2:
                        co_matrix[int(n1)][int(n2)] += 1
        corr_data = []
        for i in range(1, 40):
            for j in range(1, 40):
                if i < j: 
                    corr_data.append({'A': i, 'B': j, '次數': co_matrix[i][j]})
        
        chart_corr = alt.Chart(pd.DataFrame(corr_data)).mark_rect().encode(
            x='A:O', y='B:O',
            color=alt.Color('次數', scale=alt.Scale(scheme='orangered')),
            tooltip=['A', 'B', '次數']
        ).properties(width='container', height=700)
        st.altair_chart(chart_corr, use_container_width=True)

# --- TAB 4: 時光機 ---
with tab4:
    st.markdown("## 策略回測")
    strategy = st.selectbox("策略：", ["🔥 追熱門牌", "❄️ 抓冷門牌", "⚖️ 陰陽調和"])
    
    if st.button("開始回測 (近100期)"):
        with st.spinner("模擬中..."):
            if len(df) < 130:
                st.error("資料不足，無法進行回測")
            else:
                backtest_periods = 100
                start_index = len(df) - backtest_periods
                results = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0}
                win_history = []
                
                bar = st.progress(0)
                for i in range(backtest_periods):
                    current_idx = start_index + i
                    past_data = df.iloc[current_idx-30 : current_idx]
                    all_past_nums = past_data[num_cols].values.flatten()
                    counts = pd.Series(all_past_nums).value_counts()
                    
                    my_pick = []
                    if "熱門" in strategy:
                        my_pick = counts.head(5).index.tolist()
                    elif "冷門" in strategy:
                        all_nums = set(range(1, 40))
                        not_appeared = list(all_nums - set(counts.index))
                        if len(not_appeared) >= 5: my_pick = not_appeared[:5]
                        else: my_pick = not_appeared + counts.tail(5-len(not_appeared)).index.tolist()
                    elif "陰陽" in strategy:
                        hot_nums = counts.index.tolist()
                        odds = [n for n in hot_nums if n % 2 != 0]
                        evens = [n for n in hot_nums if n % 2 == 0]
                        if len(odds) >= 3 and len(evens) >= 2: my_pick = odds[:3] + evens[:2]
                        else: my_pick = hot_nums[:5]
                    
                    if len(my_pick) < 5:
                        remain = [x for x in range(1,40) if x not in my_pick]
                        my_pick.extend(remain[:5-len(my_pick)])
                    
                    winning_nums = df.iloc[current_idx][num_cols].values
                    hits = len(set(my_pick).intersection(set(winning_nums)))
                    results[hits] += 1
                    win_history.append(hits)
                    bar.progress((i + 1) / backtest_periods)
                
                time.sleep(0.5)
                c1, c2 = st.columns(2)
                with c1:
                    res_df = pd.DataFrame.from_dict(results, orient='index', columns=['次數'])
                    res_df.index = [f"中 {i} 星" for i in res_df.index]
                    st.dataframe(res_df.T)
                    total_hits = sum([results[k] for k in [2,3,4,5]])
                    st.metric("中獎期數 (2星+)", f"{total_hits} 期")
                with c2:
                    chart_win = alt.Chart(pd.DataFrame({'期數': range(1, 101), '星數': win_history})).mark_line(color=hermes_orange).encode(x='期數', y='星數')
                    st.altair_chart(chart_win, use_container_width=True)

# --- TAB 5: 市場概況 ---
with tab5:
    st.markdown("## 市場概況")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔢 尾數強弱")
        last_range = current_df.tail(10)
        tails = []
        for c in num_cols: tails.extend(last_range[c] % 10)
        tail_counts = pd.Series(tails).value_counts().sort_index()
        tail_df = pd.DataFrame({'尾數': tail_counts.index, '次數': tail_counts.values})
        chart_tail = alt.Chart(tail_df).mark_bar().encode(
            x='尾數:O', y='次數', 
            color=alt.condition(alt.datum.次數 >= tail_df['次數'].max(), alt.value(hermes_orange), alt.value(black))
        )
        st.altair_chart(chart_tail, use_container_width=True)

    with col2:
        st.markdown("### 🥶 冷熱象限")
        hot_data = []
        for n in range(1, 40):
            is_hit = current_df[num_cols].isin([n]).any(axis=1)
            if is_hit.sum() > 0:
                last_hit_pos = np.where(is_hit)[0][-1]
                skip = (len(current_df) - 1) - last_hit_pos
            else:
                skip = len(current_df)
                
            freq = current_df.tail(30)[num_cols].isin([n]).any(axis=1).sum()
            hot_data.append({'號碼': n, '遺漏': skip, '熱度': freq})
        
        hot_df = pd.DataFrame(hot_data)
        c = alt.Chart(hot_df).mark_circle(size=120, color=black, opacity=0.7).encode(
            x='遺漏', y='熱度', tooltip=['號碼', '遺漏', '熱度']
        ).interactive()
        text = c.mark_text(align='left', dx=6, color=hermes_orange, fontSize=13, fontWeight='bold').encode(text='號碼')
        st.altair_chart(c + text, use_container_width=True)

st.markdown("---")
st.markdown("<div style='text-align: center; color: #CCC; font-size: 12px;'>COPYRIGHT © 2025 539 PRO ANALYTICS</div>", unsafe_allow_html=True)
