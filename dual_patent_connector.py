# dual_patent_connector.py の完全動作版

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
        self.patents_api_connected = True
        
        # 正しいPatentSearch API設定
        self.api_base_url = "https://search.patentsview.org/api/v1/patent/"
        self.api_key = None
        
        # セッション設定
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "FusionPatentSearch/1.0"
        })
        
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
    
    def setup_api_key(self):
        """APIキー設定UI"""
        st.sidebar.markdown("### 🔑 PatentSearch API設定")
        
        st.sidebar.info("APIキーは https://www.patentsview.org/help-center でリクエストできます")
        
        api_key_input = st.sidebar.text_input(
            "APIキー (必須):",
            type="password",
            help="PatentSearch APIキーを入力してください"
        )
        
        if api_key_input:
            self.api_key = api_key_input
            st.sidebar.success("✅ APIキー設定済み")
            return True
        else:
            st.sidebar.warning("⚠️ APIキーが必要です")
            return False
    
    def test_api_connection(self):
        """PatentSearch API接続テスト"""
        if not self.api_key:
            return False
            
        try:
            # シンプルなテストクエリ
            test_query = {
                "q": {"patent_id": "10000000"},  # 存在する特許番号
                "f": ["patent_id", "patent_title"],
                "o": {"size": 1}
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": self.api_key
            }
            
            response = self.session.post(
                self.api_base_url,
                json=test_query,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'patents' in data:
                    return True
            elif response.status_code == 401:
                st.error("❌ APIキーが無効です")
                return False
            elif response.status_code == 429:
                st.warning("⚠️ レート制限に到達")
                return False
            else:
                st.error(f"❌ API エラー: {response.status_code}")
                return False
                
        except Exception as e:
            st.error(f"❌ 接続テストエラー: {str(e)}")
            return False
        
        return False
    
    def search_patents_api(self, start_date='2015-01-01', limit=500):
        """PatentSearch APIから実データを取得"""
        
        if not self.api_key:
            st.error("❌ APIキーが設定されていません")
            return pd.DataFrame()
        
        try:
            st.info("🔍 PatentSearch API で実データを検索中...")
            
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": self.api_key
            }
            
            all_patents = []
            
            # 検索クエリ1: electrostatic chuck
            st.info("📊 Electrostatic Chuck 特許を検索中...")
            query1 = {
                "q": {"_text_any": {"patent_title": "electrostatic chuck"}},
                "f": [
                    "patent_id",
                    "patent_title", 
                    "patent_date",
                    "assignees.assignee_organization"
                ],
                "s": [{"patent_date": "desc"}],
                "o": {"size": 100}
            }
            
            response1 = self.session.post(
                self.api_base_url,
                json=query1,
                headers=headers,
                timeout=30
            )
            
            if response1.status_code == 200:
                data1 = response1.json()
                patents1 = data1.get('patents', [])
                st.success(f"✅ Electrostatic Chuck: {len(patents1)}件取得")
                
                for patent in patents1:
                    assignees = patent.get('assignees', [])
                    assignee_name = 'Unknown'
                    if assignees and len(assignees) > 0:
                        assignee_name = assignees[0].get('assignee_organization', 'Unknown')
                    
                    all_patents.append({
                        'publication_number': patent.get('patent_id', ''),
                        'assignee': assignee_name,
                        'filing_date': patent.get('patent_date', ''),
                        'country_code': 'US',
                        'title': patent.get('patent_title', ''),
                        'abstract': 'Retrieved from PatentSearch API',
                        'data_source': 'PatentSearch API (Real Data)'
                    })
            else:
                st.warning(f"⚠️ Query 1 failed: HTTP {response1.status_code}")
            
            time.sleep(2)  # レート制限対策
            
            # 検索クエリ2: 主要企業
            st.info("📊 主要企業の特許を検索中...")
            
            target_companies = [
                "Applied Materials",
                "Tokyo Electron", 
                "Kyocera",
                "Lam Research"
            ]
            
            for company in target_companies:
                try:
                    query_company = {
                        "q": {"assignees.assignee_organization": company},
                        "f": [
                            "patent_id",
                            "patent_title",
                            "patent_date", 
                            "assignees.assignee_organization"
                        ],
                        "s": [{"patent_date": "desc"}],
                        "o": {"size": 50}
                    }
                    
                    response_company = self.session.post(
                        self.api_base_url,
                        json=query_company,
                        headers=headers,
                        timeout=25
                    )
                    
                    if response_company.status_code == 200:
                        data_company = response_company.json()
                        patents_company = data_company.get('patents', [])
                        st.success(f"✅ {company}: {len(patents_company)}件取得")
                        
                        for patent in patents_company:
                            assignees = patent.get('assignees', [])
                            assignee_name = company
                            if assignees and len(assignees) > 0:
                                assignee_name = assignees[0].get('assignee_organization', company)
                            
                            all_patents.append({
                                'publication_number': patent.get('patent_id', ''),
                                'assignee': assignee_name,
                                'filing_date': patent.get('patent_date', ''),
                                'country_code': 'US',
                                'title': patent.get('patent_title', ''),
                                'abstract': 'Retrieved from PatentSearch API',
                                'data_source': 'PatentSearch API (Real Data)'
                            })
                    else:
                        st.warning(f"⚠️ {company}: HTTP {response_company.status_code}")
                    
                    time.sleep(1.5)  # レート制限対策
                    
                except Exception as e:
                    st.warning(f"⚠️ {company} 検索エラー: {str(e)}")
                    continue
            
            # データ処理
            if all_patents:
                df = pd.DataFrame(all_patents)
                
                # 重複除去
                df = df.drop_duplicates(subset=['publication_number'])
                
                # 日付処理
                df['filing_date'] = pd.to_datetime(df['filing_date'], errors='coerce')
                df = df.dropna(subset=['filing_date'])
                df['filing_year'] = df['filing_date'].dt.year
                
                # フィルタリング
                start_dt = pd.to_datetime(start_date)
                df = df[df['filing_date'] >= start_dt]
                
                # ソートと制限
                df = df.sort_values('filing_date', ascending=False)
                df = df.head(limit)
                
                st.success(f"🎉 **実データ取得成功！** {len(df)}件の実特許データをPatentSearch APIから取得")
                st.info(f"📅 期間: {df['filing_year'].min()}-{df['filing_year'].max()}")
                st.info(f"🏢 企業数: {df['assignee'].nunique()}社")
                
                return df
            else:
                st.warning("⚠️ データが取得できませんでした")
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"❌ PatentSearch API エラー: {str(e)}")
            return pd.DataFrame()
    
    def search_esc_patents(self, start_date='2015-01-01', limit=1000, use_sample=False, data_source="PatentsView API"):
        """統合特許検索"""
        if use_sample or data_source == "デモデータ":
            return self.get_demo_data()
        
        # PatentSearch APIを使用
        api_data = self.search_patents_api(start_date, limit)
        
        if not api_data.empty:
            return api_data
        else:
            st.warning("⚠️ APIデータが取得できませんでした。デモデータを使用します。")
            return self.get_demo_data()
    
    def get_demo_data(self):
        """高品質デモデータ生成"""
        companies = [
            'Applied Materials Inc', 'Tokyo Electron Limited', 'Kyocera Corporation',
            'NGK Insulators Ltd', 'TOTO Ltd', 'Lam Research Corporation',
            'Entegris Inc', 'Shinko Electric Industries', 'ASML Holding NV',
            'KLA Corporation'
        ]
        
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
        
        year_weights = {
            2015: 0.5, 2016: 0.6, 2017: 0.7, 2018: 0.9, 2019: 1.0,
            2020: 0.8, 2021: 0.7, 2022: 0.6, 2023: 0.7, 2024: 0.8
        }
        
        for i in range(400):
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
                'abstract': f"This invention relates to advanced electrostatic chuck technology for semiconductor manufacturing. Patent {i+1} demonstrates innovative approaches developed by {company}.",
                'filing_year': filing_date.year,
                'data_source': 'Demo Data'
            })
        
        df = pd.DataFrame(demo_data)
        st.info(f"📊 高品質デモデータ: {len(df)}件")
        return df
    
    def test_connections(self):
        """接続テスト"""
        results = {}
        
        # BigQuery テスト（無効化中）
        results['BigQuery'] = "⚠️ 一時的に無効化中"
        
        # PatentSearch API テスト
        if self.api_key:
            if self.test_api_connection():
                results['PatentSearch API'] = "✅ 接続成功・APIキー有効"
            else:
                results['PatentSearch API'] = "❌ 接続失敗"
        else:
            results['PatentSearch API'] = "❌ APIキー未設定"
        
        return results
