import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
import random

# BigQuery接続用（既存）
try:
    from google.cloud import bigquery
    from google.oauth2 import service_account
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False

class DualPatentConnector:
    def __init__(self):
        self.bigquery_client = None
        self.bigquery_connected = False
        self.patents_api_connected = True  # PatentsView APIは常に利用可能
        
        # PatentsView API設定
        self.patents_api_url = "https://api.patentsview.org/patents/query"
        
        # BigQuery接続を試行（一時的に無効化）
        # if BIGQUERY_AVAILABLE:
        #     self.setup_bigquery()
        
    def setup_bigquery(self):
        """BigQuery接続設定（一時的に無効化）"""
        try:
            st.info("⚠️ BigQuery は一時的に無効化されています")
            self.bigquery_connected = False
        except Exception as e:
            self.bigquery_connected = False
    
    def search_patents_bigquery(self, start_date='2015-01-01', limit=500):
        """BigQueryから特許データを取得（無効化中）"""
        return pd.DataFrame()
    
    def search_patents_api(self, start_date='2015-01-01', limit=500):
        """PatentsView APIから特許データを取得（完成版）"""
        try:
            st.info("🔍 PatentsView API (USPTO) で検索中...")
            
            # 基本的なテストクエリ
            test_query = {
                "q": {"assignee_organization": "Applied Materials"},
                "f": ["patent_number"],
                "o": {"per_page": 1}
            }
            
            # 接続テスト
            test_response = requests.post(self.patents_api_url, json=test_query, timeout=5)
            if test_response.status_code != 200:
                st.error(f"❌ PatentsView API接続失敗: HTTP {test_response.status_code}")
                return pd.DataFrame()
            
            # 対象企業リスト
            companies = [
                "Applied Materials", "Tokyo Electron", "Lam Research", 
                "ASML", "KLA Corporation", "Entegris", "Kyocera"
            ]
            
            all_patents = []
            
            for company in companies:
                try:
                    # ESC関連キーワードを含むクエリ
                    query = {
                        "q": {
                            "_and": [
                                {"assignee_organization": company},
                                {"_gte": {"patent_date": start_date}},
                                {"_or": [
                                    {"patent_title": "chuck"},
                                    {"patent_title": "electrostatic"},
                                    {"patent_title": "semiconductor"},
                                    {"patent_title": "wafer"},
                                    {"patent_abstract": "electrostatic chuck"}
                                ]}
                            ]
                        },
                        "f": [
                            "patent_number", "patent_title", "patent_date", 
                            "assignee_organization", "patent_abstract"
                        ],
                        "s": [{"patent_date": "desc"}],
                        "o": {"per_page": 30}
                    }
                    
                    response = requests.post(self.patents_api_url, json=query, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        patents = data.get('patents', [])
                        
                        st.info(f"📊 {company}: {len(patents)}件の関連特許を発見")
                        
                        for patent in patents:
                            assignees = patent.get('assignees', [])
                            assignee_name = assignees[0].get('assignee_organization', company) if assignees else company
                            
                            patent_title = patent.get('patent_title', '')
                            patent_abstract = patent.get('patent_abstract', '') or 'No abstract available'
                            
                            all_patents.append({
                                'publication_number': patent.get('patent_number', ''),
                                'assignee': assignee_name,
                                'filing_date': patent.get('patent_date', ''),
                                'country_code': 'US',
                                'title': patent_title[:200] + '...' if len(patent_title) > 200 else patent_title,
                                'abstract': patent_abstract[:300] + '...' if len(patent_abstract) > 300 else patent_abstract,
                                'data_source': 'PatentsView API (USPTO)'
                            })
                    else:
                        st.warning(f"⚠️ {company}: API エラー {response.status_code}")
                    
                    # API制限対策
                    time.sleep(0.8)
                    
                except Exception as e:
                    st.warning(f"⚠️ {company}: {str(e)}")
                    continue
            
            if all_patents:
                df = pd.DataFrame(all_patents)
                
                # データクリーニング
                df['filing_date'] = pd.to_datetime(df['filing_date'], errors='coerce')
                df = df.dropna(subset=['filing_date'])
                df['filing_year'] = df['filing_date'].dt.year
                
                # 重複除去
                df = df.drop_duplicates(subset=['publication_number'])
                
                # 日付フィルタ
                start_dt = pd.to_datetime(start_date)
                df = df[df['filing_date'] >= start_dt]
                
                # 件数制限
                df = df.head(limit)
                
                st.success(f"✅ PatentsView API: 合計 {len(df)}件の実特許データを取得!")
                return df
            else:
                st.warning("⚠️ PatentsView API: 検索条件に一致するデータがありませんでした")
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"❌ PatentsView API エラー: {str(e)}")
            return pd.DataFrame()
    
    def search_esc_patents(self, start_date='2015-01-01', limit=1000, use_sample=False, data_source="PatentsView API"):
        """統合特許検索（完成版）"""
        if use_sample or data_source == "デモデータ":
            return self.get_demo_data()
        
        # PatentsView APIを使用
        api_data = self.search_patents_api(start_date, limit)
        
        if not api_data.empty:
            st.success(f"🎉 **実データ取得成功！** {len(api_data)}件の米国特許データ")
            return api_data
        else:
            st.warning("⚠️ 実データが取得できませんでした。デモデータを使用します。")
            return self.get_demo_data()
    
    def get_demo_data(self):
        """高品質デモデータ生成"""
        companies = [
            'Applied Materials Inc', 'Tokyo Electron Limited', 'Kyocera Corporation',
            'NGK Insulators Ltd', 'TOTO Ltd', 'Lam Research Corporation',
            'Entegris Inc', 'Shinko Electric Industries', 'ASML Holding NV',
            'KLA Corporation'
        ]
        
        # 実際のESC関連特許タイトルパターン
        title_patterns = [
            "Electrostatic chuck with curved surface for semiconductor processing",
            "Variable curvature electrostatic chuck system",
            "Conformal electrostatic chuck for wafer processing",
            "Multi-zone electrostatic chuck with temperature control",
            "Flexible electrostatic chuck for curved substrates",
            "Electrostatic chuck with improved particle performance",
            "Temperature controlled electrostatic chuck assembly",
            "Electrostatic chuck with enhanced wafer holding",
            "Curved electrostatic chuck for semiconductor manufacturing",
            "Advanced electrostatic chuck system with monitoring"
        ]
        
        demo_data = []
        base_date = datetime(2015, 1, 1)
        
        # 年次トレンドを反映
        year_weights = {
            2015: 0.5, 2016: 0.6, 2017: 0.7, 2018: 0.9, 2019: 1.0,
            2020: 0.8, 2021: 0.7, 2022: 0.6, 2023: 0.7, 2024: 0.8
        }
        
        for i in range(400):
            # 重み付けによる年の選択
            year = random.choices(list(year_weights.keys()), weights=list(year_weights.values()))[0]
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            filing_date = datetime(year, month, day)
            
            company = random.choice(companies)
            
            demo_data.append({
                'publication_number': f"US{random.randint(8000000, 11000000)}",
                'assignee': company,
                'filing_date': filing_date.date(),
                'country_code': 'US',
                'title': f"{random.choice(title_patterns)} - Patent {i+1}",
                'abstract': f"This invention relates to advanced electrostatic chuck technology for semiconductor manufacturing. The disclosed system provides improved wafer holding capabilities with enhanced temperature control and reduced particle generation. Patent {i+1} demonstrates innovative approaches to curved surface electrostatic chucking technology developed by {company}.",
                'filing_year': filing_date.year,
                'data_source': 'Demo Data'
            })
        
        df = pd.DataFrame(demo_data)
        st.info(f"📊 高品質デモデータ: {len(df)}件")
        return df
    
    def test_connections(self):
        """接続テスト（完成版）"""
        results = {}
        
        # BigQuery テスト（無効化中）
        results['BigQuery'] = "⚠️ 一時的に無効化中"
        
        # PatentsView API テスト
        try:
            test_query = {
                "q": {"assignee_organization": "Applied Materials"},
                "f": ["patent_number"],
                "o": {"per_page": 1}
            }
            response = requests.post(self.patents_api_url, json=test_query, timeout=10)
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                results['PatentsView API'] = f"✅ 接続成功 - Applied Materials: {count:,}件の特許"
            else:
                results['PatentsView API'] = f"❌ API エラー: HTTP {response.status_code}"
        except Exception as e:
            results['PatentsView API'] = f"❌ 接続失敗: {str(e)}"
        
        return results
