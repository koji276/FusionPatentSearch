import os
import json
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

class BigQueryConnector:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.patents_api_url = "https://api.patentsview.org/patents/query"
        self.setup_client()
    
    def setup_client(self):
        """BigQuery接続設定（PatentsView API優先）"""
        # BigQueryは一時的にスキップ
        st.info("⚠️ BigQuery は一時的にスキップしています")
        self.is_connected = False
        
    def search_esc_patents(self, start_date='2015-01-01', limit=1000, use_sample=False):
        """特許検索（PatentsView API + デモデータ）"""
        if use_sample:
            return self.get_demo_data()
        
        # PatentsView APIを試行
        api_data = self.search_patents_api(start_date, limit)
        
        if not api_data.empty:
            st.success(f"🎉 **実データ取得成功！** {len(api_data)}件の米国特許データ")
            return api_data
        else:
            st.warning("⚠️ 実データが取得できませんでした。デモデータを使用します。")
            return self.get_demo_data()
    
    def search_patents_api(self, start_date='2015-01-01', limit=500):
        """PatentsView APIから特許データを取得"""
        try:
            st.info("🔍 PatentsView API (USPTO) で検索中...")
            
            # 対象企業リスト
            companies = ["Applied Materials", "Tokyo Electron", "Lam Research", "ASML", "KLA"]
            all_patents = []
            
            for company in companies:
                try:
                    query = {
                        "q": {"assignee_organization": company},
                        "f": ["patent_number", "patent_title", "patent_date", "assignee_organization"],
                        "s": [{"patent_date": "desc"}],
                        "o": {"per_page": 20}
                    }
                    
                    response = requests.post(self.patents_api_url, json=query, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        patents = data.get('patents', [])
                        
                        st.info(f"📊 {company}: {len(patents)}件")
                        
                        for patent in patents:
                            assignees = patent.get('assignees', [])
                            assignee_name = assignees[0].get('assignee_organization', company) if assignees else company
                            
                            all_patents.append({
                                'publication_number': patent.get('patent_number', ''),
                                'assignee': assignee_name,
                                'filing_date': patent.get('patent_date', ''),
                                'country_code': 'US',
                                'title': patent.get('patent_title', ''),
                                'abstract': 'Patent data from USPTO PatentsView API.'
                            })
                    
                    time.sleep(0.5)  # API制限対策
                    
                except Exception as e:
                    st.warning(f"⚠️ {company}: {str(e)}")
                    continue
            
            if all_patents:
                df = pd.DataFrame(all_patents)
                df['filing_date'] = pd.to_datetime(df['filing_date'], errors='coerce')
                df = df.dropna(subset=['filing_date'])
                df['filing_year'] = df['filing_date'].dt.year
                df = df.drop_duplicates(subset=['publication_number'])
                
                # 日付フィルタ
                start_dt = pd.to_datetime(start_date)
                df = df[df['filing_date'] >= start_dt]
                df = df.head(limit)
                
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"❌ PatentsView API エラー: {str(e)}")
            return pd.DataFrame()
    
    def get_demo_data(self):
        """デモデータ生成"""
        companies = [
            'Applied Materials Inc', 'Tokyo Electron Limited', 'Kyocera Corporation',
            'NGK Insulators Ltd', 'TOTO Ltd', 'Lam Research Corporation',
            'Entegris Inc', 'Shinko Electric Industries', 'ASML Holding NV'
        ]
        
        demo_data = []
        base_date = datetime(2015, 1, 1)
        
        for i in range(300):
            company = random.choice(companies)
            days_offset = random.randint(0, (datetime.now() - base_date).days)
            filing_date = base_date + timedelta(days=days_offset)
            
            demo_data.append({
                'publication_number': f"US{random.randint(8000000, 11000000)}",
                'assignee': company,
                'filing_date': filing_date.date(),
                'country_code': 'US',
                'title': f'Advanced Electrostatic Chuck Technology - Patent {i+1}',
                'abstract': f'Enhanced electrostatic chuck system for semiconductor processing. Patent {i+1}.',
                'filing_year': filing_date.year
            })
        
        df = pd.DataFrame(demo_data)
        st.info(f"📊 デモデータ: {len(df)}件")
        return df

    def test_connection(self):
        """接続テスト"""
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
                return True, f"✅ PatentsView API接続成功 - Applied Materials: {count:,}件"
            else:
                return False, f"❌ API エラー: {response.status_code}"
        except Exception as e:
            return False, f"❌ 接続失敗: {str(e)}"
