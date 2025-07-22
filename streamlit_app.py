 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESC特許分析 Streamlit Webアプリ
GitHub + Streamlit Cloud で動作

使用方法:
streamlit run streamlit_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google.cloud import bigquery
from collections import Counter, defaultdict
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Streamlit設定
st.set_page_config(
    page_title="FusionPatentSearch - 東京科学大学版",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .company-highlight {
        background-color: #e1f5fe;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.25rem 0;
        border-left: 4px solid #2196f3;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitESCAnalyzer:
    def __init__(self):
        """初期化"""
        self.target_companies = {
            'Japanese': {
                'SHINKO ELECTRIC': '新光電気工業',
                'TOTO': 'TOTO',
                'SUMITOMO OSAKA CEMENT': '住友大阪セメント',
                'KYOCERA': '京セラ',
                'NGK INSULATORS': '日本ガイシ',
                'NTK CERATEC': 'NTKセラテック',
                'TSUKUBA SEIKO': '筑波精工',
                'CREATIVE TECHNOLOGY': 'クリエイティブテクノロジー',
                'TOKYO ELECTRON': '東京エレクトロン'
            },
            'International': {
                'APPLIED MATERIALS': 'Applied Materials (米国)',
                'LAM RESEARCH': 'Lam Research (米国)',
                'ENTEGRIS': 'Entegris (米国)',
                'FM INDUSTRIES': 'FM Industries (米国→日本ガイシ)',
                'MICO': 'MiCo (韓国)',
                'SEMCO ENGINEERING': 'SEMCO Engineering (フランス)',
                'CALITECH': 'Calitech (台湾)',
                'BEIJING U-PRECISION': 'Beijing U-Precision (中国)'
            }
        }
    
    @st.cache_data
    def load_demo_data(_self):
        """デモデータの生成（BigQuery接続なしでも動作）"""
        np.random.seed(42)
        
        # ダミーデータ生成
        companies = list(_self.target_companies['Japanese'].keys()) + list(_self.target_companies['International'].keys())
        
        data = []
        for i in range(500):  # 500件のダミー特許
            company = np.random.choice(companies, p=[0.15, 0.08, 0.05, 0.12, 0.18, 0.06, 0.03, 0.04, 0.08, 0.09, 0.05, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01])
            year = np.random.choice(range(2015, 2025), p=[0.05, 0.08, 0.10, 0.12, 0.15, 0.16, 0.14, 0.12, 0.06, 0.02])
            
            titles = [
                "Electrostatic chuck with improved temperature control",
                "Curved ESC for flexible substrate processing", 
                "Multi-zone heating system for semiconductor processing",
                "Ceramic electrostatic chuck with enhanced durability",
                "Plasma confinement system with curved geometry",
                "Temperature monitoring system for wafer processing",
                "Flexible substrate handling apparatus",
                "Advanced ceramic material for ESC applications"
            ]
            
            data.append({
                'publication_number': f'JP{year}0{i:06d}',
                'normalized_assignee': company,
                'filing_date': f'{year}-{np.random.randint(1,13):02d}-{np.random.randint(1,29):02d}',
                'title': np.random.choice(titles),
                'country_code': np.random.choice(['JP', 'US', 'EP', 'CN'], p=[0.4, 0.3, 0.2, 0.1]),
                'filing_year': year
            })
        
        return pd.DataFrame(data)
    
    @st.cache_data  
    def search_patents_bigquery(_self, use_demo=True):
        """BigQueryから特許データを検索"""
        if use_demo:
            return _self.load_demo_data()
        
        # 実際のBigQuery接続（認証設定済みの場合）
        try:
            client = bigquery.Client()
            query = """
            SELECT DISTINCT
                p.publication_number,
                p.country_code,
                p.filing_date,
                COALESCE(title_en.text, title_ja.text) as title,
                p.assignee_harmonized as assignee,
                EXTRACT(YEAR FROM p.filing_date) as filing_year
            FROM `patents-public-data.patents.publications` p
            LEFT JOIN UNNEST(title_localized) as title_en ON title_en.language = 'en'
            LEFT JOIN UNNEST(title_localized) as title_ja ON title_ja.language = 'ja'
            WHERE (
                REGEXP_CONTAINS(LOWER(COALESCE(title_en.text, '')), r'electrostatic.*chuck|esc')
                OR REGEXP_CONTAINS(COALESCE(title_ja.text, ''), r'静電チャック|ESC')
                OR REGEXP_CONTAINS(UPPER(COALESCE(p.assignee_harmonized, '')), 
                    r'SHINKO ELECTRIC|TOTO|KYOCERA|NGK|TOKYO ELECTRON|APPLIED MATERIALS|LAM RESEARCH')
            )
            AND p.filing_date >= '2015-01-01'
            ORDER BY p.filing_date DESC
            LIMIT 1000
            """
            
            df = client.query(query).to_dataframe()
            # 企業名正規化
            df['normalized_assignee'] = df['assignee'].fillna('Unknown')
            return df
            
        except Exception as e:
            st.error(f"BigQuery接続エラー: {e}")
            return _self.load_demo_data()

def create_main_dashboard():
    """メインダッシュボードの作成"""
    # ヘッダー部分
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="color: #1f77b4; font-size: 2.5rem; margin-bottom: 0.5rem;">
                🔍 FusionPatentSearch
            </h1>
            <p style="color: #666; font-size: 1.2rem; margin-bottom: 0.5rem;">
                東京科学大学 齊藤滋規教授プロジェクト
            </p>
            <p style="color: #888; font-size: 0.9rem; margin-bottom: 1.5rem;">
                ESC特許動向分析システム - Professional Edition
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    analyzer = StreamlitESCAnalyzer()
    
    # サイドバー設定
    st.sidebar.header("⚙️ 分析設定")
    
    use_demo = st.sidebar.checkbox("デモデータを使用", value=True, help="BigQuery接続なしでデモデータで動作")
    
    analysis_type = st.sidebar.selectbox(
        "分析タイプ",
        ["概要分析", "企業別詳細", "技術トレンド", "競合比較", "タイムライン分析"]
    )
    
    # データ読み込み
    with st.spinner('データを読み込み中...'):
        df = analyzer.search_patents_bigquery(use_demo=use_demo)
    
    if df.empty:
        st.error("データが見つかりませんでした。")
        return
    
    # メイン分析表示
    if analysis_type == "概要分析":
        show_overview_analysis(df, analyzer)
    elif analysis_type == "企業別詳細":
        show_company_analysis(df, analyzer)
    elif analysis_type == "技術トレンド":
        show_technology_trends(df, analyzer)
    elif analysis_type == "競合比較":
        show_competitive_analysis(df, analyzer)
    elif analysis_type == "タイムライン分析":
        show_timeline_analysis(df, analyzer)

def show_overview_analysis(df, analyzer):
    """概要分析の表示"""
    st.header("📊 概要分析")
    
    # KPIメトリクス
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総特許数", f"{len(df):,}")
    with col2:
        unique_companies = df['normalized_assignee'].nunique()
        st.metric("出願企業数", f"{unique_companies}")
    with col3:
        date_range = f"{df['filing_date'].min()[:4]}-{df['filing_date'].max()[:4]}"
        st.metric("対象期間", date_range)
    with col4:
        target_patents = df[df['normalized_assignee'].isin(
            list(analyzer.target_companies['Japanese'].keys()) + 
            list(analyzer.target_companies['International'].keys())
        )]
        st.metric("ターゲット企業特許", f"{len(target_patents)}")
    
    # グラフエリア
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 年次出願推移")
        yearly_data = df.groupby('filing_year').size().reset_index()
        yearly_data.columns = ['年', '特許数']
        
        fig = px.line(yearly_data, x='年', y='特許数', 
                     title='ESC関連特許の年次推移',
                     markers=True, line_shape='spline')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏢 企業別出願件数 Top 10")
        company_data = df['normalized_assignee'].value_counts().head(10).reset_index()
        company_data.columns = ['企業', '特許数']
        
        fig = px.bar(company_data, x='特許数', y='企業', 
                    title='企業別特許出願件数',
                    orientation='h', color='特許数',
                    color_continuous_scale='viridis')
        fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    # 国別分布
    st.subheader("🌍 国別特許分布")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        country_data = df['country_code'].value_counts().head(8)
        fig = px.pie(values=country_data.values, names=country_data.index,
                    title='国別特許分布')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # ターゲット企業の日本 vs 海外
        target_patents = df[df['normalized_assignee'].isin(
            list(analyzer.target_companies['Japanese'].keys()) + 
            list(analyzer.target_companies['International'].keys())
        )]
        
        if not target_patents.empty:
            japanese_companies = set(analyzer.target_companies['Japanese'].keys())
            target_patents_copy = target_patents.copy()
            target_patents_copy['region'] = target_patents_copy['normalized_assignee'].apply(
                lambda x: '日本企業' if x in japanese_companies else '海外企業'
            )
            region_data = target_patents_copy['region'].value_counts()
            
            fig = px.pie(values=region_data.values, names=region_data.index,
                        title='ターゲット企業: 日本 vs 海外',
                        color_discrete_map={'日本企業': '#ff9999', '海外企業': '#66b3ff'})
            st.plotly_chart(fig, use_container_width=True)

def show_company_analysis(df, analyzer):
    """企業別詳細分析"""
    st.header("🏢 企業別詳細分析")
    
    # 企業選択
    all_companies = list(analyzer.target_companies['Japanese'].keys()) + list(analyzer.target_companies['International'].keys())
    selected_companies = st.multiselect(
        "分析対象企業を選択",
        options=all_companies,
        default=all_companies[:5]
    )
    
    if not selected_companies:
        st.warning("企業を選択してください。")
        return
    
    company_data = df[df['normalized_assignee'].isin(selected_companies)]
    
    if company_data.empty:
        st.warning("選択した企業のデータが見つかりません。")
        return
    
    # 企業別統計
    st.subheader("📊 企業別統計")
    company_stats = company_data['normalized_assignee'].value_counts().reset_index()
    company_stats.columns = ['企業', '特許数']
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(company_stats, x='企業', y='特許数',
                    title='選択企業の特許出願数',
                    color='特許数', color_continuous_scale='Blues')
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 年次推移比較
        yearly_company = company_data.pivot_table(
            index='filing_year', 
            columns='normalized_assignee', 
            values='publication_number',
            aggfunc='count',
            fill_value=0
        )
        
        fig = go.Figure()
        for company in selected_companies:
            if company in yearly_company.columns:
                fig.add_trace(go.Scatter(
                    x=yearly_company.index,
                    y=yearly_company[company],
                    mode='lines+markers',
                    name=company[:15],
                    line_shape='spline'
                ))
        
        fig.update_layout(
            title='企業別年次推移',
            xaxis_title='年',
            yaxis_title='特許数',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 企業詳細情報
    st.subheader("🔍 企業詳細情報")
    
    for company in selected_companies:
        company_patents = company_data[company_data['normalized_assignee'] == company]
        if not company_patents.empty:
            # 企業情報表示
            jp_name = analyzer.target_companies['Japanese'].get(company) or \
                     analyzer.target_companies['International'].get(company, company)
            
            st.markdown(f'<div class="company-highlight">', unsafe_allow_html=True)
            st.markdown(f"**{company}** ({jp_name})")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("特許数", len(company_patents))
            with col2:
                countries = company_patents['country_code'].nunique()
                st.metric("出願国数", countries)
            with col3:
                years = company_patents['filing_year'].nunique()
                st.metric("出願年数", years)
            with col4:
                latest_year = company_patents['filing_year'].max()
                st.metric("最新出願年", latest_year)
            
            # 最新特許リスト
            with st.expander(f"{company} 最新特許 (Top 5)"):
                recent_patents = company_patents.nlargest(5, 'filing_date')[['filing_date', 'title', 'country_code']]
                st.dataframe(recent_patents, use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

def show_technology_trends(df, analyzer):
    """技術トレンド分析"""
    st.header("📈 技術トレンド分析")
    
    # キーワード分析
    st.subheader("🔍 技術キーワード分析")
    
    # 技術カテゴリ定義
    tech_categories = {
        'Temperature Control': ['temperature', 'thermal', 'heating', '温度', '加熱'],
        'Curved/Flexible': ['curved', 'flexible', 'bendable', '曲面', '湾曲'],
        'Material': ['ceramic', 'dielectric', 'material', 'セラミック', '誘電体'],
        'Process': ['plasma', 'etching', 'deposition', 'プラズマ', 'エッチング'],
        'Control': ['control', 'monitoring', 'sensor', '制御', 'センサ']
    }
    
    # 年別技術トレンド分析
    tech_trend_data = []
    
    for year in df['filing_year'].unique():
        year_patents = df[df['filing_year'] == year]
        year_text = ' '.join(year_patents['title'].fillna('').astype(str))
        
        for category, keywords in tech_categories.items():
            count = 0
            for keyword in keywords:
                count += len(re.findall(keyword, year_text, re.IGNORECASE))
            
            tech_trend_data.append({
                'year': year,
                'category': category,
                'count': count
            })
    
    trend_df = pd.DataFrame(tech_trend_data)
    
    # 技術トレンド可視化
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.line(trend_df, x='year', y='count', color='category',
                     title='技術カテゴリ別トレンド',
                     markers=True)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 最新年の技術分布
        latest_year = df['filing_year'].max()
        latest_trend = trend_df[trend_df['year'] == latest_year]
        
        fig = px.bar(latest_trend, x='category', y='count',
                    title=f'{latest_year}年 技術分野分布',
                    color='count', color_continuous_scale='viridis')
        fig.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    # ワードクラウド風表示
    st.subheader("☁️ 頻出技術キーワード")
    all_titles = ' '.join(df['title'].fillna('').astype(str))
    
    # シンプルなキーワード抽出
    tech_words = ['electrostatic', 'chuck', 'temperature', 'ceramic', 'plasma', 
                  'control', 'heating', 'flexible', 'curved', 'substrate']
    
    word_counts = []
    for word in tech_words:
        count = len(re.findall(word, all_titles, re.IGNORECASE))
        if count > 0:
            word_counts.append({'word': word, 'count': count})
    
    if word_counts:
        word_df = pd.DataFrame(word_counts).sort_values('count', ascending=True)
        fig = px.bar(word_df, x='count', y='word', orientation='h',
                    title='技術キーワード出現頻度',
                    color='count', color_continuous_scale='plasma')
        st.plotly_chart(fig, use_container_width=True)

def show_competitive_analysis(df, analyzer):
    """競合比較分析"""
    st.header("⚔️ 競合比較分析")
    
    # ターゲット企業の抽出
    target_patents = df[df['normalized_assignee'].isin(
        list(analyzer.target_companies['Japanese'].keys()) + 
        list(analyzer.target_companies['International'].keys())
    )]
    
    if target_patents.empty:
        st.warning("ターゲット企業のデータがありません。")
        return
    
    # 日本 vs 海外企業比較
    st.subheader("🌏 日本企業 vs 海外企業")
    
    japanese_companies = set(analyzer.target_companies['Japanese'].keys())
    target_patents_copy = target_patents.copy()
    target_patents_copy['region'] = target_patents_copy['normalized_assignee'].apply(
        lambda x: '日本企業' if x in japanese_companies else '海外企業'
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 地域別出願数
        region_stats = target_patents_copy['region'].value_counts()
        fig = px.pie(values=region_stats.values, names=region_stats.index,
                    title='地域別特許分布',
                    color_discrete_map={'日本企業': '#ff9999', '海外企業': '#66b3ff'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 地域別年次推移
        region_yearly = target_patents_copy.pivot_table(
            index='filing_year',
            columns='region',
            values='publication_number',
            aggfunc='count',
            fill_value=0
        )
        
        fig = go.Figure()
        for region in region_yearly.columns:
            fig.add_trace(go.Scatter(
                x=region_yearly.index,
                y=region_yearly[region],
                mode='lines+markers',
                name=region,
                line_shape='spline'
            ))
        
        fig.update_layout(
            title='地域別年次推移',
            xaxis_title='年',
            yaxis_title='特許数',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 企業別詳細比較
    st.subheader("🏢 企業別詳細比較")
    
    # ヒートマップ用データ作成
    company_year_data = target_patents.pivot_table(
        index='normalized_assignee',
        columns='filing_year', 
        values='publication_number',
        aggfunc='count',
        fill_value=0
    )
    
    if not company_year_data.empty:
        # Plotly heatmap
        fig = go.Figure(data=go.Heatmap(
            z=company_year_data.values,
            x=company_year_data.columns,
            y=company_year_data.index,
            colorscale='viridis',
            showscale=True
        ))
        
        fig.update_layout(
            title='企業×年度 出願ヒートマップ',
            xaxis_title='年度',
            yaxis_title='企業',
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 競合ランキング
    st.subheader("🏆 競合ランキング")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**日本企業ランキング**")
        jp_companies = target_patents[target_patents['normalized_assignee'].isin(japanese_companies)]
        jp_ranking = jp_companies['normalized_assignee'].value_counts()
        
        for i, (company, count) in enumerate(jp_ranking.items(), 1):
            jp_name = analyzer.target_companies['Japanese'].get(company, company)
            st.markdown(f"{i}. **{company}** ({jp_name}): {count}件")
    
    with col2:
        st.markdown("**海外企業ランキング**")
        intl_companies_set = set(analyzer.target_companies['International'].keys())
        intl_companies = target_patents[target_patents['normalized_assignee'].isin(intl_companies_set)]
        intl_ranking = intl_companies['normalized_assignee'].value_counts()
        
        for i, (company, count) in enumerate(intl_ranking.items(), 1):
            intl_name = analyzer.target_companies['International'].get(company, company)
            st.markdown(f"{i}. **{company}** ({intl_name}): {count}件")

def show_timeline_analysis(df, analyzer):
    """タイムライン分析"""
    st.header("⏰ タイムライン分析")
    
    # 年度フィルタ
    min_year, max_year = int(df['filing_year'].min()), int(df['filing_year'].max())
    selected_years = st.slider(
        "分析対象年度",
        min_value=min_year,
        max_value=max_year,
        value=(max_year-5, max_year),
        step=1
    )
    
    filtered_df = df[
        (df['filing_year'] >= selected_years[0]) & 
        (df['filing_year'] <= selected_years[1])
    ]
    
    # タイムライン可視化
    st.subheader("📅 特許出願タイムライン")
    
    timeline_data = filtered_df.groupby(['filing_year', 'normalized_assignee']).size().reset_index()
    timeline_data.columns = ['年度', '企業', '特許数']
    
    # 主要企業のみ表示
    top_companies = df['normalized_assignee'].value_counts().head(10).index
    timeline_filtered = timeline_data[timeline_data['企業'].isin(top_companies)]
    
    fig = px.line(timeline_filtered, x='年度', y='特許数', color='企業',
                 title=f'{selected_years[0]}-{selected_years[1]}年 企業別特許出願推移',
                 markers=True, line_shape='spline')
    
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # 重要な出来事のハイライト
    st.subheader("🌟 重要な出来事")
    
    # 各年の上位出願企業
    for year in range(selected_years[1], selected_years[0]-1, -1):
        year_data = filtered_df[filtered_df['filing_year'] == year]
        if not year_data.empty:
            top_company = year_data['normalized_assignee'].value_counts().head(1)
            if not top_company.empty:
                company, count = top_company.index[0], top_company.iloc[0]
                st.markdown(f"**{year}年**: {company} が {count}件で最多出願")
    
    # 最新特許リスト
    st.subheader("📋 最新特許リスト")
    
    latest_patents = filtered_df.nlargest(20, 'filing_date')[
        ['filing_date', 'normalized_assignee', 'title', 'country_code']
    ].copy()
    
    latest_patents.columns = ['出願日', '出願人', 'タイトル', '国コード']
    st.dataframe(latest_patents, use_container_width=True)

# メイン実行
if __name__ == "__main__":
    create_main_dashboard()
