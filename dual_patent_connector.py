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
        
        # PatentsView API設定
        self.patents_api_url = "https://api.patentsview.org/patents/query"
        
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
    
    def test_simple_api(self):
        """最もシンプルなAPIテスト"""
        try:
            # 極めてシンプルなクエリ
            query = {
                "q": {"patent_title": "semiconductor"},
                "f": ["patent_number", "patent_title"],
                "o": {"per_page": 3}
            }
            
            response = self.session.post(self.patents_api_url, json=query, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                patents = data.get('patents', [])
                if patents:
                    st.success(f"✅ API動作確認: {len(patents)}件のサンプルデータを取得")
                    return True
                else:
                    st.warning("⚠️ API応答はあるが、データなし")
                    return False
            else:
                st.error(f"❌ API エラー: {response.status_code}")
                return False
                
        except Exception as e:
            st.error(f"❌ API接続エラー: {str(e)}")
            return False
    
    def search_patents_api(self, start_date='2015-01-01', limit=500):
        """PatentsView APIから特許データを取得（確実に動作するバージョン）"""
        try:
            st.info("🔍 PatentsView API で検索開始...")
            
            # まず簡単なテスト
            if not self.test_simple_api():
                st.warning("⚠️ API接続に問題があるため、デモデータを使用します")
                return pd.DataFrame()
            
            # 実際のデータ取得
            all_patents = []
            
            # ステップ1: Applied Materials の検索
            try:
                st.info("📊 Applied Materials の特許を検索中...")
                query1 = {
                    "q": {"assignee_organization": "Applied Materials"},
                    "f": ["patent_number", "patent_title", "patent_date", "assignee_organization"],
                    "s": [{"patent_date": "desc"}],
                    "o": {"per_page": 25}
                }
                
                response = self.session.post(self.patents_api_url, json=query1, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    patents = data.get('patents', [])
                    st.success(f"✅ Applied Materials: {len(patents)}件取得")
                    
                    for patent in patents:
                        assignees = patent.get('assignees', [])
                        company = 'Applied Materials'
                        if assignees:
                            company = assignees[0].get('assignee_organization', 'Applied Materials')
                        
                        all_patents.append({
                            'publication_number': patent.get('patent_number', ''),
                            'assignee': company,
                            'filing_date': patent.get('patent_date', ''),
                            'country_code': 'US',
                            'title': patent.get('patent_title', 'No title')[:150] + '...',
                            'abstract': 'Patent abstract from PatentsView API...',
                            'data_source': 'PatentsView API (USPTO)'
                        })
                
                time.sleep(1)  # API制限対策
                
            except Exception as e:
                st.warning(f"Applied Materials検索エラー: {str(e)}")
            
            # ステップ2: 半導体関連の検索
            try:
                st.info("📊 半導体関連特許を検索中...")
                query2 = {
                    "q": {
                        "_or": [
                            {"patent_title": "electrostatic chuck"},
                            {"patent_title": "semiconductor chuck"},
                            {"patent_title": "wafer chuck"}
                        ]
                    },
                    "f": ["patent_number", "patent_title", "patent_date", "assignee_organization"],
                    "s": [{"patent_date": "desc"}],
                    "o": {"per_page": 30}
                }
                
                response = self.session.post(self.patents_api_url, json=query2, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    patents = data.get('patents', [])
                    st.success(f"✅ 半導体関連: {len(patents)}件取得")
                    
                    for patent in patents:
                        assignees = patent.get('assignees', [])
                        company = 'Unknown'
                        if assignees:
                            company = assignees[0].get('assignee_organization', 'Unknown')
                        
                        all_patents.append({
                            'publication_number': patent.get('patent_number', ''),
                            'assignee': company,
                            'filing_date': patent.get('patent_date', ''),
                            'country_code': 'US',
                            'title': patent.get('patent_title', 'No title')[:150] + '...',
                            'abstract': 'Patent abstract from PatentsView API...',
                            'data_source': 'PatentsView API (USPTO)'
                        })
                
                time.sleep(1)
                
            except Exception as e:
                st.warning(f"半導体検索エラー: {str(e)}")
            
            # ステップ3: その他の企業
            companies = ["Tokyo Electron", "KYOCERA", "Lam Research"]
            for company in companies:
                try:
                    st.info(f"📊 {company} の特許を検索中...")
                    query = {
                        "q": {"assignee_organization": company},
                        "f": ["patent_number", "patent_title", "patent_date", "assignee_organization"],
                        "s": [{"patent_date": "desc"}],
                        "o": {"per_page": 15}
                    }
                    
                    response = self.session.post(self.patents_api_url, json=query, timeout=12)
                    
                    if response.status_code == 200:
                        data = response.json()
                        patents = data.get('patents', [])
                        st.success(f"✅ {company}: {len(patents)}件取得")
                        
                        for patent in patents:
                            assignees = patent.get('assignees', [])
                            comp_name = company
                            if assignees:
                                comp_name = assignees[0].get('assignee_organization', company)
                            
                            all_patents.append({
                                'publication_number': patent.get('patent_number', ''),
                                'assignee': comp_name,
                                'filing_date': patent.get('patent_date', ''),
                                'country_code': 'US',
                                'title': patent.get('patent_title', 'No title')[:150] + '...',
                                'abstract': 'Patent abstract from PatentsView API...',
                                'data_source': 'PatentsView API (USPTO)'
                            })
                    else:
                        st.warning(f"⚠️ {company}: HTTP {response.status_code}")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    st.warning(f"{company}検索エラー: {str(e)}")
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
                
                st.success(f"🎉 **実データ取得成功！** {len(df)}件の実特許データ")
                st.info(f"📅 期間: {df['filing_year'].min()}-{df['filing_year'].max()}")
                st.info(f"🏢 企業数: {df['assignee'].nunique()}社")
                
                return df
            else:
                st.warning("⚠️ データが取得できませんでした")
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"❌ 重大エラー: {str(e)}")
            return pd.DataFrame()
    
    def search_esc_patents(self, start_date='2015-01-01', limit=1000, use_sample=False, data_source="PatentsView API"):
        """統合特許検索"""
        if use_sample or data_source == "デモデータ":
            return self.get_demo_data()
        
        # PatentsView APIを使用
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
        
        # PatentsView API テスト
        try:
            if self.test_simple_api():
                results['PatentsView API'] = "✅ 接続成功・データ取得可能"
            else:
                results['PatentsView API'] = "❌ 接続失敗"
        except Exception as e:
            results['PatentsView API'] = f"❌ エラー: {str(e)}"
        
        return results
