import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import random
import requests
import time

# ページ設定
st.set_page_config(
    page_title="FusionPatentSearch - ESC特許分析システム",
    page_icon="🔍",
    layout="wide"
)

# メインヘッダー
st.title("🔍 FusionPatentSearch")
st.markdown("**ESC特許分析システム** - 東京科学大学 齊藤滋規教授プロジェクト版")

# デモデータ生成関数
def generate_demo_data():
    """デモデータ生成"""
    companies = [
        'Applied Materials Inc', 'Tokyo Electron Limited', 'Kyocera Corporation',
        'NGK Insulators Ltd', 'TOTO Ltd', 'Lam Research Corporation',
        'Entegris Inc', 'Shinko Electric Industries'
    ]
    
    demo_data = []
    base_date = datetime(2015, 1, 1)
    
    for i in range(200):
        company = random.choice(companies)
        days_offset = random.randint(0, (datetime.now() - base_date).days)
        filing_date = base_date + timedelta(days=days_offset)
        
        demo_data.append({
            'publication_number': f"US{random.randint(8000000, 11000000)}",
            'assignee': company,
            'filing_date': filing_date,  # datetimeオブジェクトとして保存
            'country_code': 'US',
            'title': f'Advanced Electrostatic Chuck Technology - Patent {i+1}',
            'abstract': f'Enhanced electrostatic chuck system for semiconductor processing. Patent {i+1}.',
            'filing_year': filing_date.year
        })
    
    return pd.DataFrame(demo_data)

# PatentsView API検索関数
def search_patents_api():
    """PatentsView APIから特許データを取得"""
    try:
        st.info("🔍 PatentsView API (USPTO) で検索中...")
        
        companies = ["Applied Materials", "Tokyo Electron", "Lam Research"]
        all_patents = []
        
        for company in companies:
            try:
                query = {
                    "q": {"assignee_organization": company},
                    "f": ["patent_number", "patent_title", "patent_date", "assignee_organization"],
                    "s": [{"patent_date": "desc"}],
                    "o": {"per_page": 15}
                }
                
                response = requests.post("https://api.patentsview.org/patents/query", json=query, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    patents = data.get('patents', [])
                    
                    for patent in patents:
                        assignees = patent.get('assignees', [])
                        assignee_name = assignees[0].get('assignee_organization', company) if assignees else company
                        
                        # 日付をdatetimeに変換
                        patent_date = patent.get('patent_date', '')
                        try:
                            filing_date = pd.to_datetime(patent_date)
                        except:
                            filing_date = datetime.now()
                        
                        all_patents.append({
                            'publication_number': patent.get('patent_number', ''),
                            'assignee': assignee_name,
                            'filing_date': filing_date,
                            'country_code': 'US',
                            'title': patent.get('patent_title', ''),
                            'abstract': 'Patent data from USPTO PatentsView API.',
                            'filing_year': filing_date.year
                        })
                
                time.sleep(0.5)  # API制限対策
                
            except Exception as e:
                st.warning(f"⚠️ {company}: {str(e)}")
                continue
        
        if all_patents:
            df = pd.DataFrame(all_patents)
            st.success(f"✅ PatentsView API: {len(df)}件の実データを取得!")
            return df
        else:
            st.warning("⚠️ API からデータを取得できませんでした")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ API エラー: {str(e)}")
        return pd.DataFrame()

# サイドバー
with st.sidebar:
    st.header("⚙️ 分析設定")
    
    data_source = st.selectbox(
        "📊 データソース:",
        ["PatentsView API", "デモデータ"],
        index=1
    )
    
    analysis_type = st.selectbox(
        "🎯 分析タイプ:",
        ["概要分析", "企業別分析"],
        index=0
    )

# データ取得
if data_source == "PatentsView API":
    df = search_patents_api()
    if df.empty:
        st.warning("API データが取得できませんでした。デモデータを使用します。")
        df = generate_demo_data()
else:
    df = generate_demo_data()
    st.info("📊 デモデータを使用中")

# データが存在する場合のみ分析実行
if not df.empty:
    # データ型を確実にdatetimeに変換
    df['filing_date'] = pd.to_datetime(df['filing_date'])
    df['filing_year'] = df['filing_date'].dt.year
    
    # 企業名正規化
    def normalize_company_name(name):
        if pd.isna(name):
            return "Unknown"
        name = str(name).upper()
        
        company_mapping = {
            'APPLIED MATERIALS': 'Applied Materials',
            'TOKYO ELECTRON': 'Tokyo Electron',
            'LAM RESEARCH': 'Lam Research',
            'KYOCERA': 'Kyocera',
            'NGK INSULATORS': 'NGK Insulators',
            'TOTO': 'TOTO',
            'ENTEGRIS': 'Entegris',
            'SHINKO ELECTRIC': 'Shinko Electric'
        }
        
        for key, value in company_mapping.items():
            if key in name:
                return value
        return name.title()
    
    df['company_normalized'] = df['assignee'].apply(normalize_company_name)
    
    # 分析表示
    if analysis_type == "概要分析":
        st.header("📊 概要分析")
        
        # KPI表示
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("総特許数", len(df))
        
        with col2:
            st.metric("企業数", df['company_normalized'].nunique())
        
        with col3:
            date_range = f"{df['filing_date'].min().year}-{df['filing_date'].max().year}"
            st.metric("対象期間", date_range)
        
        with col4:
            year_span = df['filing_date'].max().year - df['filing_date'].min().year + 1
            avg_per_year = len(df) / year_span if year_span > 0 else len(df)
            st.metric("年平均特許数", f"{avg_per_year:.1f}")
        
        # グラフ表示
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 年次推移")
            yearly_counts = df.groupby('filing_year').size().reset_index(name='count')
            
            fig = px.line(yearly_counts, x='filing_year', y='count',
                         title='特許出願数の年次推移', markers=True)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🏢 企業別ランキング")
            company_counts = df['company_normalized'].value_counts().head(10)
            
            fig = px.bar(x=company_counts.values, y=company_counts.index,
                        orientation='h', title='企業別特許数ランキング')
            st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "企業別分析":
        st.header("🏢 企業別詳細分析")
        
        # 企業選択
        available_companies = sorted(df['company_normalized'].unique())
        selected_company = st.selectbox(
            "🎯 分析対象企業:",
            options=available_companies
        )
        
        company_data = df[df['company_normalized'] == selected_company]
        
        if not company_data.empty:
            # 企業サマリー
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("総特許数", len(company_data))
            
            with col2:
                latest_patent = company_data['filing_date'].max()
                st.metric("最新特許日", latest_patent.strftime('%Y-%m-%d'))
            
            with col3:
                market_share = (len(company_data) / len(df)) * 100
                st.metric("市場シェア", f"{market_share:.1f}%")
            
            # 最新特許リスト（安全な方法でソート）
            st.subheader("📝 最新特許リスト")
            latest_patents = company_data.sort_values('filing_date', ascending=False).head(5)
            
            for idx, patent in latest_patents.iterrows():
                with st.expander(f"📄 {patent['publication_number']} ({patent['filing_date'].strftime('%Y-%m-%d')})"):
                    st.write(f"**タイトル:** {patent['title']}")
                    st.write(f"**国:** {patent['country_code']}")
                    st.write(f"**年:** {patent['filing_year']}")
    
    # 生データ表示
    with st.expander("📋 生データを表示"):
        st.dataframe(df.head(50))
        
        # CSV ダウンロード
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 CSVダウンロード",
            data=csv,
            file_name=f"patents_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

else:
    st.error("❌ データの読み込みに失敗しました。")

# フッター
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
<strong>FusionPatentSearch v2.0</strong> - ESC特許分析システム<br>
開発: FUSIONDRIVER INC | 学術連携: 東京科学大学 齊藤滋規教授研究室<br>
最終更新: 2025年7月22日 | KSPプロジェクト
</div>
""", unsafe_allow_html=True)
