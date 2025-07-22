 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
曲面ESC特許 高度分析モジュール
大学・研究機関の分析と技術トレンド詳細分析

使用方法:
python advanced_analyzer.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import re
from collections import Counter, defaultdict
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

class AdvancedPatentAnalyzer:
    def __init__(self, patent_data_file='curved_esc_patents.csv'):
        """特許データの読み込み"""
        try:
            self.df = pd.read_csv(patent_data_file, encoding='utf-8-sig')
            print(f"✓ {len(self.df)}件の特許データを読み込みました")
        except FileNotFoundError:
            print("❌ 特許データファイルが見つかりません。先にcurved_esc_analyzer.pyを実行してください。")
            exit(1)
    
    def classify_organizations(self):
        """組織タイプの分類（企業/大学/研究機関）"""
        print("\n🏛️ 組織タイプを分類中...")
        
        # 大学キーワード
        university_keywords = [
            'UNIVERSITY', 'UNIV', 'COLLEGE', 'INSTITUTE OF TECHNOLOGY',
            'TECH UNIVERSITY', 'STATE UNIVERSITY', 'NATIONAL UNIVERSITY',
            '大学', '工業大学', '技術大学', '科学技術大学', 'KAIST', 'POSTECH'
        ]
        
        # 研究機関キーワード  
        research_keywords = [
            'RESEARCH', 'INSTITUTE', 'LABORATORY', 'LAB', 'CENTER',
            'FOUNDATION', 'AGENCY', 'ORGANIZATION', 'COUNCIL',
            '研究所', '研究機構', '研究センター', '技術研究組合', '産総研', 'AIST'
        ]
        
        def classify_org(assignee):
            if pd.isna(assignee):
                return 'Unknown'
            
            assignee_upper = assignee.upper()
            
            # 大学判定
            for keyword in university_keywords:
                if keyword in assignee_upper:
                    return 'University'
            
            # 研究機関判定
            for keyword in research_keywords:
                if keyword in assignee_upper:
                    return 'Research Institute'
            
            return 'Company'
        
        self.df['org_type'] = self.df['normalized_assignee'].apply(classify_org)
        
        # 統計表示
        org_stats = self.df['org_type'].value_counts()
        print("📊 組織タイプ別統計:")
        for org_type, count in org_stats.items():
            percentage = count / len(self.df) * 100
            print(f"   {org_type}: {count}件 ({percentage:.1f}%)")
        
        return org_stats
    
    def university_ranking_analysis(self):
        """大学・研究機関のランキング分析"""
        print("\n🎓 大学・研究機関ランキング分析...")
        
        academic_orgs = self.df[self.df['org_type'].isin(['University', 'Research Institute'])]
        
        if len(academic_orgs) == 0:
            print("🔍 大学・研究機関の特許が見つかりませんでした")
            return pd.DataFrame(), pd.DataFrame()
        
        # 大学ランキング
        university_ranking = academic_orgs[academic_orgs['org_type'] == 'University']['normalized_assignee'].value_counts()
        
        # 研究機関ランキング  
        research_ranking = academic_orgs[academic_orgs['org_type'] == 'Research Institute']['normalized_assignee'].value_counts()
        
        print(f"🏆 トップ大学 (Top 10):")
        for i, (univ, count) in enumerate(university_ranking.head(10).items(), 1):
            print(f"   {i:2d}. {univ}: {count}件")
        
        print(f"\n🔬 トップ研究機関 (Top 10):")
        for i, (inst, count) in enumerate(research_ranking.head(10).items(), 1):
            print(f"   {i:2d}. {inst}: {count}件")
        
        return university_ranking, research_ranking
    
    def technology_trend_analysis(self):
        """詳細技術トレンド分析"""
        print("\n📈 技術トレンド詳細分析中...")
        
        # 年度データ準備
        self.df['filing_year'] = pd.to_datetime(self.df['filing_date']).dt.year
        
        # 技術キーワード分類
        tech_categories = {
            'Material': ['ceramic', 'dielectric', 'coating', 'polymer', 'silicon', 'セラミック', '誘電体'],
            'Control': ['temperature', 'thermal', 'control', 'feedback', 'sensor', '温度制御', '制御'],
            'Structure': ['electrode', 'chuck', 'clamp', 'surface', 'geometry', '電極', 'チャック'],
            'Process': ['plasma', 'etching', 'deposition', 'CVD', 'sputtering', 'プラズマ', 'エッチング'],
            'Measurement': ['monitoring', 'detection', 'measurement', 'sensing', '測定', 'モニタリング']
        }
        
        # 各技術カテゴリの年次トレンド
        tech_trends = {}
        
        for category, keywords in tech_categories.items():
            yearly_counts = {}
            
            for year in range(2015, 2025):
                year_data = self.df[self.df['filing_year'] == year]
                count = 0
                
                for _, row in year_data.iterrows():
                    text = str(row['title']) + ' ' + str(row['abstract'])
                    for keyword in keywords:
                        if keyword.lower() in text.lower():
                            count += 1
                            break  # 1件につき1回のみカウント
                
                yearly_counts[year] = count
            
            tech_trends[category] = yearly_counts
        
        # トレンドデータをDataFrameに変換
        tech_trend_df = pd.DataFrame(tech_trends)
        
        print("📊 技術分野別トレンド (2015-2024):")
        for category in tech_categories.keys():
            total = sum(tech_trends[category].values())
            print(f"   {category}: {total}件")
        
        return tech_trend_df
    
    def collaboration_network_analysis(self):
        """共同研究ネットワーク分析"""
        print("\n🤝 共同研究ネットワーク分析中...")
        
        # 複数出願人がいる特許を抽出
        collaboration_patents = []
        
        for _, row in self.df.iterrows():
            if pd.notna(row['assignee']) and ';' in str(row['assignee']):
                assignees = [a.strip() for a in str(row['assignee']).split(';')]
                if len(assignees) > 1:
                    collaboration_patents.append({
                        'patent_id': row['publication_number'],
                        'assignees': assignees,
                        'filing_year': row.get('filing_year', 0)
                    })
        
        print(f"🔍 共同出願特許: {len(collaboration_patents)}件発見")
        
        # 共同研究ペアの抽出
        collaboration_pairs = Counter()
        
        for patent in collaboration_patents:
            assignees = patent['assignees']
            for i in range(len(assignees)):
                for j in range(i+1, len(assignees)):
                    pair = tuple(sorted([assignees[i], assignees[j]]))
                    collaboration_pairs[pair] += 1
        
        # 上位共同研究ペア
        print("\n🏆 頻出共同研究ペア (Top 10):")
        for i, ((org1, org2), count) in enumerate(collaboration_pairs.most_common(10), 1):
            print(f"   {i:2d}. {org1} × {org2}: {count}件")
        
        return collaboration_patents, collaboration_pairs
    
    def emerging_technology_detection(self):
        """新興技術の検出"""
        print("\n🚀 新興技術検出分析中...")
        
        # 前期（2015-2019）と後期（2020-2024）で比較
        early_period = self.df[self.df['filing_year'].between(2015, 2019)]
        recent_period = self.df[self.df['filing_year'].between(2020, 2024)]
        
        # テキストデータの準備
        early_texts = (early_period['title'].fillna('') + ' ' + early_period['abstract'].fillna('')).tolist()
        recent_texts = (recent_period['title'].fillna('') + ' ' + recent_period['abstract'].fillna('')).tolist()
        
        if len(early_texts) == 0 or len(recent_texts) == 0:
            print("⚠️ 比較用データが不足しています")
            return
        
        # TF-IDF分析
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2
        )
        
        # 前期のTF-IDF
        early_tfidf = vectorizer.fit_transform(early_texts)
        early_scores = early_tfidf.mean(axis=0).A1
        
        # 後期のTF-IDF  
        recent_tfidf = vectorizer.transform(recent_texts)
        recent_scores = recent_tfidf.mean(axis=0).A1
        
        # スコア差分計算
        feature_names = vectorizer.get_feature_names_out()
        score_diff = recent_scores - early_scores
        
        # 新興キーワード（後期で急上昇）
        emerging_indices = np.argsort(score_diff)[-20:]
        emerging_keywords = [(feature_names[i], score_diff[i]) for i in emerging_indices[::-1]]
        
        print("🔥 新興技術キーワード (Top 15):")
        for i, (keyword, score) in enumerate(emerging_keywords[:15], 1):
            print(f"   {i:2d}. {keyword}: +{score:.4f}")
        
        return emerging_keywords
    
    def create_advanced_visualizations(self, org_stats, tech_trend_df, university_ranking, research_ranking):
        """高度な可視化の作成"""
        print("\n🎨 高度可視化を作成中...")
        
        # 図全体の設定
        fig = plt.figure(figsize=(20, 16))
        
        # 1. 組織タイプ別分布
        ax1 = plt.subplot(3, 3, 1)
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        wedges, texts, autotexts = ax1.pie(org_stats.values, labels=org_stats.index, 
                                          autopct='%1.1f%%', colors=colors)
        ax1.set_title('Organization Type Distribution', fontweight='bold', fontsize=12)
        
        # 2. 技術トレンド推移
        ax2 = plt.subplot(3, 3, 2)
        for column in tech_trend_df.columns:
            ax2.plot(tech_trend_df.index, tech_trend_df[column], marker='o', label=column, linewidth=2)
        ax2.set_title('Technology Trend by Category', fontweight='bold', fontsize=12)
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Number of Patents')
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax2.grid(True, alpha=0.3)
        
        # 3. 大学ランキング (Top 10)
        ax3 = plt.subplot(3, 3, 3)
        if len(university_ranking) > 0:
            top_unis = university_ranking.head(10)
            ax3.barh(range(len(top_unis)), top_unis.values, color='skyblue')
            ax3.set_yticks(range(len(top_unis)))
            ax3.set_yticklabels([name[:20] + '...' if len(name) > 20 else name for name in top_unis.index])
            ax3.set_title('Top Universities', fontweight='bold', fontsize=12)
            ax3.set_xlabel('Number of Patents')
        
        # 4. 研究機関ランキング (Top 10)
        ax4 = plt.subplot(3, 3, 4)
        if len(research_ranking) > 0:
            top_research = research_ranking.head(10)
            ax4.barh(range(len(top_research)), top_research.values, color='lightcoral')
            ax4.set_yticks(range(len(top_research)))
            ax4.set_yticklabels([name[:20] + '...' if len(name) > 20 else name for name in top_research.index])
            ax4.set_title('Top Research Institutes', fontweight='bold', fontsize=12)
            ax4.set_xlabel('Number of Patents')
        
        # 5. 企業 vs 学術機関の年次比較
        ax5 = plt.subplot(3, 3, 5)
        yearly_org_data = self.df.groupby(['filing_year', 'org_type']).size().unstack(fill_value=0)
        
        if 'Company' in yearly_org_data.columns:
            ax5.plot(yearly_org_data.index, yearly_org_data['Company'], 
                    marker='s', label='Company', linewidth=3, markersize=6)
        
        academic_patents = yearly_org_data.get('University', pd.Series(0)) + yearly_org_data.get('Research Institute', pd.Series(0))
        if len(academic_patents) > 0:
            ax5.plot(yearly_org_data.index, academic_patents, 
                    marker='^', label='Academic', linewidth=3, markersize=6)
        
        ax5.set_title('Company vs Academic Patents Trend', fontweight='bold', fontsize=12)
        ax5.set_xlabel('Year')
        ax5.set_ylabel('Number of Patents')
        ax5.legend()
        ax5.grid(True, alpha=0.3)
        
        # 6-9. 技術カテゴリ別個別トレンド
        tech_categories = tech_trend_df.columns[:4]  # 上位4カテゴリ
        for i, category in enumerate(tech_categories):
            ax = plt.subplot(3, 3, 6+i)
            ax.bar(tech_trend_df.index, tech_trend_df[category], alpha=0.7, color=f'C{i}')
            ax.set_title(f'{category} Technology Trend', fontweight='bold', fontsize=10)
            ax.set_xlabel('Year')
            ax.set_ylabel('Patents')
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('advanced_analysis.png', dpi=300, bbox_inches='tight')
        print("✓ 高度分析グラフを 'advanced_analysis.png' に保存しました")
        
        # 追加: ワードクラウド生成
        self.create_wordcloud()
    
    def create_wordcloud(self):
        """技術キーワードのワードクラウド生成"""
        print("☁️ ワードクラウドを生成中...")
        
        # テキストデータの準備
        all_text = ' '.join(self.df['title'].fillna('') + ' ' + self.df['abstract'].fillna(''))
        
        # ストップワード定義
        stop_words = {
            'method', 'system', 'apparatus', 'device', 'means', 'provided', 'including',
            'comprising', 'having', 'using', 'according', 'invention', 'present',
            'embodiment', 'example', 'first', 'second', 'third', 'one', 'two', 'three'
        }
        
        # ワードクラウド生成
        wordcloud = WordCloud(
            width=1200, height=800,
            background_color='white',
            stopwords=stop_words,
            max_words=100,
            colormap='viridis',
            font_path=None  # システムフォント使用
        ).generate(all_text)
        
        plt.figure(figsize=(15, 10))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('Curved ESC Technology Keywords', fontsize=20, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig('technology_wordcloud.png', dpi=300, bbox_inches='tight')
        print("✓ ワードクラウドを 'technology_wordcloud.png' に保存しました")
    
    def generate_comprehensive_report(self, org_stats, university_ranking, research_ranking, 
                                    emerging_keywords, collaboration_pairs):
        """包括的分析レポートの生成"""
        print("\n📄 包括的分析レポートを生成中...")
        
        with open('comprehensive_analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("曲面ESC特許 包括的分析レポート\n")
            f.write("=" * 80 + "\n")
            f.write(f"分析日時: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"分析対象: {len(self.df):,}件の特許\n")
            f.write(f"対象期間: {self.df['filing_date'].min()} ～ {self.df['filing_date'].max()}\n\n")
            
            # 組織分析
            f.write("【組織タイプ別分析】\n")
            f.write("-" * 40 + "\n")
            total_patents = len(self.df)
            for org_type, count in org_stats.items():
                percentage = count / total_patents * 100
                f.write(f"{org_type:18s}: {count:6,}件 ({percentage:5.1f}%)\n")
            
            # 大学ランキング
            f.write(f"\n【大学ランキング Top 15】\n")
            f.write("-" * 40 + "\n")
            for i, (univ, count) in enumerate(university_ranking.head(15).items(), 1):
                f.write(f"{i:2d}. {univ:<40s}: {count:3,}件\n")
            
            # 研究機関ランキング
            f.write(f"\n【研究機関ランキング Top 15】\n")
            f.write("-" * 40 + "\n")
            for i, (inst, count) in enumerate(research_ranking.head(15).items(), 1):
                f.write(f"{i:2d}. {inst:<40s}: {count:3,}件\n")
            
            # 新興技術
            f.write(f"\n【新興技術キーワード Top 20】\n")
            f.write("-" * 40 + "\n")
            for i, (keyword, score) in enumerate(emerging_keywords[:20], 1):
                f.write(f"{i:2d}. {keyword:<30s}: +{score:.4f}\n")
            
            # 共同研究
            f.write(f"\n【主要共同研究ペア Top 15】\n")
            f.write("-" * 40 + "\n")
            for i, ((org1, org2), count) in enumerate(collaboration_pairs.most_common(15), 1):
                f.write(f"{i:2d}. {org1} × {org2}: {count}件\n")
            
            # 年次統計
            yearly_stats = self.df.groupby('filing_year').size()
            f.write(f"\n【年次出願統計】\n")
            f.write("-" * 40 + "\n")
            for year, count in yearly_stats.items():
                f.write(f"{year}: {count:,}件\n")
        
        print("✓ 包括的分析レポートを 'comprehensive_analysis_report.txt' に保存しました")
    
    def run_advanced_analysis(self):
        """高度分析の実行"""
        print("🔬 高度特許分析を開始します...")
        print("=" * 60)
        
        # 1. 組織分類
        org_stats = self.classify_organizations()
        
        # 2. 大学・研究機関ランキング
        university_ranking, research_ranking = self.university_ranking_analysis()
        
        # 3. 技術トレンド分析
        tech_trend_df = self.technology_trend_analysis()
        
        # 4. 共同研究ネットワーク
        collaboration_patents, collaboration_pairs = self.collaboration_network_analysis()
        
        # 5. 新興技術検出
        emerging_keywords = self.emerging_technology_detection()
        
        # 6. 高度可視化
        self.create_advanced_visualizations(org_stats, tech_trend_df, university_ranking, research_ranking)
        
        # 7. 包括レポート生成
        self.generate_comprehensive_report(org_stats, university_ranking, research_ranking, 
                                         emerging_keywords, collaboration_pairs)
        
        print("\n🎉 高度分析完了！詳細な分析結果が生成されました。")
        print("\n📁 生成ファイル:")
        print("   - advanced_analysis.png (高度分析グラフ)")
        print("   - technology_wordcloud.png (技術キーワード雲)")  
        print("   - comprehensive_analysis_report.txt (包括レポート)")

if __name__ == "__main__":
    analyzer = AdvancedPatentAnalyzer()
    analyzer.run_advanced_analysis()
