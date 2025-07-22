# dual_patent_connector.py への段階的修正
# フェーズ1: 基本的な改善（既存コードに追加）

import streamlit as st
import pandas as pd
import requests
import time
import logging
from typing import Optional, Dict

class DualPatentConnector:
    def __init__(self):
        # 既存の初期化コード...
        self.bigquery_client = None
        self.is_bigquery_connected = False
        
        # === 新規追加: セッション設定 ===
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "FusionPatentSearch/1.0 (Academic Research)"
        })
        
        # === 新規追加: ログ設定 ===
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # === 新規追加: 改善された企業名マッピング ===
        self.enhanced_company_mapping = {
            'applied materials': 'Applied Materials',
            'applied materials inc': 'Applied Materials',
            'applied materials, inc.': 'Applied Materials',
            'tokyo electron': '東京エレクトロン',
            'tokyo electron limited': '東京エレクトロン',
            'tokyo electron ltd': '東京エレクトロン',
            'kyocera': '京セラ',
            'kyocera corporation': '京セラ',
            'toto': 'TOTO',
            'toto ltd': 'TOTO',
            'ngk insulators': '日本ガイシ',
            'ngk insulators, ltd.': '日本ガイシ',
            'lam research': 'Lam Research',
            'lam research corporation': 'Lam Research',
            'entegris': 'Entegris',
            'entegris, inc.': 'Entegris',
            'shinko electric': '新光電気工業',
            'shinko electric industries': '新光電気工業'
        }

    # 既存のsetup_bigquery()メソッドはそのまま保持

    # === 新規追加: 接続テストメソッド ===
    def test_api_connection(self) -> bool:
        """PatentsView API接続テスト（新規追加）"""
        try:
            # 最もシンプルなテストクエリ
            test_query = {
                "q": {"patent_number": "999999999"},  # 存在しない番号でテスト
                "f": ["patent_number"],
                "o": {"per_page": 1}
            }
            
            response = self.session.post(
                "https://api.patentsview.org/patents/query",
                json=test_query,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'patents' in data:
                    self.logger.info("API接続テスト成功")
                    return True
            
            self.logger.warning(f"API接続テスト失敗: {response.status_code}")
            return False
            
        except Exception as e:
            self.logger.error(f"API接続テストエラー: {e}")
            return False

    # === 既存メソッドの改善版 ===
    def search_patents_api_improved(self, limit=100):
        """改善版API検索（既存メソッドを置き換えない）"""
        
        # 接続テストを最初に実行
        if not self.test_api_connection():
            st.warning("⚠️ API接続に問題があります。デモデータを使用します。")
            return None
        
        # 既存のクエリを改善
        improved_query = {
            "q": {
                "_or": [
                    {"assignee_organization": "Applied Materials"},
                    {"assignee_organization": "Tokyo Electron"},
                    {"assignee_organization": "KYOCERA"},
                    {"assignee_organization": "Applied Materials Inc"},
                    {"assignee_organization": "Tokyo Electron Limited"},
                    # より多くのバリエーションを追加
                    {"patent_title": "electrostatic chuck"},
                    {"patent_title": "ESC"}
                ]
            },
            "f": ["patent_number", "patent_title", "patent_date", "assignee_organization"],
            "s": [{"patent_date": "desc"}],
            "o": {"per_page": min(limit, 100)}  # 制限を追加
        }
        
        return self._execute_query_with_retry(improved_query)

    # === 新規追加: リトライ機能付きクエリ実行 ===
    def _execute_query_with_retry(self, query: Dict, max_retries: int = 3) -> Optional[pd.DataFrame]:
        """リトライ機能付きクエリ実行"""
        
        for attempt in range(max_retries):
            try:
                # タイムアウトを段階的に延長
                timeout = 30 + (attempt * 15)
                
                self.logger.info(f"API クエリ実行 (試行 {attempt + 1}/{max_retries})")
                
                response = self.session.post(
                    "https://api.patentsview.org/patents/query",
                    json=query,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    return self._process_response_improved(response.json())
                    
                elif response.status_code == 429:  # レート制限
                    wait_time = 2 ** attempt
                    self.logger.warning(f"レート制限。{wait_time}秒待機...")
                    time.sleep(wait_time)
                    continue
                    
                elif response.status_code >= 500:  # サーバーエラー
                    self.logger.warning(f"サーバーエラー {response.status_code}。リトライ...")
                    time.sleep(2)
                    continue
                    
                else:
                    self.logger.error(f"API エラー {response.status_code}: {response.text[:100]}")
                    break
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"タイムアウト (試行 {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                    
            except Exception as e:
                self.logger.error(f"クエリ実行エラー: {e}")
                break
        
        return None

    # === 新規追加: 改善されたレスポンス処理 ===
    def _process_response_improved(self, data: Dict) -> Optional[pd.DataFrame]:
        """改善されたレスポンス処理"""
        
        if 'patents' not in data or not data['patents']:
            self.logger.warning("特許データが見つかりませんでした")
            return None
        
        patents = data['patents']
        self.logger.info(f"取得データ: {len(patents)}件")
        
        # DataFrameデータ準備
        df_data = []
        for patent in patents:
            # 企業名の処理（改善版）
            assignees = []
            if 'assignees' in patent:
                for assignee in patent['assignees']:
                    org = assignee.get('assignee_organization', '')
                    if org:
                        normalized_org = self.normalize_company_name_improved(org)
                        assignees.append(normalized_org)
            
            df_data.append({
                'patent_number': patent.get('patent_number', ''),
                'patent_title': patent.get('patent_title', ''),
                'patent_date': patent.get('patent_date', ''),
                'assignee_organization': '; '.join(assignees) if assignees else '不明',
                'filing_year': None  # 後で計算
            })
        
        # DataFrame作成
        df = pd.DataFrame(df_data)
        
        if df.empty:
            return None
        
        # 日付処理（改善版）
        try:
            df['patent_date'] = pd.to_datetime(df['patent_date'], errors='coerce')
            df = df.dropna(subset=['patent_date'])
            df['filing_year'] = df['patent_date'].dt.year
            df = df.sort_values('patent_date', ascending=False)
            
            self.logger.info(f"処理完了: {len(df)}行")
            return df
            
        except Exception as e:
            self.logger.error(f"データ処理エラー: {e}")
            return None

    # === 新規追加: 改善された企業名正規化 ===
    def normalize_company_name_improved(self, assignee: str) -> str:
        """改善された企業名正規化"""
        if not assignee:
            return "不明"
        
        # クリーニング
        assignee_clean = assignee.strip()
        assignee_lower = assignee_clean.lower()
        
        # 改善されたマッピング適用
        for key, normalized in self.enhanced_company_mapping.items():
            if key in assignee_lower:
                return normalized
        
        return assignee_clean

    # === 既存メソッドの安全な置き換え ===
    def search_patents_api(self, limit=100):
        """既存メソッド（改善版を呼び出すように変更）"""
        
        # オプション: 新しい実装を使用するかチェック
        use_improved = getattr(self, '_use_improved_api', True)
        
        if use_improved:
            try:
                result = self.search_patents_api_improved(limit)
                if result is not None:
                    return result
            except Exception as e:
                st.warning(f"改善版API実行中にエラー: {e}")
        
        # 元の実装にフォールバック（既存コードをここに維持）
        try:
            url = "https://api.patentsview.org/patents/query"
            query = {
                "q": {
                    "_or": [
                        {"assignee_organization": "Applied Materials"},
                        {"assignee_organization": "Tokyo Electron"},
                        {"assignee_organization": "KYOCERA"}
                    ]
                },
                "f": ["patent_number", "patent_title", "patent_date", "assignee_organization"],
                "s": [{"patent_date": "desc"}],
                "o": {"per_page": limit}
            }
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=query, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return self._process_api_response(response.json())
            else:
                return None
        except Exception as e:
            return None

    # 既存の_process_api_response()メソッドもそのまま保持...

# 段階的実装手順

## ステップ1: 既存ファイルのバックアップ

```bash
# プロジェクトフォルダで実行
cp dual_patent_connector.py dual_patent_connector_backup.py
```

## ステップ2: 既存の`__init__`メソッドに追加

既存の`DualPatentConnector`クラスの`__init__`メソッドの**最後に**以下を追加：

```python
def __init__(self):
    # 既存のコード...
    self.bigquery_client = None
    self.is_bigquery_connected = False
    
    # === ここから追加 ===
    # セッション設定
    self.session = requests.Session()
    self.session.headers.update({
        "Content-Type": "application/json",
        "User-Agent": "FusionPatentSearch/1.0 (Academic Research)"
    })
    
    # ログ設定
    import logging
    logging.basicConfig(level=logging.INFO)
    self.logger = logging.getLogger(__name__)
    
    # 改善された企業名マッピング
    self.enhanced_company_mapping = {
        'applied materials': 'Applied Materials',
        'applied materials inc': 'Applied Materials',
        'tokyo electron': '東京エレクトロン',
        'tokyo electron limited': '東京エレクトロン',
        'kyocera': '京セラ',
        'kyocera corporation': '京セラ',
        'toto': 'TOTO',
        'toto ltd': 'TOTO',
        'ngk insulators': '日本ガイシ',
        'lam research': 'Lam Research',
        'entegris': 'Entegris'
    }
```

## ステップ3: 新しいメソッドを追加

既存クラスの**最後に**以下のメソッドを追加：

```python
    def test_api_connection(self):
        """API接続テスト（新規追加）"""
        try:
            test_query = {
                "q": {"patent_number": "999999999"},
                "f": ["patent_number"],
                "o": {"per_page": 1}
            }
            
            response = self.session.post(
                "https://api.patentsview.org/patents/query",
                json=test_query,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'patents' in data:
                    self.logger.info("API接続テスト成功")
                    return True
            
            self.logger.warning(f"API接続テスト失敗: {response.status_code}")
            return False
            
        except Exception as e:
            self.logger.error(f"API接続テストエラー: {e}")
            return False
```

## ステップ4: `streamlit_app.py`に診断機能追加

メインアプリの適切な場所（サイドバーなど）に以下を追加：

```python
# サイドバーに診断セクション追加
with st.sidebar:
    st.markdown("### 🔧 診断ツール")
    
    if st.button("API接続テスト"):
        connector = DualPatentConnector()
        with st.spinner("接続テスト中..."):
            if connector.test_api_connection():
                st.success("✅ API接続成功")
            else:
                st.error("❌ API接続失敗")
```

## ステップ5: ローカルテスト

```bash
# ローカル環境で実行
streamlit run streamlit_app.py
```

1. アプリが正常に起動するか確認
2. サイドバーの「API接続テスト」ボタンをクリック
3. 結果を確認

## ステップ6: 結果に応じた次のアクション

### ✅ 接続テストが成功した場合
→ ステップ7に進む（既存メソッドの改善）

### ❌ 接続テストが失敗した場合  
→ 問題を特定して対処：

1. **ネットワーク問題**: ファイアウォール、プロキシ設定確認
2. **API制限**: レート制限に達している可能性
3. **CORS問題**: ブラウザからの直接アクセス制限

## ステップ7: 段階的な機能改善（成功時のみ）

接続テストが成功した場合、既存の`search_patents_api`メソッドを安全に改善：

```python
def search_patents_api(self, limit=100):
    """既存メソッドの安全な改善"""
    
    # 接続テストを最初に実行
    if not self.test_api_connection():
        st.warning("⚠️ API接続に問題があります")
        return None
    
    # 既存のクエリ実行（タイムアウトを延長）
    try:
        url = "https://api.patentsview.org/patents/query"
        query = {
            "q": {
                "_or": [
                    {"assignee_organization": "Applied Materials"},
                    {"assignee_organization": "Tokyo Electron"},
                    {"assignee_organization": "KYOCERA"}
                ]
            },
            "f": ["patent_number", "patent_title", "patent_date", "assignee_organization"],
            "s": [{"patent_date": "desc"}],
            "o": {"per_page": limit}
        }
        headers = {"Content-Type": "application/json"}
        
        # タイムアウトを30秒→60秒に延長
        response = self.session.post(url, json=query, headers=headers, timeout=60)
        
        if response.status_code == 200:
            return self._process_api_response(response.json())
        else:
            st.error(f"API エラー: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"API 実行エラー: {e}")
        return None
```

## 緊急時の復旧手順

問題が発生した場合：

```bash
# バックアップから復旧
cp dual_patent_connector_backup.py dual_patent_connector.py

# アプリ再起動で確認
streamlit run streamlit_app.py
```

## 次回の作業予定

ステップ1-4が成功したら、次回は：
- より高度なエラーハンドリング
- リトライ機能の追加
- クエリの最適化

---

**重要な注意点**:
- 各ステップ後に必ずテストしてください
- エラーが発生したら即座にバックアップに戻してください
- 一度に大きな変更を加えず、段階的に進めてください
