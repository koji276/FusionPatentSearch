import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# デュアル接続システムをインポート
try:
    from dual_patent_connector import DualPatentConnector
    DUAL_CONNECTOR_AVAILABLE = True
except ImportError:
    DUAL_CONNECTOR_AVAILABLE = False
    st.error("❌ dual_patent_connector.py が見つかりません")

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
.success-box {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 5px;
    padding: 1rem;
    margin: 1rem 0;
}
.warning-box {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 5px;
    padding: 1rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# メインヘッダー
st.markdown('<div class="main-header">🔍 FusionPatentSearch</div>', unsafe_allow_html=True)
st.markdown("**ESC特許分析システム** - 東京科学大学 齊藤滋規教授プロジェクト版")

# デュアル接続初期化
@st.cache_resource
def init_dual_connector():
    if DUAL_CONNECTOR_AVAILABLE:
        return DualPatentConnector()
    else:
        return None

connector = init_dual_connector()

# サイドバー設定
with st.sidebar:
    st.markdown("### ⚙️ 分析設定")
    
    # 接続ステータス表示
    if connector:
        st.markdown("#### 📡 データソース接続状況")
        
        # BigQuery接続状況（無効化中）
        st.error("❌ BigQuery (一時的に無効化)")
        
        # PatentsView API接続状況
        if hasattr(connector, 'patents_api_connected') and connector.patents_api_connected:
            st.success("✅ PatentsView API (USPTO)")
        else:
            st.error("❌ PatentsView API (USPTO)")
        
        # 詳細接続テスト
        if st.button("🔍 詳細接続テスト"):
            with st.spinner("接続テスト中..."):
                if hasattr(connector, 'test_connections'):
                    results = connector.test_connections()
                    for source, status in results.items():
                        if "✅" in status:
                            st.success(f"{source}: {status}")
                        elif "⚠️" in status:
                            st.warning(f"{source}: {status}")
                        else:
                            st.error(f"{source}: {status}")
    else:
        st.error("❌ 接続システム初期化失敗")
    
    st.markdown("---")
    
    # データソース選択
    if connector:
        available_sources = ["PatentsView API", "デモデータ"]
        
        data_source = st.selectbox(
            "📊 データソース:",
            available_sources,
            index=0,
            help="PatentsView API: 米国特許庁の公式データ"
        )
        
        use_real_data = (data_source != "デモデータ")
    else:
        data_source = "デモデータ"
        use_real_data = False
        st.info("💡 デモデータのみ利用可能")
    
    # 分析タイプ選択
    analysis_type = st.selectbox(
        "🎯 分析タイプを選択:",
        ["概要分析", "企業別詳細分析", "技術トレンド分析", "競合比較分析"],
        help="実行したい分析の種類を選択してください"
    )
    
    # 分析パラメータ
    st.markdown("### 📅 分析パラメータ")
    
    start_date = st.date_input(
        "開始日",
        datetime(2018, 1, 1),
        min_value=datetime(2000, 1, 1),
        max_value=datetime.now(),
        help="特許検索の開始日を設定"
    )
    
    data_limit = st.slider(
        "取得データ件数", 
        50, 500, 200,
        help="取得する最大データ件数"
    )
    
    # システム情報
    st.markdown("---")
    st.markdown("### 📋 システム情報")
    st.markdown(f"""
    **バージョン:** v2.0.0 完成版  
    **データソース:** PatentsView API (USPTO)  
    **最終更新:** 2025年7月22日  
    **開発:** FUSIONDRIVER INC  
    **プロジェクト:** KSPプロジェクト  
    **GitHub:** [FusionPatentSearch](https://github.com/koji276/FusionPatentSearch)
    """)

# データ取得
@st.cache_data(ttl=3600, show_spinner=False)
def load_patent_data(use_real, start_date_str, limit, source):
    if connector and hasattr(connector, 'search_esc_patents'):
        return connector.search_esc_patents(
            start_date=start_date_str,
            limit=limit,
            use_sample=not use_real,
            data_source=source if use_real else "demo"
        )
    else:
        return pd.DataFrame()

# メインコンテンツ
with st.spinner("📊 特許データを読み込み中..."):
    df = load_patent_data(use_real_data, start_date.strftime('%Y-%m-%d'), data_limit, data_source)

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
            'SHINKO ELECTRIC': 'Shinko Electric',
            'ASML': 'ASML',
            'KLA': 'KLA Corporation'
        }
        
        for key, value in company_mapping.items():
            if key in name:
                return value
        return name.title()
    
    df['company_normalized'] = df['assignee'].apply(normalize_company_name)
    
    # 概要分析
    if analysis_type == "概要分析":
        st.header("📊 概要分析")
        
        # データソース表示
        if use_real_data:
            if 'data_source' in df.columns:
                source_counts = df['data_source'].value_counts()
                st.markdown(f"""
                <div class="success-box">
                <strong>📈 実データ分析結果</strong><br>
                データソース: {dict(source_counts)}<br>
                取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.success("📈 **実データ分析結果** - PatentsView API (USPTO)")
        else:
            st.info("📊 **デモデータ分析結果** - 高品質サンプルデータ")
        
        # KPI表示
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("総特許数", f"{len(df):,}", help="取得された特許の総数")
        
        with col2:
            unique_companies = df['company_normalized'].nunique()
            st.metric("企業数", unique_companies, help="分析対象企業数")
        
        with col3:
            date_range = f"{df['filing_date'].min().year}-{df['filing_date'].max().year}"
            st.metric("対象期間", date_range, help="特許出願期間")
        
        with col4:
            year_span = df['filing_date'].max().year - df['filing_date'].min().year + 1
            avg_per_year = len(df) / year_span if year_span > 0 else len(df)
            st.metric("年平均特許数", f"{avg_per_year:.1f}", help="年間平均出願数")
        
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
        
        # 追加分析
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 企業別市場シェア")
            company_counts = df['company_normalized'].value_counts().head(8)
            
            fig = px.pie(
                values=company_counts.values, 
                names=company_counts.index,
                title='企業別特許シェア分布'
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📅 年別特許出願動向")
            
            # 移動平均を追加
            yearly_counts_ma = yearly_counts.copy()
            yearly_counts_ma['moving_avg'] = yearly_counts_ma['count'].rolling(window=3, center=True).mean()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=yearly_counts_ma['filing_year'], 
                y=yearly_counts_ma['count'],
                mode='lines+markers',
                name='実際の出願数',
                line=dict(color='#1f77b4', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=yearly_counts_ma['filing_year'], 
                y=yearly_counts_ma['moving_avg'],
                mode='lines',
                name='3年移動平均',
                line=dict(color='#ff7f0e', width=3, dash='dash')
            ))
            fig.update_layout(
                title='特許出願トレンド分析',
                xaxis_title='年',
                yaxis_title='特許数',
                hovermode='x unified'
            )
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
                # 全体に占める割合
                market_share = (len(company_data) / len(df)) * 100
                st.metric("市場シェア", f"{market_share:.1f}%")
            
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
                            st.write(f"**概要:** {patent['abstract'][:400]}...")
                    with col2:
                        st.write(f"**国:** {patent['country_code']}")
                        st.write(f"**年:** {patent['filing_year']}")
                        if 'data_source' in patent:
                            st.write(f"**データソース:** {patent['data_source']}")
        else:
            st.warning("選択された企業のデータがありません。")
    
    # 技術トレンド分析
    elif analysis_type == "技術トレンド分析":
        st.header("🔬 技術トレンド分析")
        
        # キーワード分析
        st.subheader("🔍 技術キーワード分析")
        
        # タイトルからキーワード抽出
        all_titles = ' '.join(df['title'].astype(str)).upper()
        
        tech_keywords = {
            'ELECTROSTATIC': all_titles.count('ELECTROSTATIC'),
            'CHUCK': all_titles.count('CHUCK'),
            'SEMICONDUCTOR': all_titles.count('SEMICONDUCTOR'),
            'WAFER': all_titles.count('WAFER'),
            'TEMPERATURE': all_titles.count('TEMPERATURE'),
            'CONTROL': all_titles.count('CONTROL'),
            'CURVED': all_titles.count('CURVED'),
            'FLEXIBLE': all_titles.count('FLEXIBLE')
        }
        
        keyword_df = pd.DataFrame(list(tech_keywords.items()), columns=['Keyword', 'Frequency'])
        keyword_df = keyword_df[keyword_df['Frequency'] > 0].sort_values('Frequency', ascending=False)
        
        if not keyword_df.empty:
            fig = px.bar(keyword_df, x='Frequency', y='Keyword', orientation='h',
                        title='技術キーワード出現頻度')
            st.plotly_chart(fig, use_container_width=True)
    
    # 生データ表示
    with st.expander("📋 生データを表示", expanded=False):
        st.subheader("データテーブル")
        
        # 表示用カラム選択
        display_columns = ['publication_number', 'company_normalized', 'filing_date', 'country_code', 'title']
        if 'data_source' in df.columns:
            display_columns.append('data_source')
        
        # フィルタリング機能
        col1, col2 = st.columns(2)
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
        
        # フィルタ適用
        filtered_df = df.copy()
        if year_filter:
            filtered_df = filtered_df[filtered_df['filing_year'].isin(year_filter)]
        if company_filter:
            filtered_df = filtered_df[filtered_df['company_normalized'].isin(company_filter)]
        
        st.dataframe(filtered_df[display_columns].head(100), use_container_width=True)
        
        # CSV ダウンロード
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
    - dual_patent_connector.py が正しく配置されているか
    - PatentsView APIが正常に動作しているか
    - インターネット接続が安定しているか
    """)

# フッター
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
<strong>FusionPatentSearch v2.0 完成版</strong> - ESC特許分析システム<br>
開発: FUSIONDRIVER INC | 学術連携: 東京科学大学 齊藤滋規教授研究室<br>
データソース: USPTO PatentsView API | GitHub: FusionPatentSearch<br>
最終更新: 2025年7月22日 | KSPプロジェクト<br>
<em>5万円のイノベーションリサーチ社サービスの完全代替システム</em>
</div>
""", unsafe_allow_html=True)
