import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import re
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns

# BigQuery関連のインポート
try:
    from google.cloud import bigquery
    from google.oauth2 import service_account
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False
    st.warning("⚠️ BigQuery ライブラリが利用できません。デモデータを使用します。")

# 特許データ接続システム
from dual_patent_connector import DualPatentConnector

# === 修正：generate_demo_data関数を追加 ===
def generate_demo_data():
    """デモデータ生成関数（互換性のため）"""
    connector = DualPatentConnector()
    return connector.get_demo_data()

# ページ設定
st.set_page_config(
    page_title="FusionPatentSearch - ESC特許分析システム",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 0.5rem;
}
.sub-header {
    font-size: 1.2rem;
    color: #666;
    text-align: center;
    margin-bottom: 2rem;
}
.metric-card {
    background: linear-gradient(90deg, #f0f8ff 0%, #e6f3ff 100%);
    padding: 1rem;
    border-radius: 10px;
    border-left: 5px solid #1f77b4;
    margin: 0.5rem 0;
}
.sidebar-header {
    font-size: 1.5rem;
    font-weight: bold;
    color: #1f77b4;
    margin-bottom: 1rem;
}
.status-success {
    color: #28a745;
    font-weight: bold;
}
.status-warning {
    color: #ffc107;
    font-weight: bold;
}
.status-error {
    color: #dc3545;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# タイトル
st.markdown('<div class="main-header">🔍 FusionPatentSearch</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">ESC特許分析システム - 東京科学大学 齊藤滋規教授プロジェクト版</div>', unsafe_allow_html=True)

# サイドバー設定
with st.sidebar:
    st.markdown('<div class="sidebar-header">⚙️ 分析設定</div>', unsafe_allow_html=True)
    
    # データソース選択
    st.markdown("### 📊 データソース")
    data_source = st.selectbox(
        "データソースを選択:",
        ["PatentsView API", "デモデータ"],
        index=0
    )
    
    use_demo_data = (data_source == "デモデータ")
    
    # 分析タイプ選択
    st.markdown("### 🎯 分析タイプ")
    analysis_type = st.selectbox(
        "分析タイプを選択:",
        ["概要分析", "企業別詳細分析", "技術トレンド分析", "競合比較分析", "タイムライン分析"]
    )
    
    # 詳細設定
    st.markdown("### 🔧 詳細設定")
    
    # 年度範囲
    start_year = st.slider("開始年", 2015, 2025, 2015)
    end_year = st.slider("終了年", 2015, 2025, 2025)
    
    # 表示件数
    max_patents = st.slider("最大表示件数", 100, 1000, 500, step=100)

# 接続システム初期化
def get_patent_connector():
    return DualPatentConnector()

connector = get_patent_connector()

# データソース状態表示
st.markdown("### 📡 データソース状態")
col1, col2 = st.columns(2)

with col1:
    if data_source == "PatentsView API":
        st.info("🔍 PatentsView API (USPTO) で検索中...")
    else:
        st.info("📊 デモデータを使用中")

with col2:
    # 接続テスト結果表示
    connections = connector.test_connections()
    for source, status in connections.items():
        if "✅" in status:
            st.success(f"{source}: {status}")
        elif "⚠️" in status:
            st.warning(f"{source}: {status}")
        else:
            st.error(f"{source}: {status}")

# BigQuery接続設定
bq_connector = None
if BIGQUERY_AVAILABLE and not use_demo_data:
    bq_connector = connector

# データ読み込み関数
def load_patent_data(use_demo_data=False, bq_connector=None):
    """特許データを読み込む"""
    
    if use_demo_data or not BIGQUERY_AVAILABLE or bq_connector is None:
        # デモデータ生成
        connector = DualPatentConnector()
        return connector.get_demo_data()
    
    else:
        # BigQueryから実データを取得
        try:
            st.info("🔍 BigQueryから実データを取得中...")
            
            # BigQueryクエリ実行（簡略化）
            query = f"""
            SELECT 
                publication_number,
                assignee_harmonized as assignee,
                DATE(filing_date) as filing_date,
                country_code,
                title_localized as title,
                abstract_localized as abstract
            FROM `patents-public-data.patents.publications`
            WHERE 
                country_code = 'US'
                AND filing_date >= '{start_year}-01-01'
                AND filing_date <= '{end_year}-12-31'
                AND (
                    LOWER(title_localized) LIKE '%electrostatic chuck%'
                    OR LOWER(title_localized) LIKE '%esc%'
                    OR LOWER(abstract_localized) LIKE '%electrostatic chuck%'
                    OR assignee_harmonized IN (
                        'Applied Materials Inc', 'Tokyo Electron Limited', 
                        'Kyocera Corporation', 'NGK Insulators Ltd'
                    )
                )
            ORDER BY filing_date DESC
            LIMIT {max_patents}
            """
            
            df = bq_connector.bigquery_client.query(query).to_dataframe()
            return df
            
        except Exception as e:
            st.error(f"BigQueryエラー: {str(e)}")
            return generate_demo_data()

# 安全なnlargest関数
def safe_nlargest(df, n, column):
    """DataFrameのnlargest操作を安全に実行"""
    try:
        if len(df) <= n:
            return df.sort_values(column, ascending=False)
        return df.nlargest(n, column)
    except Exception:
        return df.head(n)

# 分析関数群
def overview_analysis(df):
    """概要分析"""
    st.markdown("### 📊 概要分析")
    
    # KPI指標
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総特許数", len(df))
    
    with col2:
        unique_companies = df['assignee'].nunique()
        st.metric("企業数", unique_companies)
    
    with col3:
        if 'filing_date' in df.columns:
            df['filing_date'] = pd.to_datetime(df['filing_date'])
            date_range = f"{df['filing_date'].dt.year.min()}-{df['filing_date'].dt.year.max()}"
            st.metric("対象期間", date_range)
        else:
            st.metric("対象期間", "2015-2025")
    
    with col4:
        if 'filing_date' in df.columns:
            df['filing_year'] = df['filing_date'].dt.year
            annual_avg = len(df) / max(1, df['filing_year'].nunique())
            st.metric("年平均特許数", f"{annual_avg:.1f}")
        else:
            st.metric("年平均特許数", "18.2")
    
    # グラフ表示
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 年次推移")
        if 'filing_date' in df.columns:
            df['filing_year'] = df['filing_date'].dt.year
            yearly_counts = df['filing_year'].value_counts().sort_index()
            
            fig = px.line(
                x=yearly_counts.index, 
                y=yearly_counts.values,
                title="特許出願数の年次推移",
                labels={'x': 'filing_year', 'y': 'count'}
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            # デモデータ用の年次推移
            demo_years = list(range(2015, 2025))
            demo_counts = [12, 22, 15, 23, 16, 22, 18, 14, 18, 11]
            
            fig = px.line(
                x=demo_years, 
                y=demo_counts,
                title="特許出願数の年次推移"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🏢 企業別ランキング")
        company_counts = df['assignee'].value_counts().head(10)
        
        fig = px.bar(
            x=company_counts.values,
            y=company_counts.index,
            orientation='h',
            title="企業別特許数ランキング",
            labels={'x': '特許数', 'y': '企業名'}
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

def company_analysis(df):
    """企業別詳細分析"""
    st.markdown("### 🏢 企業別詳細分析")
    
    # 企業選択
    companies = ['全て'] + sorted(df['assignee'].unique().tolist())
    selected_company = st.selectbox("企業を選択:", companies)
    
    if selected_company != '全て':
        company_df = df[df['assignee'] == selected_company]
        st.info(f"📊 {selected_company}: {len(company_df)}件の特許")
    else:
        company_df = df
    
    # 企業別統計
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 年次推移比較")
        if 'filing_date' in df.columns:
            df['filing_year'] = df['filing_date'].dt.year
            
            # 上位企業の年次推移
            top_companies = df['assignee'].value_counts().head(5).index
            
            fig = go.Figure()
            for company in top_companies:
                company_data = df[df['assignee'] == company]
                yearly_counts = company_data['filing_year'].value_counts().sort_index()
                
                fig.add_trace(go.Scatter(
                    x=yearly_counts.index,
                    y=yearly_counts.values,
                    mode='lines+markers',
                    name=company[:20] + ('...' if len(company) > 20 else '')
                ))
            
            fig.update_layout(
                title="主要企業の年次推移比較",
                xaxis_title="年",
                yaxis_title="特許数"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 最新特許リスト")
        if selected_company != '全て':
            display_df = company_df
        else:
            display_df = safe_nlargest(df, 10, 'filing_date') if 'filing_date' in df.columns else df.head(10)
        
        # 特許リスト表示
        for idx, row in display_df.head(5).iterrows():
            with st.expander(f"📄 {row.get('publication_number', 'N/A')} - {row.get('assignee', 'Unknown')[:30]}..."):
                st.write(f"**タイトル:** {row.get('title', 'No title')[:100]}...")
                st.write(f"**出願日:** {row.get('filing_date', 'Unknown')}")
                st.write(f"**要約:** {row.get('abstract', 'No abstract')[:200]}...")

def technology_trends(df):
    """技術トレンド分析"""
    st.markdown("### 🔬 技術トレンド分析")
    
    # 技術キーワード分析
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔍 技術キーワード分析")
        
        # タイトルからキーワード抽出
        all_titles = ' '.join(df['title'].fillna('').astype(str))
        
        # ESC関連キーワード
        esc_keywords = [
            'electrostatic', 'chuck', 'semiconductor', 'wafer', 'substrate',
            'curved', 'flexible', 'temperature', 'control', 'plasma',
            'processing', 'manufacturing', 'silicon', 'thin film'
        ]
        
        keyword_counts = {}
        for keyword in esc_keywords:
            count = all_titles.lower().count(keyword.lower())
            if count > 0:
                keyword_counts[keyword] = count
        
        if keyword_counts:
            fig = px.bar(
                x=list(keyword_counts.values()),
                y=list(keyword_counts.keys()),
                orientation='h',
                title="頻出キーワードランキング"
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### ☁️ ワードクラウド")
        
        try:
            # ワードクラウド生成
            if len(all_titles) > 0:
                # 基本的なテキスト処理
                clean_text = re.sub(r'[^\w\s]', ' ', all_titles.lower())
                
                # 簡易ワードクラウド（matplotlib使用）
                words = clean_text.split()
                word_freq = Counter(words)
                
                # 一般的な単語を除外
                stop_words = ['the', 'and', 'or', 'of', 'in', 'for', 'with', 'by', 'a', 'an']
                filtered_freq = {word: freq for word, freq in word_freq.items() 
                               if len(word) > 3 and word not in stop_words}
                
                if filtered_freq:
                    # 上位20単語を表示
                    top_words = dict(sorted(filtered_freq.items(), key=lambda x: x[1], reverse=True)[:20])
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    words_list = list(top_words.keys())
                    freqs_list = list(top_words.values())
                    
                    ax.barh(words_list, freqs_list)
                    ax.set_title('主要技術用語')
                    ax.set_xlabel('出現回数')
                    
                    st.pyplot(fig)
                else:
                    st.info("十分なテキストデータがありません")
            else:
                st.info("テキストデータがありません")
                
        except Exception as e:
            st.warning(f"ワードクラウド生成エラー: {str(e)}")
            st.info("代替として上位キーワードを表示します")

def competitive_analysis(df):
    """競合比較分析"""
    st.markdown("### ⚔️ 競合比較分析")
    
    # 日本企業 vs 海外企業
    japanese_companies = ['Tokyo Electron', '東京エレクトロン', 'Kyocera', '京セラ', 'NGK Insulators', '日本ガイシ', 'TOTO']
    
    df['region'] = df['assignee'].apply(
        lambda x: '日本企業' if any(jp in str(x) for jp in japanese_companies) else '海外企業'
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🌏 日本 vs 海外企業比較")
        region_counts = df['region'].value_counts()
        
        fig = px.pie(
            values=region_counts.values,
            names=region_counts.index,
            title="地域別特許分布"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 企業×年度ヒートマップ")
        
        if 'filing_date' in df.columns:
            df['filing_year'] = df['filing_date'].dt.year
            
            # 上位企業を選択
            top_companies = df['assignee'].value_counts().head(8).index
            
            # ヒートマップ用データ作成
            heatmap_data = []
            years = sorted(df['filing_year'].unique())
            
            for company in top_companies:
                company_data = df[df['assignee'] == company]
                yearly_counts = company_data['filing_year'].value_counts()
                
                row = []
                for year in years:
                    row.append(yearly_counts.get(year, 0))
                heatmap_data.append(row)
            
            # ヒートマップ作成
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=years,
                y=[comp[:20] + '...' if len(comp) > 20 else comp for comp in top_companies],
                colorscale='Blues'
            ))
            
            fig.update_layout(
                title="企業×年度 特許出願ヒートマップ",
                xaxis_title="年",
                yaxis_title="企業"
            )
            st.plotly_chart(fig, use_container_width=True)

def timeline_analysis(df):
    """タイムライン分析"""
    st.markdown("### ⏰ タイムライン分析")
    
    # 年度フィルタ
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if 'filing_date' in df.columns:
            df['filing_year'] = df['filing_date'].dt.year
            available_years = sorted(df['filing_year'].unique())
            selected_years = st.multiselect(
                "表示年度を選択:",
                available_years,
                default=available_years[-5:] if len(available_years) >= 5 else available_years
            )
            
            if selected_years:
                filtered_df = df[df['filing_year'].isin(selected_years)]
            else:
                filtered_df = df
        else:
            filtered_df = df
            st.info("年度情報が利用できません")
    
    with col2:
        st.markdown("#### 📅 最新特許タイムライン")
        
        # 最新20件を表示
        recent_patents = safe_nlargest(filtered_df, 20, 'filing_date') if 'filing_date' in filtered_df.columns else filtered_df.head(20)
        
        for idx, row in recent_patents.iterrows():
            filing_date = row.get('filing_date', 'Unknown')
            assignee = row.get('assignee', 'Unknown')
            title = row.get('title', 'No title')
            patent_num = row.get('publication_number', 'N/A')
            
            # タイムライン要素
            st.markdown(f"""
            <div style="border-left: 3px solid #1f77b4; padding-left: 15px; margin: 10px 0;">
                <strong>{filing_date}</strong> | {assignee}<br>
                <span style="font-size: 0.9em;">{patent_num}</span><br>
                <em>{title[:80]}{'...' if len(str(title)) > 80 else ''}</em>
            </div>
            """, unsafe_allow_html=True)

# メイン処理
def main():
    # データ読み込み
    try:
        with st.spinner("データを読み込み中..."):
            df = load_patent_data(use_demo_data=use_demo_data, bq_connector=bq_connector)
        
        if not use_demo_data and bq_connector:
            st.success(f"✅ BigQueryから実データを読み込みました（{len(df)}件）")
        else:
            if data_source == "PatentsView API":
                # === 修正：PatentsView APIを使用 ===
                st.info("🔍 PatentsView API からデータを取得中...")
                df = connector.search_esc_patents(
                    start_date=f"{start_year}-01-01",
                    limit=max_patents,
                    use_sample=False,
                    data_source="PatentsView API"
                )
            else:
                st.info(f"📊 デモデータを使用中（{len(df)}件）")
        
    except Exception as e:
        st.error(f"❌ データの読み込みに失敗しました: {str(e)}")
        st.info("デモデータを使用します。")
        # === 修正：エラー時のデモデータ使用 ===
        connector = DualPatentConnector()
        df = connector.get_demo_data()
    
    # 分析画面の表示
    try:
        if df is not None and not df.empty:
            # 年度フィルタリング
            if 'filing_date' in df.columns:
                df['filing_date'] = pd.to_datetime(df['filing_date'])
                df['filing_year'] = df['filing_date'].dt.year
                df = df[(df['filing_year'] >= start_year) & (df['filing_year'] <= end_year)]
            
            # 分析実行
            if analysis_type == "概要分析":
                overview_analysis(df)
            elif analysis_type == "企業別詳細分析":
                company_analysis(df)
            elif analysis_type == "技術トレンド分析":
                technology_trends(df)
            elif analysis_type == "競合比較分析":
                competitive_analysis(df)
            elif analysis_type == "タイムライン分析":
                timeline_analysis(df)
        else:
            st.error("❌ データが空です")
            
    except Exception as e:
        st.error(f"❌ 分析処理でエラーが発生しました: {str(e)}")
        st.info("システム管理者にお問い合わせください。")

# フッター
st.markdown("""
---
<div style="text-align: center; color: #666; font-size: 0.8em;">
📧 <strong>FusionPatentSearch</strong> - ESC特許分析システム<br>
🏛️ 東京科学大学 齊藤滋規教授研究室 × FUSIONDRIVER INC KSPプロジェクト<br>
🔗 <a href="https://github.com/koji276/FusionPatentSearch" target="_blank">GitHub Repository</a>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
