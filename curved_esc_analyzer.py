 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
曲面ESC特許分析システム
Google Patents BigQueryを使用して世界中の曲面ESC関連特許を分析

使用方法:
1. Google Cloud ProjectでBigQuery APIを有効化
2. 認証情報を設定 (gcloud auth application-default login)
3. python curved_esc_analyzer.py を実行

出力:
- curved_esc_patents.csv: 全特許データ
- company_ranking.csv: 企業別ランキング
- trend_analysis.csv: 年次トレンド分析
- keyword_analysis.csv: キーワード分析
"""

import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import seaborn as sns
import re
from collections import Counter
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 日本語フォント設定
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif']

class CurvedESCPatentAnalyzer:
    def __init__(self):
        """BigQueryクライアントの初期化"""
        try:
            self.client = bigquery.Client()
            print("✓ BigQueryクライアント接続成功")
        except Exception as e:
            print(f"❌ BigQuery接続エラー: {e}")
            print("Google Cloud認証を確認してください: gcloud auth application-default login")
            exit(1)
    
    def search_curved_esc_patents(self):
        """ESC関連特許を日英両言語で検索 - ターゲット企業特化版"""
        query = """
        SELECT DISTINCT
            p.publication_number,
            p.country_code,
            p.filing_date,
            p.publication_date,
            p.application_kind,
            COALESCE(title_en.text, title_ja.text, title_other.text) as title,
            COALESCE(abstract_en.text, abstract_ja.text, abstract_other.text) as abstract,
            p.assignee_harmonized as assignee,
            p.inventor_harmonized as inventor,
            p.cpc_at_publication as cpc_codes
        FROM `patents-public-data.patents.publications` p
        LEFT JOIN UNNEST(title_localized) as title_en ON title_en.language = 'en'
        LEFT JOIN UNNEST(title_localized) as title_ja ON title_ja.language = 'ja' 
        LEFT JOIN UNNEST(title_localized) as title_other ON title_other.language NOT IN ('en', 'ja')
        LEFT JOIN UNNEST(abstract_localized) as abstract_en ON abstract_en.language = 'en'
        LEFT JOIN UNNEST(abstract_localized) as abstract_ja ON abstract_ja.language = 'ja'
        LEFT JOIN UNNEST(abstract_localized) as abstract_other ON abstract_other.language NOT IN ('en', 'ja')
        WHERE (
            -- ESC関連技術キーワード（英語）
            (REGEXP_CONTAINS(LOWER(COALESCE(title_en.text, '')), r'electrostatic.*chuck|esc|curved.*chuck|flexible.*chuck|wafer.*chuck')
             OR REGEXP_CONTAINS(LOWER(COALESCE(abstract_en.text, '')), r'electrostatic.*chuck|esc|curved.*substrate|flexible.*substrate|wafer.*distortion|substrate.*warpage'))
            OR
            -- ESC関連技術キーワード（日本語）
            (REGEXP_CONTAINS(COALESCE(title_ja.text, ''), r'静電チャック|ESC|ウエハチャック|基板チャック|曲面.*チャック')
             OR REGEXP_CONTAINS(COALESCE(abstract_ja.text, ''), r'静電.*チャック|ウエハ.*反り|基板.*歪|チャック.*吸着|静電.*吸着'))
            OR
            -- ターゲット企業での出願
            (REGEXP_CONTAINS(UPPER(COALESCE(p.assignee_harmonized, '')), 
                r'SHINKO ELECTRIC|TOTO|SUMITOMO OSAKA CEMENT|KYOCERA|NGK|NTK CERATEC|TSUKUBA SEIKO|CREATIVE TECHNOLOGY|TOKYO ELECTRON|APPLIED MATERIALS|LAM RESEARCH|ENTEGRIS|FM INDUSTRIES|MICO|SEMCO|CALITECH|BEIJING U-PRECISION|新光電気|住友大阪セメント|京セラ|日本ガイシ|筑波精工|東京エレクトロン'))
        )
        AND p.filing_date >= '2010-01-01'
        AND p.filing_date <= '2024-12-31'
        ORDER BY p.filing_date DESC
        LIMIT 15000
        """
        
        print("🔍 ESC関連特許データを検索中（ターゲット企業重点）...")
        try:
            df = self.client.query(query).to_dataframe()
            print(f"✓ {len(df)}件の特許データを取得しました")
            return df
        except Exception as e:
            print(f"❌ クエリエラー: {e}")
            return pd.DataFrame()
    
    def normalize_company_names(self, df):
        """企業名の正規化 - ESCメーカー特化版"""
        company_mapping = {
            # 日本企業
            'SHINKO ELECTRIC': ['新光電気工業', 'SHINKO ELECTRIC INDUSTRIES', 'Shinko Electric'],
            'TOTO': ['TOTO', 'TOTO LTD', 'トートー'],
            'SUMITOMO OSAKA CEMENT': ['住友大阪セメント', 'SUMITOMO OSAKA CEMENT CO'],
            'KYOCERA': ['Kyocera', '京セラ', 'KYOCERA CORPORATION'],
            'NGK INSULATORS': ['NGK', '日本ガイシ', 'NGK INSULATORS LTD'],
            'NTK CERATEC': ['NTK CERATEC', 'NTKセラテック', '日本特殊陶業', 'NGK SPARK PLUG'],
            'TSUKUBA SEIKO': ['筑波精工', 'TSUKUBA SEIKO CO'],
            'CREATIVE TECHNOLOGY': ['クリエイティブテクノロジー', 'CREATIVE TECHNOLOGY'],
            'TOKYO ELECTRON': ['Tokyo Electron', 'TEL', 'TOKYO ELECTRON LIMITED', '東京エレクトロン'],
            
            # 海外企業
            'APPLIED MATERIALS': ['Applied Materials', 'AMAT', 'APPLIED MATERIALS INC'],
            'LAM RESEARCH': ['Lam Research', 'LAM RESEARCH CORPORATION'],
            'ENTEGRIS': ['Entegris', 'ENTEGRIS INC'],
            'FM INDUSTRIES': ['FM Industries', 'FM INDUSTRIES INC'],  # 日本ガイシが買収
            'MICO': ['MiCo', 'MICO CERAMICS', 'MICO CO'],
            'SEMCO ENGINEERING': ['SEMCO Engineering', 'SEMCO ENGINEERING SAS'],
            'CALITECH': ['Calitech', 'CALITECH CO'],
            'BEIJING U-PRECISION': ['Beijing U-Precision', 'U-PRECISION TECH', 'BEIJING U-PRECISION TECH'],
            
            # 関連企業（比較対象）
            'KLA': ['KLA-Tencor', 'KLA CORPORATION'],
            'HITACHI HIGH-TECH': ['Hitachi High-Tech', '日立ハイテク'],
            'SCREEN': ['SCREEN Holdings', 'SCREEN SEMICONDUCTOR'],
            'ASML': ['ASML NETHERLANDS', 'ASML HOLDING']
        }
        
        df['normalized_assignee'] = df['assignee'].fillna('Unknown')
        
        for normalized, variants in company_mapping.items():
            for variant in variants:
                mask = df['normalized_assignee'].str.contains(variant, case=False, na=False)
                df.loc[mask, 'normalized_assignee'] = normalized
        
        return df
    
    def extract_keywords(self, text_series):
        """技術キーワードの抽出"""
        if text_series.isna().all():
            return Counter()
        
        # 英語技術キーワード
        en_keywords = [
            'curved', 'flexible', 'bendable', 'conformal', 'variable curvature',
            'electrostatic chuck', 'ESC', 'wafer distortion', 'substrate warpage',
            'temperature control', 'plasma confinement', 'ceramic', 'electrode',
            'dielectric', 'RF distribution', 'etch uniformity', 'clamping force'
        ]
        
        # 日本語技術キーワード
        ja_keywords = [
            '曲面', '湾曲', '可撓性', 'フレキシブル', '静電チャック',
            'ウエハ反り', '基板歪み', '温度制御', '密着性', '吸着力',
            'セラミック', '誘電体', '電極構造', 'プラズマ', 'エッチング均一性'
        ]
        
        all_text = ' '.join(text_series.fillna('').astype(str))
        keyword_counts = Counter()
        
        for keyword in en_keywords + ja_keywords:
            count = len(re.findall(keyword, all_text, re.IGNORECASE))
            if count > 0:
                keyword_counts[keyword] = count
        
        return keyword_counts
    
    def analyze_data(self, df):
        """データ分析実行"""
        print("\n📊 データ分析を開始...")
        
        # 基本統計
        total_patents = len(df)
        date_range = f"{df['filing_date'].min()} ～ {df['filing_date'].max()}"
        unique_companies = df['normalized_assignee'].nunique()
        
        print(f"📈 総特許数: {total_patents}件")
        print(f"📅 対象期間: {date_range}")
        print(f"🏢 出願機関数: {unique_companies}機関")
        
        # 企業別ランキング
        company_ranking = df['normalized_assignee'].value_counts().head(20)
        print(f"\n🏆 トップ企業: {company_ranking.index[0]} ({company_ranking.iloc[0]}件)")
        
        # 年次トレンド
        df['filing_year'] = pd.to_datetime(df['filing_date']).dt.year
        yearly_trend = df.groupby('filing_year').size()
        
        # キーワード分析
        title_keywords = self.extract_keywords(df['title'])
        abstract_keywords = self.extract_keywords(df['abstract'])
        
        return {
            'total_patents': total_patents,
            'company_ranking': company_ranking,
            'yearly_trend': yearly_trend,
            'title_keywords': title_keywords,
            'abstract_keywords': abstract_keywords,
            'unique_companies': unique_companies
        }
    
    def create_visualizations(self, df, analysis_results):
        """可視化グラフの作成"""
        print("\n📊 可視化グラフを作成中...")
        
        # 企業別出願件数 (Top 15)
        plt.figure(figsize=(12, 8))
        top_companies = analysis_results['company_ranking'].head(15)
        ax1 = plt.subplot(2, 2, 1)
        top_companies.plot(kind='barh', ax=ax1)
        plt.title('Top 15 Companies - Curved ESC Patents', fontsize=12, fontweight='bold')
        plt.xlabel('Number of Patents')
        plt.tight_layout()
        
        # 年次トレンド
        ax2 = plt.subplot(2, 2, 2)
        analysis_results['yearly_trend'].plot(kind='line', marker='o', ax=ax2)
        plt.title('Yearly Filing Trend', fontsize=12, fontweight='bold')
        plt.xlabel('Year')
        plt.ylabel('Number of Patents')
        plt.grid(True, alpha=0.3)
        
        # 国別分布
        ax3 = plt.subplot(2, 2, 3)
        country_dist = df['country_code'].value_counts().head(10)
        country_dist.plot(kind='pie', ax=ax3, autopct='%1.1f%%')
        plt.title('Patent Distribution by Country', fontsize=12, fontweight='bold')
        
        # 技術キーワード (Top 10)
        ax4 = plt.subplot(2, 2, 4)
        top_keywords = Counter(analysis_results['title_keywords']) + Counter(analysis_results['abstract_keywords'])
        if top_keywords:
            keywords_df = pd.Series(dict(top_keywords.most_common(10)))
            keywords_df.plot(kind='barh', ax=ax4)
            plt.title('Top Technology Keywords', fontsize=12, fontweight='bold')
            plt.xlabel('Frequency')
        
        plt.tight_layout()
        plt.savefig('curved_esc_analysis.png', dpi=300, bbox_inches='tight')
        print("✓ グラフを 'curved_esc_analysis.png' に保存しました")
        
        # 詳細な年次・企業別ヒートマップ
        plt.figure(figsize=(14, 8))
        
        # 主要企業の年次出願推移
        top_10_companies = analysis_results['company_ranking'].head(10).index
        company_year_data = df[df['normalized_assignee'].isin(top_10_companies)]
        heatmap_data = company_year_data.pivot_table(
            index='normalized_assignee', 
            columns='filing_year', 
            values='publication_number', 
            aggfunc='count', 
            fill_value=0
        )
        
        sns.heatmap(heatmap_data, annot=True, fmt='d', cmap='YlOrRd', 
                   cbar_kws={'label': 'Number of Patents'})
        plt.title('Patent Filing Heatmap: Top Companies by Year', 
                 fontsize=14, fontweight='bold')
        plt.xlabel('Filing Year')
        plt.ylabel('Company')
        plt.xticks(rotation=45)
        plt.yticks(rotation=0)
        
        plt.tight_layout()
        plt.savefig('company_year_heatmap.png', dpi=300, bbox_inches='tight')
        print("✓ ヒートマップを 'company_year_heatmap.png' に保存しました")
        
    def save_results(self, df, analysis_results):
        """結果をCSVファイルに保存"""
        print("\n💾 結果を保存中...")
        
        # 全特許データ
        df.to_csv('curved_esc_patents.csv', index=False, encoding='utf-8-sig')
        print("✓ curved_esc_patents.csv")
        
        # 企業別ランキング
        analysis_results['company_ranking'].to_csv('company_ranking.csv', 
                                                  header=['Patent_Count'], encoding='utf-8-sig')
        print("✓ company_ranking.csv")
        
        # 年次トレンド
        analysis_results['yearly_trend'].to_csv('yearly_trend.csv', 
                                               header=['Patent_Count'], encoding='utf-8-sig')
        print("✓ yearly_trend.csv")
        
        # キーワード分析
        combined_keywords = Counter(analysis_results['title_keywords']) + Counter(analysis_results['abstract_keywords'])
        pd.Series(dict(combined_keywords.most_common(50))).to_csv('keyword_analysis.csv', 
                                                                  header=['Frequency'], encoding='utf-8-sig')
        print("✓ keyword_analysis.csv")
        
        # サマリーレポート
        with open('analysis_summary.txt', 'w', encoding='utf-8') as f:
            f.write("=== 曲面ESC特許分析レポート ===\n")
            f.write(f"分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"総特許数: {analysis_results['total_patents']:,}件\n")
            f.write(f"出願機関数: {analysis_results['unique_companies']:,}機関\n\n")
            f.write("=== トップ10企業 ===\n")
            for i, (company, count) in enumerate(analysis_results['company_ranking'].head(10).items(), 1):
                f.write(f"{i:2d}. {company}: {count:,}件\n")
            f.write("\n=== 主要技術キーワード ===\n")
            combined_keywords = Counter(analysis_results['title_keywords']) + Counter(analysis_results['abstract_keywords'])
            for i, (keyword, count) in enumerate(combined_keywords.most_common(20), 1):
                f.write(f"{i:2d}. {keyword}: {count:,}回\n")
        
        print("✓ analysis_summary.txt")
        print(f"\n🎉 分析完了！{analysis_results['total_patents']}件の曲面ESC関連特許を分析しました。")
    
    def run_analysis(self):
        """メイン分析プロセスの実行"""
        print("🚀 曲面ESC特許分析システムを開始します...")
        print("=" * 50)
        
        # データ取得
        df = self.search_curved_esc_patents()
        if df.empty:
            print("❌ データが取得できませんでした。")
            return
        
        # データ前処理
        df = self.normalize_company_names(df)
        
        # 分析実行
        analysis_results = self.analyze_data(df)
        
        # 可視化
        self.create_visualizations(df, analysis_results)
        
        # 結果保存
        self.save_results(df, analysis_results)

if __name__ == "__main__":
    analyzer = CurvedESCPatentAnalyzer()
    analyzer.run_analysis()
