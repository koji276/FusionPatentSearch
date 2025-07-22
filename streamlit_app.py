import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
from datetime import datetime, timedelta
import re
from collections import Counter
from wordcloud import WordCloud
import networkx as nx

# 日本語フォント設定
plt.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']
warnings.filterwarnings('ignore')

# ページ設定
st.set_page_config(
    page_title="🔍 FusionPatentSearch - ESC特許分析システム",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS スタイリング
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f8ff, #e6f3ff);
        border-radius: 10px;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .company-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .sidebar-header {
        color: #1f77b4;
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# 対象企業リスト
TARGET_COMPANIES = {
    "日本企業": [
        "新光電気工業", "TOTO", "住友大阪セメント", "京セラ", 
        "日本ガイシ", "NTKセラテック", "筑波精工", 
        "クリエイティブテクノロジー", "東京エレクトロン"
    ],
    "海外企業": [
        "Applied Materials", "Lam Research", "Entegris", 
        "FM Industries", "MiCo", "SEMCO Engineering", 
        "Calitech", "Beijing U-Precision"
    ]
}

# ESC関連キーワード
ESC_KEYWORDS = {
    "英語": [
        "curved ESC", "flexible ESC", "bendable electrostatic chuck",
        "variable curvature ESC", "conformal chuck", "wafer distortion control",
        "substrate warpage", "electrostatic chuck", "ESC"
    ],
    "日本語": [
        "静電チャック", "曲面チャック", "湾曲チャック", "可撓性チャック",
        "曲面", "湾曲", "可撓性", "ウエハ反り", "基板歪み", "反り補正"
    ]
}

def safe_nlargest(df, n, column):
    """安全なnlargest関数"""
    try:
        if df.empty:
            return pd.DataFrame()
        
        if column not in df.columns:
            st.warning(f"カラム '{column}' が見つかりません。")
            return pd.DataFrame()
        
        # NaNや無効な値を除外
        valid_df = df.dropna(subset=[column]).copy()
        
        if valid_df.empty:
            st.warning(f"'{column}' カラムに有効なデータがありません。")
            return pd.DataFrame()
        
        # 日付の場合は適切に処理
        if column == 'filing_date':
            valid_df[column] = pd.to_datetime(valid_df[column], errors='coerce')
            valid_df = valid_df.dropna(subset=[column])
        
        if valid_df.empty:
            return pd.DataFrame()
        
        # nlargestを実行
        return valid_df.nlargest(min(n, len(valid_df)), column)
        
    except Exception as e:
        st.error(f"データ処理でエラーが発生しました: {str(e)}")
        return pd.DataFrame()

def generate_demo_data():
    """デモデータ生成"""
    np.random.seed(42)
    
    all_companies = TARGET_COMPANIES["日本企業"] + TARGET_COMPANIES["海外企業"]
    years = list(range(2010, 2025))
    
    data = []
    patent_id = 1
    
    for year in years:
        for company in all_companies:
            # 年度ごとの特許数をランダムに生成
            num_patents = np.random.poisson(3) + 1
            
            for _ in range(num_patents):
                filing_date = datetime(year, np.random.randint(1, 13), np.random.randint(1, 29))
                
                data.append({
                    'patent_id': f'JP{patent_id:06d}',
                    'title': f'曲面ESC技術に関する特許 #{patent_id}',
                    'assignee': company,
                    'filing_date': filing_date,
                    'country': 'JP' if company in TARGET_COMPANIES["日本企業"] else 'US',
                    'technology_category': np.random.choice(['基礎技術', '応用技術', '製造技術', '制御技術']),
                    'abstract': f'この発明は{company}による曲面ESC技術の改良に関する。'
                })
                patent_id += 1
    
    return pd.DataFrame(data)

def create_overview_dashboard(df):
    """概要分析ダッシュボード"""
    st.markdown("## 📊 概要分析")
    
    if df.empty:
        st.warning("データがありません。")
        return
    
    # KPI指標
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総特許数", len(df))
    
    with col2:
        unique_companies = df['assignee'].nunique() if 'assignee' in df.columns else 0
        st.metric("企業数", unique_companies)
    
    with col3:
        if 'filing_date' in df.columns:
            date_range = f"{df['filing_date'].min().year} - {df['filing_date'].max().year}"
        else:
            date_range = "N/A"
        st.metric("対象期間", date_range)
    
    with col4:
        japan_count = len(df[df['assignee'].isin(TARGET_COMPANIES["日本企業"])]) if 'assignee' in df.columns else 0
        st.metric("日本企業特許数", japan_count)
    
    st.markdown("---")
    
    # 年次推移グラフ
    if 'filing_date' in df.columns:
        st.markdown("### 📈 年次推移")
        
        df_yearly = df.copy()
        df_yearly['year'] = pd.to_datetime(df_yearly['filing_date']).dt.year
        yearly_counts = df_yearly.groupby('year').size().reset_index(name='count')
        
        fig = px.line(yearly_counts, x='year', y='count', 
                     title='年次特許出願数推移',
                     markers=True)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # 企業別ランキング
    if 'assignee' in df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏆 企業別ランキング（TOP10）")
            company_counts = df['assignee'].value_counts().head(10)
            
            fig = px.bar(
                x=company_counts.values,
                y=company_counts.index,
                orientation='h',
                title="企業別特許数",
                labels={'x': '特許数', 'y': '企業'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 🌍 日本 vs 海外比較")
            
            japan_patents = df[df['assignee'].isin(TARGET_COMPANIES["日本企業"])]
            overseas_patents = df[df['assignee'].isin(TARGET_COMPANIES["海外企業"])]
            
            comparison_data = pd.DataFrame({
                '地域': ['日本', '海外'],
                '特許数': [len(japan_patents), len(overseas_patents)]
            })
            
            fig = px.pie(comparison_data, values='特許数', names='地域',
                        title="地域別特許分布")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

def create_company_analysis(df, selected_company):
    """企業別詳細分析"""
    st.markdown(f"## 🏢 企業別分析: {selected_company}")
    
    if df.empty:
        st.warning("データがありません。")
        return
    
    # 選択企業のデータをフィルタリング
    company_df = df[df['assignee'] == selected_company] if 'assignee' in df.columns else pd.DataFrame()
    
    if company_df.empty:
        st.warning(f"{selected_company}のデータがありません。")
        return
    
    # 企業情報カード
    st.markdown(f"""
    <div class="company-card">
        <h3>📋 {selected_company} 基本情報</h3>
        <p><strong>総特許数:</strong> {len(company_df)}</p>
        <p><strong>最新出願:</strong> {company_df['filing_date'].max().strftime('%Y-%m-%d') if 'filing_date' in company_df.columns else 'N/A'}</p>
        <p><strong>出願期間:</strong> {company_df['filing_date'].min().year if 'filing_date' in company_df.columns else 'N/A'} - {company_df['filing_date'].max().year if 'filing_date' in company_df.columns else 'N/A'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 年次推移
        if 'filing_date' in company_df.columns:
            st.markdown("### 📊 年次推移")
            company_yearly = company_df.copy()
            company_yearly['year'] = pd.to_datetime(company_yearly['filing_date']).dt.year
            yearly_counts = company_yearly.groupby('year').size().reset_index(name='count')
            
            fig = px.bar(yearly_counts, x='year', y='count',
                        title=f"{selected_company} 年次特許出願数")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 技術カテゴリ分布
        if 'technology_category' in company_df.columns:
            st.markdown("### 🔬 技術カテゴリ分布")
            tech_counts = company_df['technology_category'].value_counts()
            
            fig = px.pie(values=tech_counts.values, names=tech_counts.index,
                        title="技術カテゴリ別特許分布")
            st.plotly_chart(fig, use_container_width=True)
    
    # 最新特許リスト
    st.markdown("### 📝 最新特許リスト")
    if 'filing_date' in company_df.columns:
        latest_patents = safe_nlargest(company_df, 10, 'filing_date')
        if not latest_patents.empty:
            display_columns = ['patent_id', 'title', 'filing_date']
            available_columns = [col for col in display_columns if col in latest_patents.columns]
            st.dataframe(latest_patents[available_columns], use_container_width=True)
        else:
            st.info("表示する最新特許がありません。")

def create_technology_trends(df):
    """技術トレンド分析"""
    st.markdown("## 🔬 技術トレンド分析")
    
    if df.empty:
        st.warning("データがありません。")
        return
    
    # 技術キーワード分析
    st.markdown("### 🔍 技術キーワード分析")
    
    # サンプルキーワード頻度データを生成
    keywords = ESC_KEYWORDS["英語"] + ESC_KEYWORDS["日本語"]
    keyword_counts = {keyword: np.random.randint(5, 50) for keyword in keywords[:10]}
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 頻出キーワードランキング
        st.markdown("#### 📊 頻出キーワードTOP10")
        keyword_df = pd.DataFrame(list(keyword_counts.items()), columns=['Keyword', 'Count'])
        keyword_df = keyword_df.sort_values('Count', ascending=True)
        
        fig = px.bar(keyword_df, x='Count', y='Keyword', orientation='h',
                    title="キーワード出現頻度")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # ワードクラウド
        st.markdown("#### ☁️ キーワードクラウド")
        try:
            wordcloud = WordCloud(
                width=400, height=300,
                background_color='white',
                font_path=None,
                relative_scaling=0.5,
                colormap='viridis'
            ).generate_from_frequencies(keyword_counts)
            
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
        except Exception as e:
            st.info("ワードクラウドの生成に失敗しました。")
    
    # 技術カテゴリトレンド
    if 'technology_category' in df.columns and 'filing_date' in df.columns:
        st.markdown("### 📈 技術カテゴリ別トレンド")
        
        df_trend = df.copy()
        df_trend['year'] = pd.to_datetime(df_trend['filing_date']).dt.year
        
        category_trend = df_trend.groupby(['year', 'technology_category']).size().reset_index(name='count')
        
        fig = px.line(category_trend, x='year', y='count', color='technology_category',
                     title="技術カテゴリ別年次推移", markers=True)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def create_competitive_analysis(df):
    """競合比較分析"""
    st.markdown("## ⚔️ 競合比較分析")
    
    if df.empty:
        st.warning("データがありません。")
        return
    
    # 日本企業 vs 海外企業比較
    st.markdown("### 🌍 日本企業 vs 海外企業")
    
    if 'assignee' in df.columns:
        japan_companies = [comp for comp in df['assignee'].unique() 
                          if comp in TARGET_COMPANIES["日本企業"]]
        overseas_companies = [comp for comp in df['assignee'].unique() 
                             if comp in TARGET_COMPANIES["海外企業"]]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 日本企業ランキング
            st.markdown("#### 🇯🇵 日本企業TOP5")
            japan_df = df[df['assignee'].isin(japan_companies)]
            japan_ranking = japan_df['assignee'].value_counts().head(5)
            
            if not japan_ranking.empty:
                fig = px.bar(x=japan_ranking.values, y=japan_ranking.index, orientation='h',
                            title="日本企業特許数ランキング")
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 海外企業ランキング
            st.markdown("#### 🌎 海外企業TOP5")
            overseas_df = df[df['assignee'].isin(overseas_companies)]
            overseas_ranking = overseas_df['assignee'].value_counts().head(5)
            
            if not overseas_ranking.empty:
                fig = px.bar(x=overseas_ranking.values, y=overseas_ranking.index, orientation='h',
                            title="海外企業特許数ランキング")
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
    
    # 企業×年度ヒートマップ
    if 'assignee' in df.columns and 'filing_date' in df.columns:
        st.markdown("### 🔥 企業×年度ヒートマップ")
        
        df_heatmap = df.copy()
        df_heatmap['year'] = pd.to_datetime(df_heatmap['filing_date']).dt.year
        
        # 上位10社のみを表示
        top_companies = df['assignee'].value_counts().head(10).index
        df_heatmap = df_heatmap[df_heatmap['assignee'].isin(top_companies)]
        
        heatmap_data = df_heatmap.groupby(['assignee', 'year']).size().unstack(fill_value=0)
        
        if not heatmap_data.empty:
            fig = px.imshow(heatmap_data, 
                           title="企業×年度別特許出願数ヒートマップ",
                           labels=dict(x="年度", y="企業", color="特許数"))
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

def create_timeline_analysis(df):
    """タイムライン分析"""
    st.markdown("## ⏰ タイムライン分析")
    
    if df.empty:
        st.warning("データがありません。")
        return
    
    if 'filing_date' not in df.columns:
        st.warning("日付データがありません。")
        return
    
    # 年度フィルタ
    df_copy = df.copy()
    df_copy['filing_date'] = pd.to_datetime(df_copy['filing_date'])
    
    min_year = int(df_copy['filing_date'].dt.year.min())
    max_year = int(df_copy['filing_date'].dt.year.max())
    
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.slider("開始年", min_year, max_year, min_year)
    with col2:
        end_year = st.slider("終了年", min_year, max_year, max_year)
    
    # フィルタリング
    filtered_df = df_copy[
        (df_copy['filing_date'].dt.year >= start_year) & 
        (df_copy['filing_date'].dt.year <= end_year)
    ]
    
    if filtered_df.empty:
        st.warning("選択された期間にデータがありません。")
        return
    
    # 期間別統計
    st.markdown("### 📊 期間別統計")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("期間内特許数", len(filtered_df))
    
    with col2:
        active_companies = filtered_df['assignee'].nunique() if 'assignee' in filtered_df.columns else 0
        st.metric("活動企業数", active_companies)
    
    with col3:
        avg_per_year = len(filtered_df) / max(1, (end_year - start_year + 1))
        st.metric("年平均出願数", f"{avg_per_year:.1f}")
    
    # 企業別推移比較
    if 'assignee' in filtered_df.columns:
        st.markdown("### 📈 主要企業の推移比較")
        
        # 上位5社を選択
        top5_companies = filtered_df['assignee'].value_counts().head(5).index
        
        selected_companies = st.multiselect(
            "比較する企業を選択してください：",
            options=top5_companies.tolist(),
            default=top5_companies.tolist()[:3]
        )
        
        if selected_companies:
            company_trend_data = []
            
            for company in selected_companies:
                company_data = filtered_df[filtered_df['assignee'] == company].copy()
                company_data['year'] = company_data['filing_date'].dt.year
                yearly_counts = company_data.groupby('year').size().reset_index(name='count')
                yearly_counts['company'] = company
                company_trend_data.append(yearly_counts)
            
            if company_trend_data:
                all_trends = pd.concat(company_trend_data, ignore_index=True)
                
                fig = px.line(all_trends, x='year', y='count', color='company',
                             title="選択企業の年次推移比較", markers=True)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    # 最新特許リスト
    st.markdown("### 📝 期間内最新特許リスト")
    
    latest_patents = safe_nlargest(filtered_df, 20, 'filing_date')
    if not latest_patents.empty:
        display_columns = ['patent_id', 'title', 'assignee', 'filing_date']
        available_columns = [col for col in display_columns if col in latest_patents.columns]
        st.dataframe(latest_patents[available_columns], use_container_width=True)
    else:
        st.info("表示する特許がありません。")

def main():
    """メイン関数"""
    
    # ヘッダー
    st.markdown("""
    <div class="main-header">
        🔍 FusionPatentSearch<br>
        <small>ESC特許分析システム - 東京科学大学 齊藤滋規教授プロジェクト</small>
    </div>
    """, unsafe_allow_html=True)
    
    # サイドバー
    with st.sidebar:
        st.markdown('<div class="sidebar-header">⚙️ 分析設定</div>', unsafe_allow_html=True)
        
        # 分析タイプ選択
        analysis_type = st.selectbox(
            "分析タイプを選択:",
            ["概要分析", "企業別詳細分析", "技術トレンド分析", "競合比較分析", "タイムライン分析"]
        )
        
        st.markdown("---")
        
        # データソース選択
        use_demo_data = st.checkbox("デモデータを使用", value=True)
        
        if use_demo_data:
            st.info("💡 デモデータを使用しています。実際のBigQueryデータへの接続は設定が必要です。")
        
        st.markdown("---")
        
        # 企業選択（企業別分析の場合）
        selected_company = None
        if analysis_type == "企業別詳細分析":
            all_companies = TARGET_COMPANIES["日本企業"] + TARGET_COMPANIES["海外企業"]
            selected_company = st.selectbox("企業を選択:", all_companies)
        
        st.markdown("---")
        
        # システム情報
        st.markdown("### ℹ️ システム情報")
        st.markdown("""
        - **バージョン**: v1.0.0
        - **最終更新**: 2024年7月
        - **開発**: 東京科学大学
        - **GitHub**: [FusionPatentSearch](https://github.com/koji276/FusionPatentSearch)
        """)
    
    # データ読み込み
    try:
        if use_demo_data:
            with st.spinner("デモデータを生成しています..."):
                df = generate_demo_data()
                st.success(f"✅ デモデータを読み込みました（{len(df)}件の特許データ）")
        else:
            st.warning("⚠️ BigQueryデータベースへの接続設定が必要です。現在はデモデータのみ利用可能です。")
            df = generate_demo_data()
    
    except Exception as e:
        st.error(f"❌ データの読み込みに失敗しました: {str(e)}")
        st.info("デモデータを使用します。")
        df = generate_demo_data()
    
    # 分析画面の表示
    try:
        if analysis_type == "概要分析":
            create_overview_dashboard(df)
        
        elif analysis_type == "企業別詳細分析":
            if selected_company:
                create_company_analysis(df, selected_company)
            else:
                st.warning("企業を選択してください。")
        
        elif analysis_type == "技術トレンド分析":
            create_technology_trends(df)
        
        elif analysis_type == "競合比較分析":
            create_competitive_analysis(df)
        
        elif analysis_type == "タイムライン分析":
            create_timeline_analysis(df)
    
    except Exception as e:
        st.error(f"❌ 分析処理でエラーが発生しました: {str(e)}")
        st.info("データの形式や内容を確認してください。")
    
    # フッター
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>🔬 <strong>FusionPatentSearch</strong> - Developed by Tokyo Institute of Science and Technology</p>
        <p>📧 Contact: <a href="mailto:saito@titech.ac.jp">saito@titech.ac.jp</a> | 
           📚 <a href="https://github.com/koji276/FusionPatentSearch">GitHub Repository</a></p>
        <p><small>© 2024 Tokyo Institute of Science and Technology. All rights reserved.</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()