# --- 爬蟲更新函數 (欄位強對齊修正版) ---
def update_data_from_web():
    url = "https://www.pilio.idv.tw/lto539/list539APP.asp"
    import re
    
    try:
        # 1. 讀取現有 CSV (先讀取，確保格式一致)
        try:
            # 讀取時將所有欄位轉為字串，避免型別錯誤
            current_csv = pd.read_csv(CSV_FILE, dtype=str)
            # 強制清洗欄位名稱：去除前後空白
            current_csv.columns = [c.strip() for c in current_csv.columns]
            
            # 定義標準欄位順序 (確保寫入時不會亂掉)
            std_columns = ['總期數', '年份', '日期', '期數', '球號 1', '球號 2', '球號 3', '球號 4', '球號 5', '出牌次數', '數字', '次數高至低']
            
            # 確保現有 CSV 擁有標準欄位，沒有的補空值
            for col in std_columns:
                if col not in current_csv.columns:
                    current_csv[col] = ""
            
            # 依照標準順序重新排列
            current_csv = current_csv[std_columns]
            
            # 取得最後一筆日期的基準
            if not current_csv.empty:
                last_row = current_csv.iloc[-1]
                # 組合日期字串
                d_str = str(last_row['日期']).replace('月', '/').replace('日', '')
                last_date_str = f"{last_row['年份']}/{d_str}"
                last_record_date = pd.to_datetime(last_date_str)
                
                # 取得最後期數 ID
                try:
                    last_total_id = int(last_row['總期數'])
                    last_draw_id = int(last_row['期數'])
                except:
                    last_total_id = len(current_csv)
                    last_draw_id = 0
            else:
                last_record_date = pd.to_datetime("2000/01/01")
                last_total_id = 0
                last_draw_id = 0

        except Exception as e:
            return f"❌ 讀取 CSV 失敗，請檢查檔案格式: {e}"

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
            return "❌ 抓不到網頁表格"

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
            
            # 建立乾淨的字典
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
        
        # 關鍵：確保新資料的欄位順序跟舊的一模一樣
        df_new = df_new[std_columns]
        
        # 合併
        final_df = pd.concat([current_csv, df_new], ignore_index=True)
        
        # 存檔 (不寫入 index，避免產生 Unnamed: 0 欄位)
        final_df.to_csv(CSV_FILE, index=False, encoding='utf-8')
        st.cache_data.clear()
        
        return f"🎉 成功更新 {len(rows_to_add)} 筆資料！"

    except Exception as e:
        return f"❌ 更新錯誤: {str(e)}"
