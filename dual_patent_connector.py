# dual_patent_connector.py の完全修正版

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
        
        # 新しいPatentSearch API設定
        self.new_api_base_url = "https://search.patentsview.org/api/v1/patent"
        self.api_key = None  # 後で設定画面で入力
        
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
    
    def test_new_api_connection(self):
        """新しいPatentSearch API接続テスト"""
        try:
            # APIキーなしでも公開データは取得可能かテスト
            test_url = f"{self.new_api_base_url}"
            
            # シンプルなクエリでテスト
            test_params = {
                "q": "electrostatic chuck",
                "f": ["patent_id", "patent_title"],
                "s": [{"patent_date": "desc"}],
                "o": {"size": 5}
            }
            
            response = self.session.post(test_url, json=test_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'patents' in data or 'data' in data:
                    st.success("✅ 新しいPatentSearch API接続成功")
                    return True
            elif response.status_code == 401:
                st.warning("⚠️ APIキーが必要です")
                return False
            else:
                st.error(f"❌ API エラー: {response.status_code}")
                return False
                
        except Exception as e:
            st.error(f"❌ API接続エラー: {str(e)}")
            return False
    
    def search_patents_new_api(self, start_date='2015-01-01', limit=500):
        """新しいPatentSearch APIから特許データを取得"""
        try:
            st.info("🔍 新しいPatentSearch API で検索中...")
            
            # APIキー設定の確認
            if not self.api_key:
                st.warning("⚠️ APIキーが設定されていません。公開データで試行します...")
            
            all_patents = []
            
            # 検索クエリのパターン
            search_queries = [
                # クエリ1: electrostatic chuck
                {
                    "q": "electrostatic chuck",
                    "f": ["patent_id", "patent_title", "patent_date", "assignee_organization"],
                    "s": [{"patent_date": "desc"}],
                    "o": {"size": 50}
                },
                # クエリ2: semiconductor chuck
                {
                    "q": "semiconductor chuck",
                    "f": ["patent_id", "patent_title", "patent_date", "assignee_organization"],
                    "s": [{"patent_date": "desc"}],
                    "o": {"size": 30}
                }
            ]
            
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-Api-Key"] = self.api_key
            
            for i, query in enumerate(search_queries, 1):
                try:
                    st.info(f"📊 検索パターン {i}/{len(search_queries)} を実行中...")
                    
                    response = self.session.post(
                        self.new_api_base_url,
                        json=query,
                        headers=headers,
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        patents = data.get('patents', data.get('data', []))
                        
                        st.success(f"✅ 検索パターン {i}: {len(patents)}件取得")
                        
                        for patent in patents:
                            # 新しいAPIの構造に合わせてデータ処理
                            patent_id = patent.get('patent_id', patent.get('id', ''))
                            title = patent.get('patent_title', patent.get('title', ''))
                            date = patent.get('patent_date', patent.get('date', ''))
                            
                            # assignee情報の処理
                            assignee = 'Unknown'
                            if 'assignee_organization' in patent:
                                assignee = patent['assignee_organization']
                            elif 'assignees' in patent and patent['assignees']:
                                assignee = patent['assignees'][0].get('organization', 'Unknown')
                            
                            all_patents.append({
                                'publication_number': patent_id,
                                'assignee': assignee,
                                'filing_date': date,
                                'country_code': 'US',
                                'title': title[:150] + '...' if len(title) > 150 else title,
                                'abstract': 'Patent abstract from PatentSearch API...',
                                'data_source': 'PatentSearch API (New)'
                            })
                    
                    elif response.status_code == 401:
                        st.error("❌ APIキーが無効です")
                        break
                    elif response.status_code == 429:
                        st.warning("⚠️ レート制限に到達。待機中...")
                        time.sleep(2)
                        continue
                    else:
                        st.warning(f"⚠️ 検索パターン {i}: HTTP {response.status_code}")
                    
                    time.sleep(1.5)  # レート制限対策
                    
                except Exception as e:
                    st.warning(f"検索パターン {i} エラー: {str(e)}")
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
            st.error(f"❌ 新API検索エラー: {str(e)}")
            return pd.DataFrame()
    
    def setup_api_key(self):
        """APIキー設定UI"""
        st.sidebar.markdown("### 🔑 API設定")
        
        api_key_input = st.sidebar.text_input(
            "PatentSearch APIキー:",
            type="password",
            help="https://search.patentsview.org からAPIキーを取得してください"
        )
        
        if api_key_input:
            self.api_key = api_key_input
            st.sidebar.success("✅ APIキー設定済み")
        else:
            st.sidebar.info("APIキーなしでも制限付きで動作します")
        
        return bool(api_key_input)
    
    def search_patents_api(self, start_date='2015-01-01', limit=500):
        """統合特許検索（新API対応）"""
        
        # 新しいAPIを試行
        new_api_data = self.search_patents_new_api(start_date, limit)
        
        if not new_api_data.empty:
            return new_api_data
        else:
            st.warning("⚠️ 新APIからデータを取得できませんでした")
            return pd.DataFrame()
    
    def search_esc_patents(self, start_date='2015-01-01', limit=1000, use_sample=False, data_source="PatentsView API"):
        """統合特許検索"""
        if use_sample or data_source == "デモデータ":
            return self.get_demo_data()
        
        # 新しいPatentSearch APIを使用
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
        
        # 新しいPatentSearch API テスト
        try:
            if self.test_new_api_connection():
                results['PatentSearch API'] = "✅ 接続成功・新API対応"
            else:
                results['PatentSearch API'] = "❌ 接続失敗・APIキー必要"
        except Exception as e:
            results['PatentSearch API'] = f"❌ エラー: {str(e)}"
        
        return results
