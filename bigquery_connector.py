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

# カスタムCSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.kpi-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    text-align: center;
    margin: 0.5rem 0;
}
.sidebar-header {
    font-size: 1.2rem;
    font-weight: bold;
    color: #333;
    margin-bottom: 1rem;
}
.status-success {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 5px;
    padding: 0.5rem;
    margin: 0.5rem 0;
}
.status-error {
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    border-radius: 5px;
    padding: 0.5rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# メインヘッダー
st.markdown('<div class="main-header">🔍 FusionPatentSearch</div>', unsafe_allow_html=True)
st.markdown("**ESC特許分析システム** - 東京科学大学 齊藤滋規教授プロジェクト版")

# BigQuery接続初期化
@st.cache_resource
def init_bigquery():
    return BigQueryConnector()

connector = init_bigquery()

# サイドバー設定
with st.sidebar:
    st.markdown('<div class="sidebar-header">⚙️ 分析設定</div>', unsafe_allow_html=True)
    
    # 接続ステータス表示
    if connector.is_connected:
        st.markdown('<div class="status-success">✅ BigQuery接続済み</div>', unsafe_allow_html=True)
        
        # 接続詳細テスト
        if st.button("🔍 詳細接続テスト"):
            with st.spinner("接続テスト中..."):
                is_connected, message = connector.test_connection()
                if is_connected:
                    st.success(message)
                else:
                    st.error(message)
    else:
        st.markdown('<div class="status-error">❌ BigQuery未接続</div>', unsafe_allow_html=True)
        st.info("💡 デモデータで動作します")
        
        # Secrets設定のヘルプ
        with st.expander("🔧 接続設定ヘルプ"):
            st.markdown("""
            **BigQuery接続には以下が必要です:**
            1. Google Cloud Project設定
            2. BigQuery API有効化
            3. 課金アカウント設定
            4. サービスアカウント作成
            5. Streamlit Secrets設定
            
            **現在の状況:**
            - Streamlit Secretsに認証情報が見つかりません
            """)
    
    st.markdown("---")
    
    # データソース選択
    if connector.is_connected:
        data_source = st.radio(
            "📊 データソース:",
            ["実データ (BigQuery)", "デモデータ"],
            index=0,
            help="実データは Google Patents BigQuery から取得されます"
        )
        use_real_data = (data_source == "実データ (BigQuery)")
    else:
        st.info("🔄 BigQuery接続後に実データが利用可能になります")
        use_real_data = False
    
    # 分析タイプ選択
    analysis_type = st.selectbox(
        "🎯 分析タイプを選択:",
        ["概要分析", "企業別詳細分析", "技術トレンド分析", "競合比較分析", "タイムライン分析"],
        help="実行したい分析の種類を選択してください"
    )
    
    # 分析パラメータ
    st.markdown("### 📅 分析パラメータ")
    
    start_date = st.date_input(
        "開始日",
        datetime(2015, 1, 1),
        min_value=datetime(2000, 1, 1),
        max_value=datetime.now(),
        help="特許検索の開始日を設定"
    )
    
    data_limit = st.slider(
        "取得データ件数", 
        100, 2000, 500,
        help="BigQueryから取得する最大データ件数"
    )
    
    # システム情報
    st.markdown("---")
    st.markdown("### 📋 システム情報")
    st.markdown("""
    **バージョン:** v1.0.0  
    **最終更新:** 2024年7月  
    **開発:** FUSIONDRIVER INC  
    **プロジェクト:** KSPプロジェクト  
    **GitHub:** [FusionPatentSearch](https://github.com/koji276/FusionPatentSearch)
    """)

# データ取得
@st.cache_data(ttl=3600, show_spinner=False)
def load_patent_data(use_real, start_date_str, limit):
    return connector.search_esc_patents(
        start_date=start_date_str,
        limit=limit,
        use_sample=not use_real
    )

# メインコンテンツ
with st.spinner("📊 特許データを読み込み中..."):
    df = load_patent_data(use_real_data, start_date.strftime('%Y-%m-%d'), data_limit)

if df is not None and not df.empty:
    # データ前処理
    df['filing_date'] = pd.to_datetime(df['filing_date'])
    df['filing_year'] = df['filing_date'].dt.year
    
    # 企業名正規化関数
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
            'SHINKO ELECTRIC': 'Shinko Electric',
            'SUMITOMO OSAKA CEMENT': 'Sumitomo Osaka Cement',
            'NTK CERATEC': 'NTK Ceratec',
            'TSUKUBA SEIKO': 'Tsukuba Seiko',
            'CREATIVE TECHNOLOGY': 'Creative Technology'
        }
        
        for key, value in company_mapping.items():
            if key in name:
                return value
        return name.title()
    
    df['company_normalized'] = df['assignee'].apply(normalize_company_name)
    
    # 分析実行
    if analysis_type == "概要分析":
        st.header("📊 概要分析")
        
        # データソース表示
        if use_real_data and connector.is_connected:
            st.success("📈 **実データ分析結果** - Google Patents BigQuery Dataset")
        else:
            st.info("📊 **デモデータ分析結果** - サンプルデータによる分析")
        
        # KPI表示
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="kpi-card">
                <h3>{len(df):,}</h3>
                <p>総特許数</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            unique_companies = df['company_normalized'].nunique()
            st.markdown(f"""
            <div class="kpi-card">
                <h3>{unique_companies}</h3>
                <p>企業数</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            date_range = f"{df['filing_date'].min().year}-{df['filing_date'].max().year}"
            st.markdown(f"""
            <div class="kpi-card">
                <h3>{date_range}</h3>
                <p>対象期間</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            if len(df) > 0:
                year_span = df['filing_date'].max().year - df['filing_date'].min().year + 1
                avg_per_year = len(df) / year_span if year_span > 0 else len(df)
            else:
                avg_per_year = 0
            st.markdown(f"""
            <div class="kpi-card">
                <h3>{avg_per_year:.1f}</h3>
                <p>年平均特許数</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # グラフ表示
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 年次推移")
            yearly_counts = df.groupby('filing_year').size().reset_index(name='count')
            
            fig = px.line(yearly_counts, x='filing_year', y='count',
                         title='特許出願数の年次推移',
                         markers=True)
            fig.update_layout(
                xaxis_title="年", 
                yaxis_title="特許数",
                hovermode='x unified'
            )
            fig.update_traces(line_color='#1f77b4', line_width=3, marker_size=8)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🏢 企業別ランキング")
            company_counts = df['company_normalized'].value_counts().head(10)
            
            fig = px.bar(
                x=company_counts.values, 
                y=company_counts.index,
                orientation='h',
                title='企業別特許数ランキング (Top 10)',
                color=company_counts.values,
                color_continuous_scale='viridis'
            )
            fig.update_layout(
                xaxis_title="特許数", 
                yaxis_title="企業名",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # 国別分布と日本vs海外比較
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🌍 国別分布")
            country_counts = df['country_code'].value_calls()
            
            fig = px.pie(
                values=country_counts.values, 
                names=country_counts.index,
                title='特許出願国別分布',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🗾 日本 vs 海外比較")
            japanese_companies = [
                'Tokyo Electron', 'Kyocera', 'NGK Insulators', 'TOTO', 
                'Shinko Electric', 'Sumitomo Osaka Cement', 'NTK Ceratec', 
                'Tsukuba Seiko', 'Creative Technology'
            ]
            df['region'] = df['company_normalized'].apply(
                lambda x: '日本企業' if x in japanese_companies else '海外企業'
            )
            
            region_counts = df['region'].value_counts()
            
            fig = px.bar(
                x=region_counts.index, 
                y=region_counts.values,
                title='日本企業 vs 海外企業の特許数比較',
                color=region_counts.index,
                color_discrete_map={'日本企業': '#ff6b6b', '海外企業': '#4ecdc4'}
            )
            fig.update_layout(xaxis_title="地域", yaxis_title="特許数", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "企業別詳細分析":
        st.header("🏢 企業別詳細分析")
        
        # 企業選択
        available_companies = sorted(df['company_normalized'].unique())
        selected_company = st.selectbox(
            "🎯 分析対象企業を選択:",
            options=available_companies,
            help="詳細分析を実行したい企業を選択してください"
        )
        
        company_data = df[df['company_normalized'] == selected_company]
        
        if not company_data.empty:
            # 企業サマリー
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("総特許数", len(company_data))
            
            with col2:
                latest_patent = company_data['filing_date'].max()
                st.metric("最新特許日", latest_patent.strftime('%Y-%m-%d'))
            
            with col3:
                first_patent = company_data['filing_date'].min()
                years_active = latest_patent.year - first_patent.year + 1
                avg_per_year = len(company_data) / years_active if years_active > 0 else len(company_data)
                st.metric("年平均特許数", f"{avg_per_year:.1f}")
            
            with col4:
                country_diversity = company_data['country_code'].nunique()
                st.metric("出願国数", country_diversity)
            
            # 企業の年次推移
            st.subheader(f"📊 {selected_company} の年次推移")
            company_yearly = company_data.groupby('filing_year').size().reset_index(name='count')
            
            fig = px.area(
                company_yearly, 
                x='filing_year', 
                y='count',
                title=f'{selected_company} の特許出願数推移',
                line_color='rgb(131, 90, 241)',
                fill='tonexty'
            )
            fig.update_layout(xaxis_title="年", yaxis_title="特許数")
            st.plotly_chart(fig, use_container_width=True)
            
            # 最新特許リスト
            st.subheader("📝 最新特許リスト")
            latest_patents = company_data.sort_values('filing_date', ascending=False).head(10)
            
            for idx, patent in latest_patents.iterrows():
                with st.expander(f"📄 {patent['publication_number']} ({patent['filing_date'].strftime('%Y-%m-%d')})"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**タイトル:** {patent['title']}")
                        if 'abstract' in patent and patent['abstract']:
                            st.write(f"**概要:** {patent['abstract'][:300]}...")
                    with col2:
                        st.write(f"**国:** {patent['country_code']}")
                        st.write(f"**年:** {patent['filing_year']}")
        else:
            st.warning("選択された企業のデータがありません。")
    
    # 生データ表示
    with st.expander("📋 生データを表示", expanded=False):
        st.subheader("データテーブル")
        
        # フィルタリング機能
        col1, col2, col3 = st.columns(3)
        with col1:
            year_filter = st.multiselect(
                "年でフィルタ",
                options=sorted(df['filing_year'].unique()),
                default=[]
            )
        with col2:
            company_filter = st.multiselect(
                "企業でフィルタ",
                options=sorted(df['company_normalized'].unique()),
                default=[]
            )
        with col3:
            country_filter = st.multiselect(
                "国でフィルタ",
                options=sorted(df['country_code'].unique()),
                default=[]
            )
        
        # フィルタ適用
        filtered_df = df.copy()
        if year_filter:
            filtered_df = filtered_df[filtered_df['filing_year'].isin(year_filter)]
        if company_filter:
            filtered_df = filtered_df[filtered_df['company_normalized'].isin(company_filter)]
        if country_filter:
            filtered_df = filtered_df[filtered_df['country_code'].isin(country_filter)]
        
        st.dataframe(
            filtered_df[['publication_number', 'company_normalized', 'filing_date', 'country_code', 'title']].head(100),
            use_container_width=True
        )
        
        # CSVダウンロード
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 CSVダウンロード",
            data=csv,
            file_name=f"esc_patents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help="フィルタリングされたデータをCSVファイルとしてダウンロード"
        )

else:
    st.error("❌ データの読み込みに失敗しました。")
    st.info("💡 以下の点を確認してください:")
    st.markdown("""
    - BigQuery APIが有効になっているか
    - 課金アカウントが設定されているか  
    - Streamlit Secretsが正しく設定されているか
    - サービスアカウントに適切な権限があるか
    """)

# フッター
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
<strong>FusionPatentSearch</strong> - ESC特許分析システム<br>
開発: FUSIONDRIVER INC | 学術連携: 東京科学大学 齊藤滋規教授研究室<br>
最終更新: 2025年7月22日 | KSPプロジェクト
</div>
""", unsafe_allow_html=True)