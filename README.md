# 🔍 FusionPatentSearch
**ESC特許分析システム - 東京科学大学 齊藤滋規教授プロジェクト**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://fusionpatentsearch-titech.streamlit.app)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 プロジェクト概要

**FusionPatentSearch** は、曲面ESC（Electronic Speed Controller）技術に特化した包括的な特許分析システムです。FUSIONDRIVER INCが開発し、東京科学大学 齊藤滋規教授との産学連携プロジェクト（KSPプロジェクト）として進められています。

### 🎯 開発背景・目的
- **コスト削減**: 5万円/回の外部サービス → 完全無料の自社システム
- **機能向上**: 静的PDFレポート → インタラクティブWebアプリケーション
- **継続性**: 一度きりの調査 → リアルタイム自動更新
- **カスタマイズ**: 汎用分析 → 17社特化の詳細分析

### 🏢 対象企業・技術
**日本企業（9社）**: 新光電気工業、TOTO、住友大阪セメント、京セラ、日本ガイシ、NTKセラテック、筑波精工、クリエイティブテクノロジー、東京エレクトロン

**海外企業（8社）**: Applied Materials、Lam Research、Entegris、FM Industries、MiCo、SEMCO Engineering、Calitech、Beijing U-Precision

---

## ✨ 主要機能

### 📊 概要分析
- **KPI指標**: 総特許数、企業数、対象期間、日本企業特許数
- **年次推移グラフ**: 2010-2024年の特許出願動向
- **企業別ランキング**: TOP10企業の特許保有数
- **地域別比較**: 日本 vs 海外企業の比較分析

### 🏢 企業別詳細分析
- **企業情報カード**: 基本統計情報とメタデータ
- **年次推移分析**: 選択企業の出願動向
- **技術カテゴリ分布**: 企業の技術領域分析
- **最新特許リスト**: 直近の特許出願一覧

### 🔬 技術トレンド分析
- **キーワード分析**: ESC関連技術の頻出キーワード
- **ワードクラウド**: 視覚的なキーワード分布
- **技術カテゴリトレンド**: 年度別技術分野の推移
- **多言語対応**: 日英両言語での検索・分析

### ⚔️ 競合比較分析
- **日本 vs 海外比較**: 地域別競合状況
- **企業×年度ヒートマップ**: 活動パターンの可視化
- **ランキング分析**: 地域別・技術別ランキング

### ⏰ タイムライン分析
- **期間フィルタリング**: 年度スライダーによる動的絞り込み
- **企業別推移比較**: 複数企業の同時比較
- **統計指標**: 期間別の詳細統計情報

---

## 🚀 デモアプリ

**ライブデモ**: [https://fusionpatentsearch-titech.streamlit.app](https://fusionpatentsearch-titech.streamlit.app)

### 📸 スクリーンショット

#### 概要分析ダッシュボード
*年次推移、企業ランキング、地域別分析が一目で把握可能*

#### 企業別詳細分析
*選択企業の包括的な特許ポートフォリオ分析*

#### 技術トレンド分析
*キーワード分析とワードクラウドによる技術動向把握*

#### 競合比較分析
*ヒートマップによる企業間競合状況の可視化*

---

## 🛠 技術仕様

### アーキテクチャ
```
Google Patents BigQuery → Python分析 → Streamlit UI → ユーザー
```

### 技術スタック
- **フロントエンド**: Streamlit (Webアプリケーション)
- **バックエンド**: Python 3.9+
- **データベース**: Google Patents BigQuery
- **可視化**: Plotly, Matplotlib, Seaborn
- **自然言語処理**: scikit-learn, NLTK, WordCloud
- **クラウド**: Streamlit Cloud, GitHub Actions
- **バージョン管理**: Git + GitHub

### 主要ライブラリ
```python
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.21.0
matplotlib>=3.5.0
seaborn>=0.11.0
plotly>=5.10.0
google-cloud-bigquery>=3.4.0
scikit-learn>=1.3.0
wordcloud>=1.9.0
networkx>=3.1
```

---

## 🏗 インストール・セットアップ

### 前提条件
- Python 3.9以上
- Git
- Google Cloud アカウント（BigQuery使用時）

### ローカル環境での実行

1. **リポジトリのクローン**
```bash
git clone https://github.com/koji276/FusionPatentSearch.git
cd FusionPatentSearch
```

2. **仮想環境の作成・有効化**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **依存関係のインストール**
```bash
pip install -r requirements.txt
```

4. **アプリケーションの起動**
```bash
streamlit run streamlit_app.py
```

5. **ブラウザでアクセス**
```
http://localhost:8501
```

### Google BigQuery設定（オプション）

実際の特許データにアクセスするには：

1. **Google Cloud プロジェクトの作成**
2. **BigQuery APIの有効化**
3. **サービスアカウントの作成と認証キー取得**
4. **Streamlit Secretsの設定**

```toml
# .streamlit/secrets.toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "service-account@your-project.iam.gserviceaccount.com"
client_id = "client-id"
```

---

## 📁 プロジェクト構造

```
FusionPatentSearch/
├── .github/workflows/       # GitHub Actions CI/CD
├── .streamlit/             # Streamlit設定
├── config/                 # 設定ファイル
├── data/                   # データキャッシュ
├── assets/                 # 静的アセット
├── docs/                   # ドキュメント
├── streamlit_app.py        # メインアプリケーション
├── requirements.txt        # Python依存関係
├── README.md              # プロジェクト説明
└── .gitignore             # Git除外設定
```

---

## 🔍 使用方法

### 1. 分析タイプの選択
サイドバーから以下の分析タイプを選択：
- **概要分析**: 全体的な特許動向の把握
- **企業別詳細分析**: 特定企業の詳細分析
- **技術トレンド分析**: 技術キーワードとトレンド
- **競合比較分析**: 企業間・地域間比較
- **タイムライン分析**: 時系列での詳細分析

### 2. データソースの選択
- **デモデータ**: 即座にシステムを体験
- **BigQueryデータ**: 実際の特許データベース（要設定）

### 3. フィルタリングとカスタマイズ
- 企業選択
- 期間指定
- 技術カテゴリフィルタ

---

## 📈 期待される成果・ビジネス価値

### 即座の効果
- ✅ **コスト削減**: 5万円/回 → 0円
- ✅ **速度向上**: 1週間 → リアルタイム
- ✅ **カスタマイズ**: 汎用 → 17社特化
- ✅ **アクセス性**: PDF → Webアプリ

### 中期的利益
- 📈 **競合分析精度向上**: リアルタイム動向把握
- 🎯 **R&D戦略最適化**: データドリブンな開発方針決定
- 🤝 **産学連携促進**: 大学研究機関との協業機会発見
- 💰 **事業機会創出**: 未開拓技術領域の特定

### 長期的ビジョン
- 🚀 **技術プラットフォーム化**: 他技術分野への横展開
- 🌍 **グローバル展開**: 海外市場分析への応用
- 🏛 **アカデミックブランド**: 大学発プロジェクトとしての価値向上
- 💼 **新規事業創出**: 特許分析SaaSとしての事業化可能性

---

## 🤝 開発チーム・連携

### 開発・運営
- **FUSIONDRIVER INC** - システム開発・運営
- **プロジェクト**: KSPプロジェクト

### 学術連携
- **東京科学大学** 材料プロセス工学研究室
- **齊藤滋規教授** - プロジェクト指導・学術監修

### 技術サポート
- **GitHub**: [koji276/FusionPatentSearch](https://github.com/koji276/FusionPatentSearch)
- **Issues**: バグレポート・機能リクエスト

---

## 🔮 ロードマップ

### Phase 4: 中期計画（3-6ヶ月）
- [ ] AI機能統合（特許トレンド予測）
- [ ] 多言語・国際対応
- [ ] モバイル対応強化
- [ ] データエクスポート機能

### Phase 5: 長期ビジョン（6ヶ月-1年）
- [ ] 学術研究支援機能
- [ ] 事業化準備（SaaS化）
- [ ] 他技術分野への横展開
- [ ] 国際連携プロジェクト

---

## 📄 ライセンス

```
MIT License

Copyright (c) 2024 FUSIONDRIVER INC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📧 コンタクト

### 学術関連
- **齊藤滋規教授** - [saito@titech.ac.jp](mailto:saito@titech.ac.jp)
- **東京科学大学** 材料プロセス工学研究室

### 技術・開発関連
- **GitHub Issues**: [https://github.com/koji276/FusionPatentSearch/issues](https://github.com/koji276/FusionPatentSearch/issues)
- **開発者**: koji276

---

<div align="center">

**🔬 FusionPatentSearch - Transforming Patent Analysis with Innovation**

*Developed by FUSIONDRIVER INC | KSPプロジェクト | 東京科学大学 産学連携*

</div>