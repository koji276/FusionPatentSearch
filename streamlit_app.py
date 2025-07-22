import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from bigquery_connector import BigQueryConnector

# ページ設定
st.set_page_config(
    page_title="FusionPatentSearch - ESC特許分析システム",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# メインヘッダー
st.markdown('<div style="font-size: 2.5rem; font-weight: bold; color: #1f77b4; text-align: center; margin-bottom: 2rem;">🔍 FusionPatentSearch</div>', unsafe_allow_html=True)
st.markdown("**ESC特許分析システム** - 東京科学大学 齊藤滋規教授プロジェクト版")

# BigQuery接続初期化
@st.cache_resource
def init_bigquery():
    return BigQueryConnector()

connector = init_bigquery()

# サイドバー設定
with st.sidebar:
    st.markdown("### ⚙️ 分析設定")
    
    # 接続ステータス表示
    if connector.is_connected:
        st.success("✅ BigQuery接続済み")
        if st.button("🔍 接続テスト"):
            is_connected, message = connector.test_connection()
            if is_connected:
                st.success(message)
            else:
                st.error(message)
    else:
        st.error("❌ BigQuery未接続")
        st.info("💡 デモデータで動作します")
    
    # データソース選択
    if connector.is_connected:
        data_source = st.radio("📊 データソース:", ["実データ (BigQuery)", "デモデータ"], index=0)
        use_real_data = (data_source == "実データ (BigQuery)")
    else:
        use_real_data = False
    
    # 分析タイプ選択
    analysis_type = st.selectbox(
        "🎯 分析タイプを選択:",
        ["概要分析", "企業別詳細分析", "技術トレンド分析", "競合比較分析"]
    )
    
    start_date = st.date_input("開始日", datetime(2015, 1, 1))
    data_limit = st.slider("取得データ件数", 100, 1000, 500)

# データ取得
@st.cache_data(ttl=3600)
def load_patent_data(use_real, start_date_str, limit):
    return connector.search_esc_patents(start_date=start_date_str, limit=limit, use_sample=not use_real)

with st.spinner("📊 特許データを読み込み中..."):
    df = load_patent_data(use_real_data, start_date.strftime('%Y-%m-%d'), data_limit)

if df is not None and not df.empty:
    # データ前処理
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
            'KYOCERA': 'Kyocera',
            'NGK INSULATORS': 'NGK Insulators',
            'TOTO': 'TOTO',
            'LAM RESEARCH': 'Lam Research',
            'ENTEGRIS': 'Entegris',
            'SHINKO ELECTRIC': 'Shinko Electric'
        }
        for key, value in company_mapping.items():
            if key in name:
                return value
        return name.title()
    
    df['company_normalized'] = df['assignee'].apply(normalize_company_name)
    
    # 概要分析
    if analysis_type == "概要分析":
        st.header("📊 概要分析")
        
        if use_real_data and connector.is_connected:
            st.success("📈 **実データ分析結果** - Google Patents BigQuery Dataset")
        else:
            st.info("📊 **デモデータ分析結果**")
        
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
        
        # 年次推移グラフ
        st.subheader("📈 年次推移")
        yearly_counts = df.groupby('filing_year').size().reset_index(name='count')
        fig = px.line(yearly_counts, x='filing_year', y='count', title='特許出願数の年次推移', markers=True)
        st.plotly_chart(fig, use_container_width=True)
        
        # 企業別ランキング
        st.subheader("🏢 企業別ランキング")
        company_counts = df['company_normalized'].value_counts().head(10)
        fig = px.bar(x=company_counts.values, y=company_counts.index, orientation='h', title='企業別特許数ランキング')
        st.plotly_chart(fig, use_container_width=True)
    
    # 生データ表示
    with st.expander("📋 生データを表示"):
        st.dataframe(df.head(50))
        csv = df.to_csv(index=False)
        st.download_button("📥 CSVダウンロード", csv, f"patents_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

else:
    st.error("❌ データの読み込みに失敗しました。")

# フッター
st.markdown("---")
st.markdown("**FusionPatentSearch** - 開発: FUSIONDRIVER INC | 東京科学大学 齊藤滋規教授研究室")