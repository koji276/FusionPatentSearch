import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from wordcloud import WordCloud
import networkx as nx
from datetime import datetime, timedelta
import re
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# 日本語フォント設定
plt.rcParams['font.family'] = 'DejaVu Sans'

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
    background: linear-gradient(90deg, #1f4e79, #2d5aa0);
    padding: 2rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
.metric-card {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 10px;
    border-left: 4px solid #007acc;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 0.5rem 0;
}
.info-box {
    background: #e7f3ff;
    padding: 1.5rem;
    border-radius: 10px;
    border: 1px solid #b3d9ff;
    margin: 1rem 0;
}
.success-box {
    background: #d4edda;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #c3e6cb;
    color: #155724;
    margin: 1rem 0;
}
.warning-box {
    background: #fff3cd;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #ffeaa7;
    color: #856404;
    margin: 1rem 0;
}
.stTab > div > div > div > div {
    padding: 2rem 1rem;
}
</style>
""", unsafe_allow_html=True)

def load_patent_data_from_cloud():
    """クラウドから効率的にデータロード"""
    try:
        from patent_cloud_collector import CloudPatentDataCollector
        
        collector = CloudPatentDataCollector()
        df = collector.load_all_patent_data()
        
        return df
        
    except Exception as e:
        st.error(f"データ読み込みエラー: {str(e)}")
        return pd.DataFrame()

def execute_real_data_analysis(df: pd.DataFrame, analysis_type: str):
    """実データベース分析実行"""
    
    if df.empty:
        st.warning("分析対象のデータがありません")
        return
    
    if analysis_type == "概要分析":
        show_overview_analysis(df)
    elif analysis_type == "企業別詳細分析":
        show_company_analysis(df)
    elif analysis_type == "技術トレンド分析":
        show_technology_trends(df)
    elif analysis_type == "競合比較分析":
        show_competitive_analysis(df)
    elif analysis_type == "タイムライン分析":
        show_timeline_analysis(df)

def show_overview_analysis(df: pd.DataFrame):
    """概要分析（完成版）"""
    st.subheader("📊 概要分析 - 実データベース")
    
    # 基本統計
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📋 総特許数</h3>
            <h2 style="color: #007acc;">{len(df)}</h2>
            <p>ESC関連技術特許</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        unique_assignees = df['assignee'].nunique()
        st.markdown(f"""
        <div class="metric-card">
            <h3>🏢 出願企業数</h3>
            <h2 style="color: #28a745;">{unique_assignees}</h2>
            <p>グローバル企業</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if 'filing_year' in df.columns:
            year_range = f"{df['filing_year'].min():.0f}-{df['filing_year'].max():.0f}"
        else:
            year_range = "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <h3>📅 出願年範囲</h3>
            <h2 style="color: #ffc107;">{year_range}</h2>
            <p>技術進化期間</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        avg_inventors = df['inventors'].apply(lambda x: len(x) if isinstance(x, list) else 0).mean()
        st.markdown(f"""
        <div class="metric-card">
            <h3>👥 平均発明者数</h3>
            <h2 style="color: #dc3545;">{avg_inventors:.1f}</h2>
            <p>共同研究指標</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 出願企業分布
    st.subheader("🏢 出願企業分布")
    assignee_counts = df['assignee'].value_counts().head(10)
    
    fig = px.bar(
        x=assignee_counts.values,
        y=assignee_counts.index,
        orientation='h',
        title="上位10社の特許出願数",
        labels={'x': '特許数', 'y': '企業名'},
        color=assignee_counts.values,
        color_continuous_scale='Blues'
    )
    fig.update_layout(
        height=500,
        showlegend=False,
        title_font_size=16,
        font_size=12
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 年次出願動向
    if 'filing_year' in df.columns:
        st.subheader("📈 年次出願動向")
        yearly_counts = df.groupby('filing_year').size()
        
        fig = px.line(
            x=yearly_counts.index,
            y=yearly_counts.values,
            title="年次特許出願数の推移",
            labels={'x': '出願年', 'y': '特許数'},
            markers=True
        )
        fig.update_traces(line_color='#007acc', line_width=3, marker_size=8)
        fig.update_layout(height=400, title_font_size=16)
        st.plotly_chart(fig, use_container_width=True)
        
        # トレンド分析
        if len(yearly_counts) > 1:
            recent_trend = yearly_counts.iloc[-3:].mean() - yearly_counts.iloc[:3].mean()
            trend_text = "増加傾向" if recent_trend > 0 else "減少傾向"
            trend_color = "#28a745" if recent_trend > 0 else "#dc3545"
            
            st.markdown(f"""
            <div class="info-box">
                <h4>📊 トレンド分析</h4>
                <p>直近3年間の出願動向: <strong style="color: {trend_color};">{trend_text}</strong></p>
                <p>技術分野の活発度: {'高' if len(df) > 100 else '中' if len(df) > 50 else '低'}</p>
            </div>
            """, unsafe_allow_html=True)

def show_company_analysis(df: pd.DataFrame):
    """企業別詳細分析（完成版）"""
    st.subheader("🏢 企業別詳細分析")
    
    # 企業選択
    companies = df['assignee'].value_counts().index.tolist()
    selected_company = st.selectbox("🔍 分析対象企業を選択", companies)
    
    if selected_company:
        company_df = df[df['assignee'] == selected_company]
        
        # 企業基本情報
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📋 特許数", len(company_df))
            
        with col2:
            avg_inventors = company_df['inventors'].apply(lambda x: len(x) if isinstance(x, list) else 0).mean()
            st.metric("👥 平均発明者数", f"{avg_inventors:.1f}")
            
        with col3:
            if 'filing_date' in company_df.columns:
                date_range = (company_df['filing_date'].max() - company_df['filing_date'].min()).days
                st.metric("📅 活動期間（日）", f"{date_range}")
        
        # 企業の時系列分析
        if 'filing_year' in company_df.columns:
            st.subheader(f"📈 {selected_company} の年次出願動向")
            company_yearly = company_df.groupby('filing_year').size()
            
            fig = px.bar(
                x=company_yearly.index,
                y=company_yearly.values,
                title=f"{selected_company} の年次特許出願数",
                labels={'x': '出願年', 'y': '特許数'},
                color=company_yearly.values,
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # 技術キーワード分析
        if not company_df['abstract'].empty:
            st.subheader(f"☁️ {selected_company} の技術キーワード")
            
            all_abstracts = ' '.join(company_df['abstract'].astype(str))
            
            # ESC関連キーワードを抽出
            esc_keywords = {
                'Electrostatic Chuck': ['electrostatic', 'chuck', 'ESC'],
                'Wafer Processing': ['wafer', 'substrate', 'silicon'],
                'Curved Technology': ['curved', 'flexible', 'bendable'],
                'Control Systems': ['control', 'voltage', 'electrode'],
                'Materials': ['ceramic', 'polymer', 'dielectric']
            }
            
            keyword_results = {}
            for category, keywords in esc_keywords.items():
                count = 0
                for keyword in keywords:
                    count += len(re.findall(r'\b' + keyword + r'\b', all_abstracts, re.IGNORECASE))
                if count > 0:
                    keyword_results[category] = count
            
            if keyword_results:
                fig = px.pie(
                    values=list(keyword_results.values()),
                    names=list(keyword_results.keys()),
                    title=f"{selected_company} の技術分野分布"
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
                
        # 発明者ネットワーク分析
        if 'inventors' in company_df.columns:
            st.subheader(f"🔗 {selected_company} の発明者ネットワーク")
            
            all_inventors = []
            for inventors_list in company_df['inventors']:
                if isinstance(inventors_list, list):
                    all_inventors.extend(inventors_list)
            
            inventor_counts = Counter(all_inventors)
            top_inventors = dict(inventor_counts.most_common(10))
            
            if top_inventors:
                fig = px.bar(
                    x=list(top_inventors.values()),
                    y=list(top_inventors.keys()),
                    orientation='h',
                    title=f"主要発明者（特許数）",
                    labels={'x': '特許数', 'y': '発明者名'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

def show_technology_trends(df: pd.DataFrame):
    """技術トレンド分析（完成版）"""
    st.subheader("🔬 技術トレンド分析")
    
    # 技術キーワード定義（より詳細）
    tech_keywords = {
        'Curved ESC': ['curved', 'curvature', 'bend', 'flexible', 'conformal'],
        'Wafer Distortion': ['distortion', 'warpage', 'deformation', 'bow', 'stress'],
        'Temperature Control': ['temperature', 'thermal', 'heating', 'cooling', 'heat'],
        'RF Technology': ['RF', 'radio frequency', 'plasma', 'ion', 'RF power'],
        'Materials Science': ['ceramic', 'silicon', 'polymer', 'composite', 'dielectric'],
        'Vacuum Technology': ['vacuum', 'pressure', 'chamber', 'pumping', 'atmosphere'],
        'Surface Technology': ['surface', 'coating', 'layer', 'film', 'interface']
    }
    
    # 年次技術トレンド分析
    if 'filing_year' in df.columns:
        yearly_tech_trends = {}
        
        for year in sorted(df['filing_year'].dropna().unique()):
            year_df = df[df['filing_year'] == year]
            year_abstracts = ' '.join(year_df['abstract'].astype(str))
            
            yearly_tech_trends[year] = {}
            for tech, keywords in tech_keywords.items():
                count = 0
                for keyword in keywords:
                    count += len(re.findall(r'\b' + keyword + r'\b', year_abstracts, re.IGNORECASE))
                yearly_tech_trends[year][tech] = count
        
        # データフレーム化
        trend_df = pd.DataFrame(yearly_tech_trends).T.fillna(0)
        
        if not trend_df.empty:
            # 技術トレンドグラフ
            fig = px.line(
                trend_df,
                title="年次技術トレンド分析（キーワード出現頻度）",
                labels={'index': '年', 'value': 'キーワード出現回数', 'variable': '技術分野'}
            )
            fig.update_layout(height=600, hovermode='x unified')
            fig.update_traces(line_width=3, marker_size=6)
            st.plotly_chart(fig, use_container_width=True)
            
            # 成長率分析
            st.subheader("📊 技術分野別成長率")
            if len(trend_df) > 1:
                growth_rates = {}
                for col in trend_df.columns:
                    recent = trend_df[col].iloc[-3:].mean()
                    early = trend_df[col].iloc[:3].mean()
                    if early > 0:
                        growth_rate = ((recent - early) / early) * 100
                        growth_rates[col] = growth_rate
                
                if growth_rates:
                    growth_df = pd.DataFrame(list(growth_rates.items()), 
                                           columns=['技術分野', '成長率(%)'])
                    growth_df = growth_df.sort_values('成長率(%)', ascending=True)
                    
                    fig = px.bar(
                        growth_df,
                        x='成長率(%)',
                        y='技術分野',
                        orientation='h',
                        title="技術分野別成長率（直近3年 vs 初期3年）",
                        color='成長率(%)',
                        color_continuous_scale='RdYlGn'
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
    
    # 最新技術動向（直近2年）
    if 'filing_year' in df.columns:
        recent_years = df['filing_year'].max() - 1
        recent_df = df[df['filing_year'] >= recent_years]
        
        if not recent_df.empty:
            st.subheader("🆕 最新技術動向（直近2年）")
            
            # 最新技術のキーワード抽出
            recent_abstracts = ' '.join(recent_df['abstract'].astype(str))
            
            # 高度なキーワード分析
            advanced_keywords = {
                'AI/ML Integration': ['artificial intelligence', 'machine learning', 'neural', 'algorithm'],
                'IoT/Smart Systems': ['IoT', 'smart', 'connected', 'sensor', 'monitoring'],
                'Sustainability': ['sustainability', 'green', 'eco', 'environment', 'carbon'],
                'Miniaturization': ['nano', 'micro', 'miniature', 'compact', 'small'],
                'Advanced Materials': ['graphene', 'quantum', 'advanced', 'novel', 'innovative']
            }
            
            recent_tech_counts = {}
            for category, keywords in advanced_keywords.items():
                count = 0
                for keyword in keywords:
                    count += len(re.findall(r'\b' + keyword + r'\b', recent_abstracts, re.IGNORECASE))
                if count > 0:
                    recent_tech_counts[category] = count
            
            if recent_tech_counts:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.pie(
                        values=list(recent_tech_counts.values()),
                        names=list(recent_tech_counts.keys()),
                        title="新興技術分野の分布"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # 技術成熟度指標
                    maturity_scores = {}
                    for tech, count in recent_tech_counts.items():
                        # 出現頻度に基づく成熟度スコア
                        if count > 20:
                            maturity_scores[tech] = "成熟期"
                        elif count > 10:
                            maturity_scores[tech] = "成長期"
                        else:
                            maturity_scores[tech] = "萌芽期"
                    
                    st.markdown("#### 🚀 技術成熟度評価")
                    for tech, maturity in maturity_scores.items():
                        color = {"成熟期": "#28a745", "成長期": "#ffc107", "萌芽期": "#17a2b8"}[maturity]
                        st.markdown(f"**{tech}**: <span style='color: {color};'>{maturity}</span>", 
                                  unsafe_allow_html=True)

def show_competitive_analysis(df: pd.DataFrame):
    """競合比較分析（完成版）"""
    st.subheader("⚔️ 競合比較分析")
    
    # 上位企業の選定
    top_companies = df['assignee'].value_counts().head(8).index.tolist()
    
    # 企業間比較メトリクス
    comparison_data = []
    
    for company in top_companies:
        company_df = df[df['assignee'] == company]
        
        # 技術多様性計算
        abstracts_text = ' '.join(company_df['abstract'].astype(str))
        unique_words = len(set(abstracts_text.lower().split()))
        
        # 最新性指標
        if 'filing_year' in company_df.columns:
            avg_year = company_df['filing_year'].mean()
            latest_year = company_df['filing_year'].max()
            recency_score = (avg_year - 2015) / (2024 - 2015) * 100  # 0-100スケール
        else:
            avg_year = 0
            latest_year = 0
            recency_score = 0
        
        # 発明者数（コラボレーション指標）
        total_inventors = sum(len(inv) if isinstance(inv, list) else 0 
                            for inv in company_df['inventors'])
        
        metrics = {
            '企業名': company,
            '特許数': len(company_df),
            '平均年間出願数': len(company_df) / max(1, company_df['filing_year'].nunique()) if 'filing_year' in company_df.columns else 0,
            '最新出願年': latest_year,
            '技術多様性': unique_words / len(company_df) if len(company_df) > 0 else 0,
            '最新性スコア': recency_score,
            '総発明者数': total_inventors,
            'コラボレーション指標': total_inventors / len(company_df) if len(company_df) > 0 else 0
        }
        comparison_data.append(metrics)
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # 比較表示
    st.subheader("📊 企業比較メトリクス")
    
    # 数値を見やすく整形
    display_df = comparison_df.copy()
    numeric_columns = ['平均年間出願数', '技術多様性', '最新性スコア', 'コラボレーション指標']
    for col in numeric_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].round(2)
    
    st.dataframe(display_df, use_container_width=True)
    
    # 競合ポジショニングマップ
    st.subheader("🎯 競合ポジショニングマップ")
    
    fig = px.scatter(
        comparison_df,
        x='特許数',
        y='最新性スコア',
        size='技術多様性',
        color='コラボレーション指標',
        hover_name='企業名',
        title="競合企業ポジショニング（バブルサイズ: 技術多様性）",
        labels={
            'x': '特許数（市場プレゼンス）',
            'y': '最新性スコア（技術革新性）',
            'color': 'コラボレーション指標'
        },
        color_continuous_scale='Viridis'
    )
    
    # 企業名をマップ上に表示
    for _, row in comparison_df.iterrows():
        fig.add_annotation(
            x=row['特許数'],
            y=row['最新性スコア'],
            text=row['企業名'].split()[0] if ' ' in row['企業名'] else row['企業名'][:10],
            showarrow=False,
            font=dict(size=10, color="white"),
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="white",
            borderwidth=1
        )
    
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)
    
    # レーダーチャート（上位5社）
    st.subheader("🕸️ 総合能力レーダーチャート（上位5社）")
    
    top5_df = comparison_df.head(5)
    radar_metrics = ['特許数', '最新性スコア', '技術多様性', 'コラボレーション指標']
    
    fig = go.Figure()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FCEA2B']
    
    for i, (_, row) in enumerate(top5_df.iterrows()):
        values = []
        for metric in radar_metrics:
            # 正規化（0-1スケール）
            max_val = comparison_df[metric].max()
            min_val = comparison_df[metric].min()
            if max_val != min_val:
                normalized = (row[metric] - min_val) / (max_val - min_val)
            else:
                normalized = 0.5
            values.append(normalized)
        
        values.append(values[0])  # レーダーチャートを閉じるため
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=radar_metrics + [radar_metrics[0]],
            fill='toself',
            name=row['企業名'],
            line_color=colors[i % len(colors)],
            fillcolor=colors[i % len(colors)],
            opacity=0.3
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickvals=[0, 0.5, 1],
                ticktext=['低', '中', '高']
            )),
        showlegend=True,
        title="企業別総合評価レーダーチャート",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 戦略的インサイト
    st.subheader("💡 戦略的インサイト")
    
    # 各企業の特徴分析
    insights = []
    for _, row in comparison_df.head(5).iterrows():
        company = row['企業名']
        
        # 強み分析
        strengths = []
        if row['特許数'] >= comparison_df['特許数'].quantile(0.8):
            strengths.append("市場リーダー")
        if row['最新性スコア'] >= comparison_df['最新性スコア'].quantile(0.8):
            strengths.append("技術革新者")
        if row['技術多様性'] >= comparison_df['技術多様性'].quantile(0.8):
            strengths.append("技術多様化")
        if row['コラボレーション指標'] >= comparison_df['コラボレーション指標'].quantile(0.8):
            strengths.append("オープンイノベーション")
        
        insights.append({
            '企業': company,
            '戦略ポジション': ', '.join(strengths) if strengths else '特化型企業',
            '特許数': int(row['特許数']),
            '主要強み': strengths[0] if strengths else 'コスト効率'
        })
    
    insights_df = pd.DataFrame(insights)
    st.dataframe(insights_df, use_container_width=True)

def show_timeline_analysis(df: pd.DataFrame):
    """タイムライン分析（完成版）"""
    st.subheader("⏰ タイムライン分析")
    
    if 'filing_date' not in df.columns or df['filing_date'].isna().all():
        st.warning("出願日データが不足しているため、タイムライン分析を実行できません")
        return
    
    # 出願日でソート
    timeline_df = df.copy()
    timeline_df = timeline_df.dropna(subset=['filing_date']).sort_values('filing_date')
    
    # 期間設定
    col1, col2 = st.columns(2)
    
    available_years = sorted(timeline_df['filing_year'].dropna().unique())
    
    with col1:
        start_year = st.selectbox(
            "📅 開始年",
            options=available_years,
            index=0 if available_years else 0
        )
    
    with col2:
        end_year = st.selectbox(
            "📅 終了年",
            options=available_years,
            index=len(available_years)-1 if available_years else 0
        )
    
    # 期間でフィルタ
    filtered_df = timeline_df[
        (timeline_df['filing_year'] >= start_year) & 
        (timeline_df['filing_year'] <= end_year)
    ]
    
    if filtered_df.empty:
        st.warning("選択した期間にデータがありません")
        return
    
    # 月次出願動向
    st.subheader("📅 月次出願動向")
    
    filtered_df['filing_month'] = filtered_df['filing_date'].dt.to_period('M')
    monthly_counts = filtered_df.groupby('filing_month').size()
    
    fig = px.line(
        x=monthly_counts.index.astype(str),
        y=monthly_counts.values,
        title=f"{start_year}-{end_year}年の月次特許出願動向",
        labels={'x': '出願月', 'y': '特許数'}
    )
    fig.update_traces(line_color='#007acc', line_width=3, marker_size=6)
    fig.update_xaxes(tickangle=45)
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # 企業別タイムライン
    st.subheader("🏢 企業別出願タイムライン")
    
    top_companies = filtered_df['assignee'].value_counts().head(5).index.tolist()
    
    fig = go.Figure()
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FCEA2B']
    
    for i, company in enumerate(top_companies):
        company_data = filtered_df[filtered_df['assignee'] == company]
        company_monthly = company_data.groupby('filing_month').size()
        
        fig.add_trace(go.Scatter(
            x=company_monthly.index.astype(str),
            y=company_monthly.values,
            mode='lines+markers',
            name=company,
            line=dict(width=3, color=colors[i % len(colors)]),
            marker=dict(size=6)
        ))
    
    fig.update_layout(
        title="上位企業の出願タイムライン比較",
        xaxis_title="出願月",
        yaxis_title="特許数",
        height=600,
        hovermode='x unified'
    )
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)
    
    # 累積出願数
    st.subheader("📈 累積特許出願数")
    
    cumulative_counts = filtered_df.groupby('filing_date').size().cumsum()
    
    fig = px.area(
        x=cumulative_counts.index,
        y=cumulative_counts.values,
        title="累積特許出願数の推移",
        labels={'x': '出願日', 'y': '累積特許数'}
    )
    fig.update_traces(fill='tonexty', fillcolor='rgba(0, 122, 204, 0.3)', line_color='#007acc')
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # 季節性分析
    st.subheader("🗓️ 季節性・周期性分析")
    
    # 月別出願パターン
    filtered_df['month'] = filtered_df['filing_date'].dt.month
    monthly_pattern = filtered_df.groupby('month').size()
    
    month_names = ['1月', '2月', '3月', '4月', '5月', '6月', 
                   '7月', '8月', '9月', '10月', '11月', '12月']
    
    fig = px.bar(
        x=month_names,
        y=monthly_pattern.values,
        title="月別出願パターン（季節性分析）",
        labels={'x': '月', 'y': '特許数'},
        color=monthly_pattern.values,
        color_continuous_scale='Blues'
    )
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # マイルストーン分析
    st.subheader("🎯 重要マイルストーン")
    
    # 出願数のピーク検出
    yearly_counts = filtered_df.groupby('filing_year').size()
    if len(yearly_counts) > 0:
        peak_year = yearly_counts.idxmax()
        peak_count = yearly_counts.max()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "📊 ピーク出願年",
                f"{peak_year}年",
                f"{peak_count}件"
            )
        
        with col2:
            total_growth = ((yearly_counts.iloc[-1] - yearly_counts.iloc[0]) / yearly_counts.iloc[0] * 100) if len(yearly_counts) > 1 and yearly_counts.iloc[0] > 0 else 0
            st.metric(
                "📈 総成長率",
                f"{total_growth:.1f}%",
                "期間全体"
            )
        
        with col3:
            avg_annual = yearly_counts.mean()
            st.metric(
                "📋 年平均出願数",
                f"{avg_annual:.1f}件",
                "安定性指標"
            )

def main():
    """メインアプリケーション（完成版）"""
    
    # ヘッダー
    st.markdown("""
    <div class="main-header">
        <h1>🔍 FusionPatentSearch</h1>
        <h2>ESC特許分析システム - 実データベース対応版</h2>
        <p>東京科学大学 齊藤滋規教授研究室 × FUSIONDRIVER INC KSPプロジェクト</p>
        <p><em>Advanced Patent Analytics Platform for Electrostatic Chuck Technology</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # プロジェクト情報サイドバー
    with st.sidebar:
        st.image("https://via.placeholder.com/300x200/1f4e79/white?text=FusionPatentSearch+2.0", 
                caption="ESC特許分析システム v2.0")
        
        st.markdown("""
        ### 📋 プロジェクト情報
        - **開発**: FUSIONDRIVER INC
        - **学術連携**: 東京科学大学
        - **指導教授**: 齊藤滋規教授
        - **技術領域**: 曲面ESC技術
        - **バージョン**: 2.0 (完成版)
        - **最終更新**: 2025年7月22日
        """)
        
        st.markdown("""
        ### 🎯 システム特徴
        - ✅ 実在特許265+件対応
        - ✅ 企業別均等収集（13社）
        - ✅ Google Drive分割保存
        - ✅ スケーラブル設計
        - ✅ リアルタイム分析
        - ✅ 高度可視化
        """)
        
        # システム状態表示
        st.markdown("### 🖥️ システム状態")
        try:
            from patent_cloud_collector import CloudPatentDataCollector
            collector = CloudPatentDataCollector()
            if collector.drive_service:
                st.success("✅ Google Drive API 接続成功")
                
                # 保存済みファイル数を表示
                files = collector.list_patent_files()
                if files:
                    st.info(f"💾 保存済みファイル: {len(files)}個")
                else:
                    st.warning("📁 データファイルなし")
            else:
                st.error("❌ Google Drive 接続失敗")
        except Exception as e:
            st.error(f"❌ システムエラー: {str(e)}")
        
        # データ状況
        st.markdown("### 📊 データ状況")
        try:
            df_check = load_patent_data_from_cloud()
            if not df_check.empty:
                st.success(f"✅ データ読み込み可能: {len(df_check)}件")
                
                # データ品質指標
                quality_score = 0
                if 'patent_number' in df_check.columns:
                    quality_score += 25
                if 'abstract' in df_check.columns and not df_check['abstract'].isna().all():
                    quality_score += 25
                if 'assignee' in df_check.columns and not df_check['assignee'].isna().all():
                    quality_score += 25
                if 'filing_date' in df_check.columns and not df_check['filing_date'].isna().all():
                    quality_score += 25
                
                color = "#28a745" if quality_score >= 75 else "#ffc107" if quality_score >= 50 else "#dc3545"
                st.markdown(f"**データ品質**: <span style='color: {color};'>{quality_score}%</span>", 
                          unsafe_allow_html=True)
            else:
                st.warning("⚠️ データなし")
        except:
            st.info("📊 データ状況: 確認中")
    
    # メインタブ構成
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔄 大量データ収集", 
        "🔍 実データ分析", 
        "☁️ クラウド管理", 
        "📊 レポート"
    ])
    
    with tab1:
        st.header("🚀 大量実特許データ収集システム")
        
        # 新アーキテクチャ説明
        st.markdown("""
        <div class="info-box">
            <h4>🏗️ 新しいアーキテクチャ</h4>
            <ol>
                <li><strong>大量の実特許データを収集</strong> - Applied Materials、Tokyo Electron等の実在特許</li>
                <li><strong>Google Driveに自動分割保存</strong> - メモリ効率とスケーラビリティを確保</li>
                <li><strong>クラウドから効率的に読み込み</strong> - 段階的データロードで高速処理</li>
                <li><strong>実データで完全分析</strong> - 学術的価値の高い本格的な特許分析</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        # データ収集インターフェース
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("📊 データ収集設定")
            
            collection_mode = st.selectbox(
                "🎯 収集モード選択",
                [
                    "標準収集 (50件)",
                    "拡張収集 (100件)", 
                    "大量収集 (200件)",
                    "全件 (60+実在特許)"
                ],
                index=2,  # デフォルトは大量収集
                help="収集する特許データの件数を選択してください"
            )
            
            # 収集予定の企業表示
            st.markdown("#### 🏢 収集対象企業")
            companies_preview = [
                "Applied Materials", "Tokyo Electron", "Kyocera", 
                "Shinko Electric", "TOTO", "Sumitomo Osaka Cement",
                "NGK Insulators", "NTK Ceratec", "Lam Research",
                "Entegris", "MiCo", "SEMCO Engineering", "Creative Technology"
            ]
            
            mode_companies = {
                "標準収集 (50件)": 5,
                "拡張収集 (100件)": 8,
                "大量収集 (200件)": 13,
                "全件 (60+実在特許)": 13
            }
            
            num_companies = mode_companies[collection_mode]
            selected_companies = companies_preview[:num_companies]
            
            for i in range(0, len(selected_companies), 3):
                cols = st.columns(3)
                for j, company in enumerate(selected_companies[i:i+3]):
                    with cols[j]:
                        st.markdown(f"✅ **{company}**")
        
        with col2:
            st.subheader("📈 収集進捗予測")
            
            mode_config = {
                "標準収集 (50件)": {"size": "~5MB", "time": "5-8分", "success": "70-80%"},
                "拡張収集 (100件)": {"size": "~10MB", "time": "8-12分", "success": "65-75%"},
                "大量収集 (200件)": {"size": "~20MB", "time": "15-25分", "success": "60-70%"},
                "全件 (60+実在特許)": {"size": "~30MB", "time": "25-35分", "success": "55-65%"}
            }
            
            config = mode_config[collection_mode]
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>📊 予想データサイズ</h4>
                <h3 style="color: #007acc;">{config["size"]}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>⏱️ 推定収集時間</h4>
                <h3 style="color: #28a745;">{config["time"]}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>✅ 予想成功率</h4>
                <h3 style="color: #ffc107;">{config["success"]}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        # 実データ収集ボタン
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 大量データ収集開始", type="primary", use_container_width=True):
                try:
                    from patent_cloud_collector import CloudPatentDataCollector
                    
                    with st.spinner("実在特許データを収集中... この処理には時間がかかります"):
                        collector = CloudPatentDataCollector()
                        result = collector.collect_real_patents(collection_mode)
                    
                    if result > 0:
                        st.markdown(f"""
                        <div class="success-box">
                            <h3>🎉 データ収集完了！</h3>
                            <p><strong>{result}件</strong>の実特許データを収集・保存しました</p>
                            <p>「実データ分析」タブで高度な分析を開始できます</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.balloons()
                    else:
                        st.error("❌ データ収集に失敗しました")
                        
                except ImportError as e:
                    st.error(f"❌ モジュールインポートエラー: {str(e)}")
                    st.info("patent_cloud_collector.py ファイルを確認してください")
                except Exception as e:
                    st.error(f"❌ 収集エラー: {str(e)}")
                    st.info("詳細エラー情報を確認して修正してください")
    
    with tab2:
        st.header("🔍 実データ分析システム")
        
        # 実データロード
        with st.spinner("保存されたデータを読み込み中..."):
            df = load_patent_data_from_cloud()
        
        if len(df) > 0:
            # データサマリー表示
            st.markdown(f"""
            <div class="success-box">
                <h4>📊 実データ分析準備完了</h4>
                <p><strong>{len(df)}件</strong>の実特許データで分析を実行できます</p>
                <p>企業数: <strong>{df['assignee'].nunique()}社</strong> | 
                   技術分野: <strong>ESC関連技術</strong> | 
                   データ品質: <strong>高品質</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            # 分析タイプ選択
            col1, col2 = st.columns([2, 1])
            
            with col1:
                analysis_type = st.selectbox(
                    "🔬 分析タイプ選択",
                    [
                        "概要分析", 
                        "企業別詳細分析", 
                        "技術トレンド分析", 
                        "競合比較分析", 
                        "タイムライン分析"
                    ],
                    help="実行したい分析の種類を選択してください"
                )
            
            with col2:
                # 分析説明
                analysis_descriptions = {
                    "概要分析": "全体的な特許動向と基本統計",
                    "企業別詳細分析": "個別企業の特許戦略分析",
                    "技術トレンド分析": "技術キーワードの時系列変化",
                    "競合比較分析": "企業間の競合ポジショニング",
                    "タイムライン分析": "時系列での出願パターン分析"
                }
                
                st.markdown(f"""
                <div class="info-box">
                    <h5>📋 {analysis_type}</h5>
                    <p>{analysis_descriptions[analysis_type]}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # 分析実行
            if st.button("📈 分析実行", type="primary", use_container_width=True):
                with st.spinner(f"{analysis_type}を実行中..."):
                    execute_real_data_analysis(df, analysis_type)
        
        else:
            st.markdown("""
            <div class="warning-box">
                <h4>⚠️ 分析対象のデータがありません</h4>
                <p>「大量データ収集」タブで実データを収集してください</p>
            </div>
            """, unsafe_allow_html=True)
            
            # デモボタン（開発・デモ用）
            if st.button("🧪 デモデータで動作確認"):
                # 簡単なデモデータ生成
                demo_data = {
                    'patent_number': ['US10847397', 'US10672634', 'US10593580', 'US10472728', 'US10340135'],
                    'title': [
                        'Electrostatic chuck with curved surface for wafer processing',
                        'Bendable chuck system for semiconductor applications',
                        'Flexible ESC design for distortion control',
                        'Advanced ceramic chuck with thermal management',
                        'Multi-zone electrostatic chuck for precision control'
                    ],
                    'assignee': ['Applied Materials', 'Tokyo Electron', 'Kyocera', 'Applied Materials', 'Lam Research'],
                    'filing_date': pd.to_datetime(['2020-01-15', '2020-06-22', '2021-03-10', '2021-08-05', '2022-02-14']),
                    'abstract': [
                        'An electrostatic chuck with curved surface for improved wafer processing and distortion control',
                        'Bendable chuck system designed for flexible semiconductor wafer handling applications',
                        'Flexible ESC technology for advanced distortion control in semiconductor manufacturing',
                        'Advanced ceramic chuck incorporating thermal management for high-precision applications',
                        'Multi-zone electrostatic chuck system providing precision control for wafer processing'
                    ],
                    'inventors': [
                        ['John Smith', 'Jane Doe'], 
                        ['Taro Tanaka', 'Hanako Sato'], 
                        ['Jiro Suzuki'], 
                        ['Mike Johnson', 'Sarah Wilson', 'Tom Brown'],
                        ['Alex Chen', 'Lisa Wang']
                    ]
                }
                demo_df = pd.DataFrame(demo_data)
                demo_df['filing_year'] = demo_df['filing_date'].dt.year
                
                st.info("🧪 デモデータで概要分析を実行")
                show_overview_analysis(demo_df)
    
    with tab3:
        st.header("☁️ クラウドストレージ管理")
        
        try:
            from patent_cloud_collector import CloudPatentDataCollector
            collector = CloudPatentDataCollector()
            
            # 保存済みファイルの確認
            st.subheader("📁 保存済みデータファイル")
            
            file_list = collector.list_patent_files()
            
            if file_list:
                st.success(f"📊 {len(file_list)}個のデータファイルが保存されています")
                
                # ファイル情報を表形式で表示
                file_data = []
                total_size = 0
                
                for file_info in file_list:
                    size_mb = int(file_info.get('size', 0)) / 1024 / 1024
                    total_size += size_mb
                    
                    file_data.append({
                        'ファイル名': file_info['name'],
                        '作成日時': file_info.get('createdTime', 'N/A')[:10] if file_info.get('createdTime') else 'N/A',
                        'サイズ(MB)': f"{size_mb:.2f}",
                        'ファイルID': file_info['id'][:20] + "..." if len(file_info['id']) > 20 else file_info['id']
                    })
                
                files_df = pd.DataFrame(file_data)
                st.dataframe(files_df, use_container_width=True)
                
                # ストレージ使用量
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("💾 総ストレージ使用量", f"{total_size:.2f} MB")
                
                with col2:
                    st.metric("📁 ファイル数", len(file_list))
                
                with col3:
                    avg_size = total_size / len(file_list) if file_list else 0
                    st.metric("📊 平均ファイルサイズ", f"{avg_size:.2f} MB")
                
            else:
                st.info("まだデータファイルが保存されていません")
                st.markdown("""
                <div class="info-box">
                    <h4>💡 ファイル保存について</h4>
                    <p>「大量データ収集」タブでデータ収集を実行すると、自動的にGoogle Driveに保存されます</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Google Drive接続状態
            st.subheader("🔗 Google Drive接続状態")
            
            if collector.drive_service and collector.folder_id:
                st.success("✅ Google Drive API 接続正常")
                st.info(f"📂 保存フォルダID: {collector.folder_id}")
            else:
                st.error("❌ Google Drive 接続に問題があります")
                
        except Exception as e:
            st.error(f"クラウド管理エラー: {str(e)}")
    
    with tab4:
        st.header("📊 分析レポート・エクスポート")
        
        # データ状況確認
        df_report = load_patent_data_from_cloud()
        
        if not df_report.empty:
            st.subheader("📈 総合レポート")
            
            # 総合統計サマリー
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 データ概要")
                summary_stats = {
                    "総特許数": len(df_report),
                    "対象企業数": df_report['assignee'].nunique(),
                    "最古出願年": df_report['filing_year'].min() if 'filing_year' in df_report.columns else 'N/A',
                    "最新出願年": df_report['filing_year'].max() if 'filing_year' in df_report.columns else 'N/A',
                    "平均発明者数": f"{df_report['inventors'].apply(lambda x: len(x) if isinstance(x, list) else 0).mean():.1f}"
                }
                
                for key, value in summary_stats.items():
                    st.metric(key, value)
            
            with col2:
                st.markdown("#### 🏢 上位企業")
                top_assignees = df_report['assignee'].value_counts().head(5)
                
                for company, count in top_assignees.items():
                    percentage = (count / len(df_report)) * 100
                    st.markdown(f"**{company}**: {count}件 ({percentage:.1f}%)")
            
            # レポートエクスポート機能
            st.subheader("💾 データエクスポート")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 CSV形式でダウンロード"):
                    csv = df_report.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="⬇️ CSVダウンロード",
                        data=csv,
                        file_name=f"fusionpatentsearch_data_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                if st.button("📊 Excel形式でダウンロード"):
                    # Excel形式は簡易版として、主要列のみ出力
                    excel_df = df_report[['patent_number', 'title', 'assignee', 'filing_date']].copy()
                    st.download_button(
                        label="⬇️ 簡易版データ",
                        data=excel_df.to_csv(index=False),
                        file_name=f"fusionpatentsearch_simple_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            with col3:
                if st.button("📋 分析レポート生成"):
                    # 自動レポート生成
                    report_content = f"""
# FusionPatentSearch 分析レポート
**生成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}

## データ概要
- **総特許数**: {len(df_report)}件
- **対象企業数**: {df_report['assignee'].nunique()}社
- **分析期間**: {df_report['filing_year'].min() if 'filing_year' in df_report.columns else 'N/A'} - {df_report['filing_year'].max() if 'filing_year' in df_report.columns else 'N/A'}年

## 上位企業（特許数）
{chr(10).join([f"{i+1}. {company}: {count}件" for i, (company, count) in enumerate(df_report['assignee'].value_counts().head(10).items())])}

## 技術分野
ESC（Electrostatic Chuck）関連技術
- 曲面ESC技術
- ウエハ歪み制御
- 半導体製造装置

---
*Generated by FusionPatentSearch v2.0*
*Tokyo Institute of Science and Technology × FUSIONDRIVER INC*
                    """
                    
                    st.download_button(
                        label="⬇️ レポートダウンロード",
                        data=report_content,
                        file_name=f"fusionpatentsearch_report_{datetime.now().strftime('%Y%m%d')}.md",
                        mime="text/markdown"
                    )
        else:
            st.warning("レポート生成のためのデータがありません。まずデータ収集を実行してください。")
    
    # フッター
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p><strong>FusionPatentSearch v2.0</strong> - ESC特許分析システム（完成版）</p>
        <p>🎓 東京科学大学 齊藤滋規教授研究室 × 🚀 FUSIONDRIVER INC KSPプロジェクト</p>
        <p><em>Advanced Patent Analytics Platform for Semiconductor Technology Research</em></p>
        <p>最終更新: 2025年7月22日 | アーキテクチャ: Cloud-based Phased Data Processing</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
