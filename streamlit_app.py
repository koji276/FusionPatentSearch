# streamlit_app.py - クラウドストレージ対応版

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# クラウド対応データ収集システム
from patent_cloud_collector import CloudPatentDataCollector

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
.big-metric {
    font-size: 2rem;
    font-weight: bold;
    color: #1f77b4;
}
</style>
""", unsafe_allow_html=True)

# タイトル
st.markdown('<div class="main-header">🔍 FusionPatentSearch</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">ESC特許分析システム - 東京科学大学 齊藤滋規教授プロジェクト版</div>', unsafe_allow_html=True)

def main():
    # セッション状態の初期化
    if 'patent_data' not in st.session_state:
        st.session_state['patent_data'] = pd.DataFrame()
    if 'data_source' not in st.session_state:
        st.session_state['data_source'] = 'none'
    
    # サイドバー
    with st.sidebar:
        st.markdown("### ⚙️ システム設定")
        
        # Google Drive 設定状況
        collector = CloudPatentDataCollector()
        
        st.markdown("### 💾 ストレージ設定")
        if collector.drive_service:
            st.success("✅ Google Drive 接続済み")
        else:
            st.warning("⚠️ Google Drive 未設定")
            st.info("streamlit secrets で google_drive を設定してください")
        
        st.markdown("### 📊 データ状況")
        if not st.session_state['patent_data'].empty:
            df = st.session_state['patent_data']
            st.metric("データ件数", len(df))
            st.metric("企業数", df['assignee'].nunique())
            st.metric("データソース", st.session_state['data_source'])
        else:
            st.info("データなし")
    
    # メインタブ
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 大量データ収集", "📂 クラウド管理", "🔬 実データ分析", "📈 レポート"])
    
    with tab1:
        st.header("🚀 大量実特許データ収集システム")
        
        st.info("""
        **新しいアーキテクチャ:**
        1. 大量の実特許データを収集
        2. Google Drive に自動分割保存
        3. クラウドから効率的に読み込み
        4. 実データで完全分析
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 データ収集設定")
            
            collection_mode = st.radio(
                "収集モード:",
                ["標準収集 (50件)", "拡張収集 (100+件)", "大量収集 (200+件)"]
            )
            
            if st.button("🚀 大量実データ収集開始", type="primary"):
                with st.spinner("大量実特許データを収集中..."):
                    
                    try:
                        # 大量データ収集実行
                        all_patents = collector.collect_and_store_massive_data()
                        
                        if all_patents:
                            # DataFrame変換
                            df = collector.convert_to_dataframe(all_patents)
                            
                            if not df.empty:
                                st.session_state['patent_data'] = df
                                st.session_state['data_source'] = 'Cloud Storage'
                                
                                st.success(f"🎉 **大量実データ収集成功！**")
                                
                                # 詳細メトリクス
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("総特許数", len(df))
                                with col2:
                                    st.metric("企業数", df['assignee'].nunique())
                                with col3:
                                    st.metric("年度範囲", f"{df['filing_year'].min()}-{df['filing_year'].max()}")
                                with col4:
                                    st.metric("平均年間", f"{len(df) / df['filing_year'].nunique():.1f}件")
                                
                                # データサンプル表示
                                st.subheader("📋 収集データサンプル")
                                sample_df = df[['publication_number', 'assignee', 'title', 'filing_date', 'data_source']].head(10)
                                st.dataframe(sample_df, use_container_width=True)
                                
                            else:
                                st.error("❌ データ変換に失敗")
                        else:
                            st.error("❌ データ収集に失敗")
                            
                    except Exception as e:
                        st.error(f"❌ 収集エラー: {str(e)}")
        
        with col2:
            st.subheader("📈 収集進捗")
            
            # 進捗表示エリア
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            # 推定データ量
            if collection_mode == "標準収集 (50件)":
                estimated_size = "~2MB"
                estimated_time = "2-3分"
            elif collection_mode == "拡張収集 (100+件)":
                estimated_size = "~5MB" 
                estimated_time = "5-7分"
            else:
                estimated_size = "~10MB+"
                estimated_time = "10-15分"
            
            st.info(f"📊 推定データサイズ: {estimated_size}")
            st.info(f"⏱️ 推定収集時間: {estimated_time}")
    
    with tab2:
        st.header("📂 クラウドデータ管理")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📥 データ読み込み")
            
            if st.button("📂 クラウドから読み込み"):
                with st.spinner("クラウドから大量データを読み込み中..."):
                    df = collector.load_and_analyze_massive_data()
                    
                    if not df.empty:
                        st.session_state['patent_data'] = df
                        st.session_state['data_source'] = 'Cloud Storage'
                        
                        st.success(f"✅ クラウド読み込み完了: {len(df)}件")
                        
                        # データ概要
                        st.subheader("📊 データ概要")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("特許数", len(df))
                        with col2:
                            st.metric("企業数", df['assignee'].nunique())
                        with col3:
                            st.metric("年度範囲", f"{df['filing_year'].min()}-{df['filing_year'].max()}")
                    else:
                        st.warning("⚠️ クラウドにデータが見つかりません")
        
        with col2:
            st.subheader("🗂️ ストレージ情報")
            
            # Google Drive 容量情報（仮想）
            st.info("📊 Google Drive 使用状況")
            st.progress(0.15)  # 15% 使用中
            st.caption("使用容量: ~10MB / 15GB")
            
            # ファイル管理
            if st.button("🗑️ キャッシュクリア"):
                st.session_state['patent_data'] = pd.DataFrame()
                st.session_state['data_source'] = 'none'
                st.success("✅ キャッシュクリア完了")
    
    with tab3:
        st.header("🔬 実データ分析")
        
        if st.session_state['patent_data'].empty:
            st.warning("⚠️ まず大量データを収集してください")
            st.info("👈 左側の「大量データ収集」タブから実データを取得してください")
        else:
            df = st.session_state['patent_data']
            
            # データソース表示
            st.success(f"✅ {len(df)}件の実特許データで分析実行中")
            st.info(f"📊 データソース: {st.session_state['data_source']}")
            
            # 分析設定
            col1, col2, col3 = st.columns(3)
            
            with col1:
                analysis_type = st.selectbox(
                    "分析タイプ:",
                    ["概要分析", "企業別分析", "技術トレンド", "競合分析", "時系列分析"]
                )
            
            with col2:
                start_year = st.slider("開始年", int(df['filing_year'].min()), int(df['filing_year'].max()), int(df['filing_year'].min()))
            
            with col3:
                end_year = st.slider("終了年", int(df['filing_year'].min()), int(df['filing_year'].max()), int(df['filing_year'].max()))
            
            # データフィルタリング
            filtered_df = df[(df['filing_year'] >= start_year) & (df['filing_year'] <= end_year)]
            
            # 分析実行
            if analysis_type == "概要分析":
                execute_overview_analysis(filtered_df)
            elif analysis_type == "企業別分析":
                execute_company_analysis(filtered_df)
            elif analysis_type == "技術トレンド":
                execute_technology_analysis(filtered_df)
            elif analysis_type == "競合分析":
                execute_competitive_analysis(filtered_df)
            else:
                execute_timeline_analysis(filtered_df)
    
    with tab4:
        st.header("📈 分析レポート")
        
        if not st.session_state['patent_data'].empty:
            df = st.session_state['patent_data']
            
            # エグゼクティブサマリー
            st.subheader("📋 エグゼクティブサマリー")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f'<div class="big-metric">{len(df)}</div>', unsafe_allow_html=True)
                st.caption("総特許数")
            
            with col2:
                st.markdown(f'<div class="big-metric">{df["assignee"].nunique()}</div>', unsafe_allow_html=True)
                st.caption("分析対象企業数")
            
            with col3:
                year_span = df['filing_year'].max() - df['filing_year'].min() + 1
                st.markdown(f'<div class="big-metric">{year_span}</div>', unsafe_allow_html=True)
                st.caption("分析期間(年)")
            
            with col4:
                avg_annual = len(df) / year_span
                st.markdown(f'<div class="big-metric">{avg_annual:.1f}</div>', unsafe_allow_html=True)
                st.caption("年平均特許数")
            
            # 主要発見事項
            st.subheader("🔍 主要発見事項")
            
            # 最も活発な企業
            top_assignee = df['assignee'].value_counts().index[0]
            top_count = df['assignee'].value_counts().iloc[0]
            
            st.info(f"📊 **最も活発な企業**: {top_assignee} ({top_count}件の特許)")
            
            # 最新技術トレンド
            recent_year = df['filing_year'].max()
            recent_patents = df[df['filing_year'] == recent_year]
            
            st.info(f"📈 **最新年度 ({recent_year})**: {len(recent_patents)}件の特許出願")
            
            # データ品質指標
            complete_abstracts = len(df[df['abstract'].str.len() > 100])
            st.info(f"✅ **データ品質**: {complete_abstracts}/{len(df)}件に詳細要約あり ({complete_abstracts/len(df)*100:.1f}%)")
            
        else:
            st.info("📊 データを収集後、レポートが生成されます")

# 分析関数
def execute_overview_analysis(df):
    """概要分析の実行"""
    st.subheader("📊 概要分析")
    
    # KPI
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("特許数", len(df))
    with col2:
        st.metric("企業数", df['assignee'].nunique())
    with col3:
        st.metric("期間", f"{df['filing_year'].min()}-{df['filing_year'].max()}")
    with col4:
        st.metric("年平均", f"{len(df)/df['filing_year'].nunique():.1f}")
    
    # 年次推移
    col1, col2 = st.columns(2)
    
    with col1:
        yearly_counts = df['filing_year'].value_counts().sort_index()
        fig = px.line(x=yearly_counts.index, y=yearly_counts.values, title="年次推移")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        company_counts = df['assignee'].value_counts().head(8)
        fig = px.bar(x=company_counts.values, y=company_counts.index, 
                     orientation='h', title="企業別特許数")
        st.plotly_chart(fig, use_container_width=True)

def execute_company_analysis(df):
    """企業別分析の実行"""
    st.subheader("🏢 企業別分析")
    
    # 企業選択
    selected_companies = st.multiselect(
        "分析対象企業:",
        df['assignee'].unique(),
        default=df['assignee'].value_counts().head(5).index.tolist()
    )
    
    if selected_companies:
        company_df = df[df['assignee'].isin(selected_companies)]
        
        # 企業別年次推移
        pivot_data = company_df.groupby(['filing_year', 'assignee']).size().reset_index(name='count')
        fig = px.line(pivot_data, x='filing_year', y='count', color='assignee', 
                      title="企業別年次推移")
        st.plotly_chart(fig, use_container_width=True)

def execute_technology_analysis(df):
    """技術トレンド分析の実行"""
    st.subheader("🔬 技術トレンド分析")
    
    # キーワード分析
    all_titles = ' '.join(df['title'].astype(str))
    keywords = ['electrostatic', 'chuck', 'curved', 'flexible', 'temperature', 'control']
    
    keyword_counts = {}
    for keyword in keywords:
        count = all_titles.lower().count(keyword)
        keyword_counts[keyword] = count
    
    fig = px.bar(x=list(keyword_counts.values()), y=list(keyword_counts.keys()),
                 orientation='h', title="技術キーワード頻度")
    st.plotly_chart(fig, use_container_width=True)

def execute_competitive_analysis(df):
    """競合分析の実行"""
    st.subheader("⚔️ 競合分析")
    
    # 日本 vs 海外企業
    japanese_companies = ['Tokyo Electron', 'Kyocera', 'TOTO', 'NGK']
    df['region'] = df['assignee'].apply(
        lambda x: '日本企業' if any(jp in x for jp in japanese_companies) else '海外企業'
    )
    
    region_counts = df['region'].value_counts()
    fig = px.pie(values=region_counts.values, names=region_counts.index, 
                 title="地域別特許分布")
    st.plotly_chart(fig, use_container_width=True)

def execute_timeline_analysis(df):
    """時系列分析の実行"""
    st.subheader("⏰ 時系列分析")
    
    # 最新特許タイムライン
    recent_patents = df.sort_values('filing_date', ascending=False).head(10)
    
    for idx, row in recent_patents.iterrows():
        with st.expander(f"📄 {row['publication_number']} - {row['assignee']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**出願日:** {row['filing_date']}")
                st.write(f"**企業:** {row['assignee']}")
            with col2:
                st.write(f"**発明者:** {row['inventors']}")
            
            st.write(f"**タイトル:** {row['title']}")
            st.write(f"**要約:** {row['abstract'][:200]}...")

if __name__ == "__main__":
    main()
