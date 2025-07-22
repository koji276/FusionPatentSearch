 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ターゲット企業専用ESC特許分析モジュール
指定企業の詳細分析とベンチマーキング

使用方法:
python target_company_analyzer.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

# 日本語フォント設定
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif']

class TargetCompanyAnalyzer:
    def __init__(self, patent_data_file='curved_esc_patents.csv'):
        """特許データの読み込み"""
        try:
            self.df = pd.read_csv(patent_data_file, encoding='utf-8-sig')
            print(f"✓ {len(self.df)}件の特許データを読み込みました")
        except FileNotFoundError:
            print("❌ 特許データファイルが見つかりません。先にcurved_esc_analyzer.pyを実行してください。")
            exit(1)
        
        # ターゲット企業リスト定義
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
        
        # 全ターゲット企業のフラットリスト
        self.all_targets = list(self.target_companies['Japanese'].keys()) + \
                          list(self.target_companies['International'].keys())
    
    def analyze_target_company_presence(self):
        """ターゲット企業の特許出願状況分析"""
        print("\n🎯 ターゲット企業分析を開始...")
        
        # ターゲット企業の特許抽出
        target_patents = self.df[self.df['normalized_assignee'].isin(self.all_targets)]
        
        if len(target_patents) == 0:
            print("⚠️ ターゲット企業の特許が見つかりませんでした")
            print("企業名マッピングを確認してください")
            return pd.DataFrame()
        
        print(f"✓ ターゲット企業の特許: {len(target_patents)}件")
        print(f"全体に占める割合: {len(target_patents)/len(self.df)*100:.1f}%")
        
        # 企業別統計
        company_stats = target_patents['normalized_assignee'].value_counts()
        
        print(f"\n📊 ターゲット企業別出願件数:")
        for company, count in company_stats.items():
            japanese_name = self.target_companies['Japanese'].get(company) or \
                          self.target_companies['International'].get(company, company)
            print(f"   {company:20s} ({japanese_name}): {count:3d}件")
        
        return target_patents
    
    def competitive_positioning_analysis(self, target_patents):
        """競合ポジショニング分析"""
        print("\n⚔️ 競合ポジショニング分析...")
        
        # 年度データ準備
        target_patents['filing_year'] = pd.to_datetime(target_patents['filing_date']).dt.year
        
        # 企業別年次推移
        yearly_company_data = target_patents.pivot_table(
            index='filing_year', 
            columns='normalized_assignee', 
            values='publication_number',
            aggfunc='count',
            fill_value=0
        )
        
        print("📈 年次推移分析 (2020-2024):")
        recent_years = yearly_company_data.loc[2020:2024] if 2020 in yearly_company_data.index else yearly_company_data
        
        for company in self.all_targets:
            if company in recent_years.columns:
                recent_total = recent_years[company].sum()
                if recent_total > 0:
                    trend = "📈" if recent_years[company].iloc[-1] > recent_years[company].iloc[0] else "📉"
                    print(f"   {company:20s}: {recent_total:2d}件 {trend}")
        
        return yearly_company_data
    
    def technology_focus_analysis(self, target_patents):
        """技術注力分野分析"""
        print("\n🔬 技術注力分野分析...")
        
        # 技術キーワード定義
        tech_keywords = {
            'Temperature Control': ['temperature', 'thermal', 'heating', 'cooling', '温度', '加熱'],
            'Curved/Flexible': ['curved', 'flexible', 'bendable', 'conformal', '曲面', '湾曲', '可撓'],
            'Material/Ceramic': ['ceramic', 'dielectric', 'material', 'coating', 'セラミック', '誘電体'],
            'Process Control': ['plasma', 'etching', 'deposition', 'process', 'プラズマ', 'エッチング'],
            'Sensor/Monitor': ['sensor', 'monitoring', 'detection', 'measurement', 'センサ', '監視'],
            'Mechanical': ['clamp', 'chuck', 'electrode', 'structure', 'チャック', '電極']
        }
        
        # 企業別技術分野スコア
        company_tech_scores = defaultdict(lambda: defaultdict(int))
        
        for _, patent in target_patents.iterrows():
            company = patent['normalized_assignee']
            text = str(patent['title']) + ' ' + str(patent['abstract'])
            text_lower = text.lower()
            
            for tech_area, keywords in tech_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        company_tech_scores[company][tech_area] += 1
                        break  # 1件につき1分野1回のみ
        
        # 結果表示
        print("🏆 企業別技術注力分野:")
        for company in self.all_targets:
            if company in company_tech_scores:
                scores = company_tech_scores[company]
                if sum(scores.values()) > 0:
                    top_tech = max(scores.items(), key=lambda x: x[1])
                    print(f"   {company:20s}: {top_tech[0]} ({top_tech[1]}件)")
        
        return company_tech_scores
    
    def innovation_timeline_analysis(self, target_patents):
        """イノベーション・タイムライン分析"""
        print("\n⏰ イノベーション・タイムライン分析...")
        
        # 重要特許の定義（外国出願ありまたは被引用多数）
        important_patents = target_patents[
            (target_patents['country_code'] != 'JP') |  # 海外出願
            (target_patents['publication_number'].str.len() > 10)  # 複雑な番号=重要特許の可能性
        ].copy()
        
        important_patents['filing_year'] = pd.to_datetime(important_patents['filing_date']).dt.year
        
        # 企業別重要特許タイムライン
        timeline_data = []
        for company in self.all_targets:
            company_patents = important_patents[important_patents['normalized_assignee'] == company]
            for _, patent in company_patents.iterrows():
                timeline_data.append({
                    'company': company,
                    'year': patent['filing_year'],
                    'title': patent['title'][:50] + '...' if len(str(patent['title'])) > 50 else patent['title'],
                    'country': patent['country_code']
                })
        
        timeline_df = pd.DataFrame(timeline_data)
        
        print("🌟 重要特許タイムライン (2020年以降):")
        recent_timeline = timeline_df[timeline_df['year'] >= 2020].sort_values('year')
        for _, row in recent_timeline.iterrows():
            print(f"   {row['year']} - {row['company']:15s}: {row['title']}")
        
        return timeline_df
    
    def market_strategy_analysis(self, target_patents):
        """市場戦略分析"""
        print("\n🌍 市場戦略分析...")
        
        # 国別出願分析
        country_analysis = target_patents.groupby(['normalized_assignee', 'country_code']).size().unstack(fill_value=0)
        
        # グローバル展開度の計算
        global_companies = []
        for company in self.all_targets:
            if company in country_analysis.index:
                countries = (country_analysis.loc[company] > 0).sum()
                total_patents = country_analysis.loc[company].sum()
                if total_patents > 0:
                    global_companies.append({
                        'company': company,
                        'countries': countries,
                        'total_patents': total_patents,
                        'global_ratio': countries / total_patents if total_patents > 0 else 0
                    })
        
        # グローバル展開度順でソート
        global_companies.sort(key=lambda x: x['countries'], reverse=True)
        
        print("🌐 グローバル展開度ランキング:")
        for i, company_data in enumerate(global_companies[:10], 1):
            company = company_data['company']
            countries = company_data['countries']
            patents = company_data['total_patents']
            print(f"   {i:2d}. {company:20s}: {countries}カ国, {patents}件")
        
        return country_analysis, global_companies
    
    def create_target_company_visualizations(self, target_patents, yearly_data, company_tech_scores, timeline_df):
        """ターゲット企業専用可視化"""
        print("\n🎨 ターゲット企業可視化を作成中...")
        
        fig = plt.figure(figsize=(20, 16))
        
        # 1. ターゲット企業別出願件数
        ax1 = plt.subplot(3, 3, 1)
        company_counts = target_patents['normalized_assignee'].value_counts().head(15)
        colors = plt.cm.Set3(np.linspace(0, 1, len(company_counts)))
        bars = ax1.barh(range(len(company_counts)), company_counts.values, color=colors)
        ax1.set_yticks(range(len(company_counts)))
        ax1.set_yticklabels([name[:15] + '...' if len(name) > 15 else name for name in company_counts.index])
        ax1.set_title('Target Companies - Patent Count', fontweight='bold', fontsize=12)
        ax1.set_xlabel('Number of Patents')
        
        # 2. 日本企業 vs 海外企業
        ax2 = plt.subplot(3, 3, 2)
        japanese_companies = set(self.target_companies['Japanese'].keys())
        target_patents['region'] = target_patents['normalized_assignee'].apply(
            lambda x: 'Japan' if x in japanese_companies else 'International'
        )
        region_data = target_patents['region'].value_counts()
        ax2.pie(region_data.values, labels=region_data.index, autopct='%1.1f%%', colors=['#ff9999', '#66b3ff'])
        ax2.set_title('Japan vs International Companies', fontweight='bold', fontsize=12)
        
        # 3. 年次推移（主要企業）
        ax3 = plt.subplot(3, 3, 3)
        top_companies = company_counts.head(8).index
        target_patents['filing_year'] = pd.to_datetime(target_patents['filing_date']).dt.year
        
        for i, company in enumerate(top_companies):
            yearly_data = target_patents[target_patents['normalized_assignee'] == company].groupby('filing_year').size()
            if len(yearly_data) > 0:
                ax3.plot(yearly_data.index, yearly_data.values, marker='o', label=company[:10], linewidth=2)
        
        ax3.set_title('Yearly Trend - Top Companies', fontweight='bold', fontsize=12)
        ax3.set_xlabel('Year')
        ax3.set_ylabel('Patents')
        ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax3.grid(True, alpha=0.3)
        
        # 4. 技術分野ヒートマップ
        ax4 = plt.subplot(3, 3, 4)
        if company_tech_scores:
            # データフレーム作成
            tech_matrix = pd.DataFrame(company_tech_scores).T.fillna(0)
            if len(tech_matrix) > 0:
                # 上位企業のみ表示
                top_tech_companies = tech_matrix.sum(axis=1).nlargest(10).index
                sns.heatmap(tech_matrix.loc[top_tech_companies], annot=True, fmt='d', 
                           cmap='YlOrRd', ax=ax4, cbar_kws={'label': 'Patents'})
                ax4.set_title('Technology Focus Heatmap', fontweight='bold', fontsize=12)
                ax4.set_xlabel('Technology Area')
                ax4.set_ylabel('Company')
        
        # 5. 国別出願分布
        ax5 = plt.subplot(3, 3, 5)
        country_dist = target_patents['country_code'].value_counts().head(8)
        ax5.bar(country_dist.index, country_dist.values, color='lightcoral')
        ax5.set_title('Patent Distribution by Country', fontweight='bold', fontsize=12)
        ax5.set_xlabel('Country Code')
        ax5.set_ylabel('Number of Patents')
        ax5.tick_params(axis='x', rotation=45)
        
        # 6-9. 主要企業個別分析
        top_4_companies = company_counts.head(4).index
        for i, company in enumerate(top_4_companies):
            ax = plt.subplot(3, 3, 6+i)
            company_data = target_patents[target_patents['normalized_assignee'] == company]
            yearly_trend = company_data.groupby('filing_year').size()
            
            if len(yearly_trend) > 0:
                ax.bar(yearly_trend.index, yearly_trend.values, alpha=0.7, color=f'C{i}')
                ax.set_title(f'{company[:20]} Trend', fontweight='bold', fontsize=10)
                ax.set_xlabel('Year')
                ax.set_ylabel('Patents')
                ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('target_company_analysis.png', dpi=300, bbox_inches='tight')
        print("✓ ターゲット企業分析グラフを 'target_company_analysis.png' に保存しました")
    
    def generate_target_company_report(self, target_patents, company_tech_scores, timeline_df, global_companies):
        """ターゲット企業専用レポート生成"""
        print("\n📋 ターゲット企業レポートを生成中...")
        
        with open('target_company_report.txt', 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("ESC特許 ターゲット企業分析レポート\n")
            f.write("=" * 80 + "\n")
            f.write(f"分析日時: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"ターゲット企業特許: {len(target_patents):,}件\n")
            f.write(f"全体データ: {len(self.df):,}件\n\n")
            
            # ターゲット企業別統計
            f.write("【ターゲット企業別出願統計】\n")
            f.write("-" * 60 + "\n")
            company_stats = target_patents['normalized_assignee'].value_counts()
            
            f.write("■ 日本企業:\n")
            for company in self.target_companies['Japanese'].keys():
                if company in company_stats:
                    count = company_stats[company]
                    jp_name = self.target_companies['Japanese'][company]
                    f.write(f"  {company:25s} ({jp_name}): {count:3d}件\n")
                else:
                    jp_name = self.target_companies['Japanese'][company]
                    f.write(f"  {company:25s} ({jp_name}): {0:3d}件\n")
            
            f.write("\n■ 海外企業:\n")
            for company in self.target_companies['International'].keys():
                if company in company_stats:
                    count = company_stats[company]
                    intl_name = self.target_companies['International'][company]
                    f.write(f"  {company:25s} ({intl_name}): {count:3d}件\n")
                else:
                    intl_name = self.target_companies['International'][company]
                    f.write(f"  {company:25s} ({intl_name}): {0:3d}件\n")
            
            # 技術注力分野
            f.write(f"\n【企業別技術注力分野】\n")
            f.write("-" * 60 + "\n")
            for company in self.all_targets:
                if company in company_tech_scores and sum(company_tech_scores[company].values()) > 0:
                    scores = company_tech_scores[company]
                    sorted_techs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                    f.write(f"{company:25s}:")
                    for tech, count in sorted_techs[:3]:  # Top 3技術分野
                        if count > 0:
                            f.write(f" {tech}({count})")
                    f.write("\n")
            
            # グローバル展開
            f.write(f"\n【グローバル展開状況】\n")
            f.write("-" * 60 + "\n")
            for company_data in global_companies[:15]:
                company = company_data['company']
                countries = company_data['countries']
                patents = company_data['total_patents']
                f.write(f"{company:25s}: {countries:2d}カ国, {patents:3d}件\n")
            
            # 重要特許タイムライン
            f.write(f"\n【重要特許タイムライン (2020年以降)】\n")
            f.write("-" * 60 + "\n")
            recent_timeline = timeline_df[timeline_df['year'] >= 2020].sort_values('year')
            for _, row in recent_timeline.iterrows():
                f.write(f"{row['year']} - {row['company']:20s}: {row['title']}\n")
        
        print("✓ ターゲット企業レポートを 'target_company_report.txt' に保存しました")
    
    def run_target_analysis(self):
        """ターゲット企業分析の実行"""
        print("🎯 ターゲット企業ESC特許分析を開始します...")
        print("=" * 70)
        
        # 1. ターゲット企業出願状況
        target_patents = self.analyze_target_company_presence()
        
        if target_patents.empty:
            print("❌ ターゲット企業の特許データが不足しています。")
            return
        
        # 2. 競合ポジショニング
        yearly_data = self.competitive_positioning_analysis(target_patents)
        
        # 3. 技術注力分野分析
        company_tech_scores = self.technology_focus_analysis(target_patents)
        
        # 4. イノベーション・タイムライン
        timeline_df = self.innovation_timeline_analysis(target_patents)
        
        # 5. 市場戦略分析
        country_analysis, global_companies = self.market_strategy_analysis(target_patents)
        
        # 6. 可視化
        self.create_target_company_visualizations(target_patents, yearly_data, company_tech_scores, timeline_df)
        
        # 7. レポート生成
        self.generate_target_company_report(target_patents, company_tech_scores, timeline_df, global_companies)
        
        print("\n🎉 ターゲット企業分析完了！")
        print("\n📁 生成ファイル:")
        print("   - target_company_analysis.png (企業別分析グラフ)")
        print("   - target_company_report.txt (詳細レポート)")

if __name__ == "__main__":
    analyzer = TargetCompanyAnalyzer()
    analyzer.run_target_analysis()
