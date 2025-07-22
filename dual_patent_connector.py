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
        
        # BigQuery接続を試行
        if BIGQUERY_AVAILABLE:
            self.setup_bigquery()
        
        # PatentsView API設定
        self.patents_api_url = "https://api.patentsview.org/patents/query"
        
    def setup_bigquery(self):
        """BigQuery接続設定"""
        try:
            if 'google_cloud' in st.secrets:
                credentials_info = dict(st.secrets["google_cloud"])
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=["https://www.googleapis.com/auth/bigquery"]
                )
                project_id = credentials_info.get('project_id', 'fusionpatentsearch')
                self.bigquery_client = bigquery.Client(credentials=credentials, project=project_id)
                
                # 接続テスト
                test_query = "SELECT 1 as test"
                query_job = self.bigquery_client.query(test_query)
                list(query_job.result())
                
                self.bigquery_connected = True
                st.success("✅ BigQuery (Google Patents) 接続成功")
                
        except Exception as e:
            st.warning(f"⚠️ BigQuery接続失敗: {str(e)}")
            self.bigquery_connected = False
    
    def search_patents_bigquery(self, start_date='2015-01-01', limit=500):
        """BigQueryから特許データを取得"""
        if not self.bigquery_connected:
            return pd.DataFrame()
        
        try:
            query = f"""
            SELECT 
                publication_number,
                assignee_harmonized as assignee,
                filing_date,
                country_code,
                title_localized as title,
                EXTRACT(YEAR FROM filing_date) as filing_year
            FROM `patents-public-data.patents.publications` 
            WHERE 
                filing_date >= '{start_date}'
                AND filing_date <= '2024-07-22'
                AND assignee_harmonized IS NOT NULL
                AND country_code IN ('US', 'JP', 'EP', 'WO')
                AND (
                    REGEXP_CONTAINS(UPPER(assignee_harmonized), r'APPLIED MATERIALS|TOKYO ELECTRON|KYOCERA|NGK INSULATORS|TOTO|LAM RESEARCH|ENTEGRIS|SHINKO ELECTRIC')
                    OR REGEXP_CONTAINS(UPPER(title_localized), r'ELECTROSTATIC CHUCK|ESC|CURVED CHUCK|FLEXIBLE CHUCK')
                )
            ORDER BY filing_date DESC
            LIMIT {limit}
            """
            
            st.info("🔍 BigQuery (Google Patents) で検索中...")
            
            job_config = bigquery.QueryJobConfig()
            job_config.maximum_bytes_billed = 1000000000  # 1GB制限
            
            query_job = self.bigquery_client.query(query, job_config=job_config)
            results = query_job.result(timeout=30)
            
            df = results.to_dataframe()
            
            if len(df) > 0:
                df['abstract'] = 'Patent data from Google Patents BigQuery dataset - comprehensive global patent information.'
                df['data_source'] = 'BigQuery (Google Patents)'
                st.success(f"✅ BigQuery: {len(df)}件取得")
                return df
            else:
                st.warning("⚠️ BigQuery: 該当データなし")
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"❌ BigQuery エラー: {str(e)}")
            return pd.DataFrame()
    
    def search_patents_api(self, start_date='2015-01-01', limit=500):
        """PatentsView APIから特許データを取得"""
        try:
            target_companies = [
                "Applied Materials", "Tokyo Electron", "Kyocera Corporation",
                "NGK Insulators", "Lam Research", "Entegris",
                "TOTO", "Shinko Electric Industries"
            ]
            
            all_patents = []
            st.info("🔍 PatentsView API (USPTO) で検索中...")
            
            for company in target_companies[:4]:  # API負荷軽減のため4社に限定
                try:
                    # 複数の検索パターンを試行
                    search_patterns = [
                        {"assignee_organization": company},
                        {"assignee_organization": company.split()[0]}  # 会社名の最初の単語
                    ]
                    
                    for pattern in search_patterns:
                        query = {
                            "q": {
                                "_and": [
                                    pattern,
                                    {"_gte": {"patent_date": start_date}},
                                    {"_or": [
                                        {"patent_title": "electrostatic chuck"},
                                        {"patent_title": "chuck"},
                                        {"patent_title": "semiconductor"},
                                        {"patent_abstract": "electrostatic"}
                                    ]}
                                ]
                            },
                            "f": [
                                "patent_number", "patent_title", "patent_date",
                                "assignee_organization", "patent_abstract"
                            ],
                            "s": [{"patent_date": "desc"}],
                            "o": {"per_page": 50}
                        }
                        
                        response = requests.post(self.patents_api_url, json=query, timeout=15)
                        
                        if response.status_code == 200:
                            data = response.json()
                            patents = data.get('patents', [])
                            
                            for patent in patents:
                                assignees = patent.get('assignees', [])
                                assignee_name = assignees[0].get('assignee_organization', company) if assignees else company
                                
                                all_patents.append({
                                    'publication_number': patent.get('patent_number', ''),
                                    'assignee': assignee_name,
                                    'filing_date': patent.get('patent_date', ''),
                                    'country_code': 'US',
                                    'title': patent.get('patent_title', ''),
                                    'abstract': (patent.get('patent_abstract', '') or '')[:300] + '...',
                                    'data_source': 'PatentsView API (USPTO)'
                                })
                            
                            if patents:
                                st.success(f"✅ PatentsView: {company} - {len(patents)}件")
                                break  # 成功したらループを抜ける
                        
                        time.sleep(0.3)  # API制限対策
                        
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
                
                st.success(f"✅ PatentsView API: 合計 {len(df)}件取得")
                return df
            else:
                st.warning("⚠️ PatentsView API: データなし")
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"❌ PatentsView API エラー: {str(e)}")
            return pd.DataFrame()
    
    def search_esc_patents(self, start_date='2015-01-01', limit=1000, use_sample=False, data_source="両方"):
        """統合特許検索"""
        if use_sample:
            return self.get_demo_data()
        
        all_data = []
        
        # データソース選択に応じて取得
        if data_source in ["両方", "BigQuery"] and self.bigquery_connected:
            bigquery_data = self.search_patents_bigquery(start_date, limit//2)
            if not bigquery_data.empty:
                all_data.append(bigquery_data)
        
        if data_source in ["両方", "PatentsView API"]:
            api_data = self.search_patents_api(start_date, limit//2)
            if not api_data.empty:
                all_data.append(api_data)
        
        # データ統合
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # 重複除去（特許番号ベース）
            combined_df = combined_df.drop_duplicates(subset=['publication_number'])
            
            # データソース統計
            source_counts = combined_df['data_source'].value_counts()
            st.info(f"📊 データソース別取得件数: {dict(source_counts)}")
            
            # 件数制限
            combined_df = combined_df.head(limit)
            
            st.success(f"🎉 **実データ取得成功！** 合計 {len(combined_df)}件の特許データ")
            return combined_df
        
        else:
            st.warning("⚠️ 両方のAPIからデータを取得できませんでした。デモデータを使用します。")
            return self.get_demo_data()
    
    def get_demo_data(self):
        """改良されたデモデータ"""
        companies = [
            'Applied Materials Inc', 'Tokyo Electron Limited', 'Kyocera Corporation',
            'NGK Insulators Ltd', 'TOTO Ltd', 'Lam Research Corporation',
            'Entegris Inc', 'Shinko Electric Industries'
        ]
        
        demo_data = []
        base_date = datetime(2015, 1, 1)
        
        for i in range(300):
            company = random.choice(companies)
            days_offset = random.randint(0, (datetime.now() - base_date).days)
            filing_date = base_date + timedelta(days=days_offset)
            
            demo_data.append({
                'publication_number': f"US{random.randint(8000000, 9999999)}",
                'assignee': company,
                'filing_date': filing_date.date(),
                'country_code': random.choice(['US', 'JP', 'EP']),
                'title': f'Advanced Electrostatic Chuck Technology for Semiconductor Processing - Patent {i+1}',
                'abstract': f'Enhanced electrostatic chuck system with improved wafer holding capabilities. Patent {i+1} by {company}.',
                'filing_year': filing_date.year,
                'data_source': 'Demo Data'
            })
        
        df = pd.DataFrame(demo_data)
        st.info(f"📊 デモデータ: {len(df)}件")
        return df
    
    def test_connections(self):
        """両方の接続をテスト"""
        results = {}
        
        # BigQuery テスト
        if self.bigquery_connected:
            try:
                query = "SELECT COUNT(*) as total FROM `patents-public-data.patents.publications` LIMIT 1"
                result = self.bigquery_client.query(query).result()
                for row in result:
                    results['BigQuery'] = f"✅ 接続成功 - 総特許数: {row.total:,}件"
            except Exception as e:
                results['BigQuery'] = f"❌ 接続失敗: {str(e)}"
        else:
            results['BigQuery'] = "❌ 未接続"
        
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
                results['PatentsView API'] = f"✅ 接続成功 - Applied Materials: {count:,}件"
            else:
                results['PatentsView API'] = f"❌ API エラー: {response.status_code}"
        except Exception as e:
            results['PatentsView API'] = f"❌ 接続失敗: {str(e)}"
        
        return results
