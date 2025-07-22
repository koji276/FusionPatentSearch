"""
BigQuery接続クラス - FusionPatentSearch用
Google Patents Public Dataへの接続とクエリ実行
"""

import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import json

class BigQueryConnector:
    """Google Patents BigQueryデータベースへの接続クラス"""
    
    def __init__(self):
        self.client = None
        self.project_id = None
        self.is_connected = False
        
    def connect_with_credentials(self, credentials_info):
        """サービスアカウント認証情報で接続"""
        try:
            # 認証情報からクレデンシャルを作成
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            
            # BigQueryクライアントを初期化
            self.client = bigquery.Client(
                credentials=credentials,
                project=credentials_info["project_id"]
            )
            self.project_id = credentials_info["project_id"]
            self.is_connected = True
            
            return True, "BigQuery接続成功"
            
        except Exception as e:
            return False, f"接続エラー: {str(e)}"
    
    def connect_with_streamlit_secrets(self):
        """Streamlit Secretsから認証情報を読み込んで接続"""
        try:
            if "gcp_service_account" in st.secrets:
                credentials_info = dict(st.secrets["gcp_service_account"])
                return self.connect_with_credentials(credentials_info)
            else:
                return False, "Streamlit Secretsに認証情報が見つかりません"
                
        except Exception as e:
            return False, f"Secrets読み込みエラー: {str(e)}"
    
    def test_connection(self):
        """接続テスト"""
        if not self.is_connected:
            return False, "未接続"
        
        try:
            # シンプルなテストクエリを実行
            query = """
            SELECT 
                COUNT(*) as total_patents
            FROM `patents-public-data.patents.publications` 
            WHERE country_code = 'US'
            LIMIT 1
            """
            
            result = self.client.query(query).to_dataframe()
            return True, f"接続成功 - 米国特許数: {result.iloc[0]['total_patents']:,}件"
            
        except Exception as e:
            return False, f"接続テストエラー: {str(e)}"
    
    def search_esc_patents(self, start_date='2010-01-01', limit=100):
        """ESC関連特許を検索"""
        if not self.is_connected:
            return None, "BigQueryに接続されていません"
        
        try:
            query = f"""
            WITH patent_data AS (
                SELECT 
                    publication_number,
                    filing_date,
                    country_code,
                    assignee,
                    -- title_localizedから英語タイトルを抽出
                    (SELECT text FROM UNNEST(title_localized) WHERE language = 'en' LIMIT 1) as title,
                    -- abstract_localizedから英語要約を抽出
                    (SELECT text FROM UNNEST(abstract_localized) WHERE language = 'en' LIMIT 1) as abstract
                FROM `patents-public-data.patents.publications` 
                WHERE 
                    filing_date >= '{start_date}'
                    AND country_code IN ('US', 'JP', 'EP')
                    AND (
                        EXISTS(SELECT 1 FROM UNNEST(title_localized) t 
                               WHERE REGEXP_CONTAINS(LOWER(t.text), 
                                     r'electrostatic.*chuck|curved.*esc|flexible.*esc|bendable.*chuck'))
                        OR 
                        EXISTS(SELECT 1 FROM UNNEST(abstract_localized) a 
                               WHERE REGEXP_CONTAINS(LOWER(a.text), 
                                     r'electrostatic.*chuck|curved.*esc|flexible.*esc'))
                    )
            )
            SELECT * FROM patent_data
            WHERE title IS NOT NULL
            ORDER BY filing_date DESC
            LIMIT {limit}
            """
            
            df = self.client.query(query).to_dataframe()
            return df, f"{len(df)}件のESC関連特許を取得"
            
        except Exception as e:
            return None, f"検索エラー: {str(e)}"
    
    def search_company_patents(self, company_name, start_date='2010-01-01', limit=50):
        """特定企業の特許を検索"""
        if not self.is_connected:
            return None, "BigQueryに接続されていません"
        
        try:
            query = f"""
            WITH patent_data AS (
                SELECT 
                    publication_number,
                    filing_date,
                    country_code,
                    assignee,
                    (SELECT text FROM UNNEST(title_localized) WHERE language = 'en' LIMIT 1) as title,
                    (SELECT text FROM UNNEST(abstract_localized) WHERE language = 'en' LIMIT 1) as abstract
                FROM `patents-public-data.patents.publications` 
                WHERE 
                    filing_date >= '{start_date}'
                    AND REGEXP_CONTAINS(LOWER(assignee), r'{company_name.lower()}')
                    AND (
                        EXISTS(SELECT 1 FROM UNNEST(title_localized) t 
                               WHERE REGEXP_CONTAINS(LOWER(t.text), 
                                     r'electrostatic.*chuck|curved.*esc|flexible.*esc|bendable.*chuck'))
                        OR 
                        EXISTS(SELECT 1 FROM UNNEST(abstract_localized) a 
                               WHERE REGEXP_CONTAINS(LOWER(a.text), 
                                     r'electrostatic.*chuck|curved.*esc|flexible.*esc'))
                    )
            )
            SELECT * FROM patent_data
            WHERE title IS NOT NULL
            ORDER BY filing_date DESC
            LIMIT {limit}
            """
            
            df = self.client.query(query).to_dataframe()
            return df, f"{company_name}の{len(df)}件のESC関連特許を取得"
            
        except Exception as e:
            return None, f"企業検索エラー: {str(e)}"
    
    def get_patent_statistics(self, start_date='2010-01-01'):
        """特許統計情報を取得"""
        if not self.is_connected:
            return None, "BigQueryに接続されていません"
        
        try:
            query = f"""
            WITH esc_patents AS (
                SELECT 
                    EXTRACT(YEAR FROM filing_date) as year,
                    country_code,
                    assignee,
                    filing_date
                FROM `patents-public-data.patents.publications` 
                WHERE 
                    filing_date >= '{start_date}'
                    AND (
                        EXISTS(SELECT 1 FROM UNNEST(title_localized) t 
                               WHERE REGEXP_CONTAINS(LOWER(t.text), 
                                     r'electrostatic.*chuck|curved.*esc|flexible.*esc'))
                        OR 
                        EXISTS(SELECT 1 FROM UNNEST(abstract_localized) a 
                               WHERE REGEXP_CONTAINS(LOWER(a.text), 
                                     r'electrostatic.*chuck|curved.*esc|flexible.*esc'))
                    )
            )
            SELECT 
                year,
                country_code,
                COUNT(*) as patent_count
            FROM esc_patents
            GROUP BY year, country_code
            ORDER BY year DESC, patent_count DESC
            """
            
            df = self.client.query(query).to_dataframe()
            return df, "統計データ取得成功"
            
        except Exception as e:
            return None, f"統計データエラー: {str(e)}"

def create_bigquery_connection():
    """BigQuery接続インスタンスを作成"""
    return BigQueryConnector()