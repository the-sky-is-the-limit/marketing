# Marketing Funnel Analyzer

資料請求 → Qualified（面談済） → 成約（売上あり）のファネルを多角的に分析するStreamlitアプリ

## セットアップ

```bash
cd marketing_app
pip install -r requirements.txt
streamlit run app.py
```

## 構成

```
marketing_app/
├── app.py                  # メインアプリ（タブルーティング）
├── requirements.txt
├── logic/
│   ├── schema.py           # 列名定義・カテゴリ順序
│   ├── preprocess.py       # データ整備・派生列生成
│   ├── metrics.py          # ファネルKPI計算
│   ├── attribution.py      # チャネル/キャンペーン集計
│   └── modeling.py         # GBMによる特徴量重要度
└── ui/
    ├── tab_data.py         # Tab A: データ取り込み
    ├── tab_funnel.py       # Tab B: ファネル健康診断
    ├── tab_segment.py      # Tab C: 年代×資産マトリクス
    ├── tab_channel.py      # Tab D: チャネル/キャンペーン比較
    └── tab_model.py        # Tab E: 要因推定（GBM）
```

## 5タブの使い方

| タブ | 目的 | 意思決定 |
|------|------|----------|
| Data | Excel取り込み・列マッピング | データ品質の確認 |
| Funnel | 全体/月次/担当者別ファネル | ボトルネック特定 |
| Segment | 年代×資産のマトリクス | 勝ち筋セグメント発見 |
| Channel | UTM・貢献フラグの上流/下流比較 | 予算配分の判断 |
| Drivers | GBMによる特徴量重要度 | 交絡の検証・因果推定 |

## データ要件

Excelファイル（.xlsx）で以下の列が必要：
- `売上金額`（成約=金額あり、未成約=0）
- `リード進捗`（Qualified=面談済）
- `Pardot コンバージョン日`
- `年代（資料請求時）`
- `純 金融資産`
- `utm_source` / `utm_campaign` 等
- 各種貢献フラグ（TRUE/FALSE）
