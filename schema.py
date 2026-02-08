from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List

# Excel列名 → 内部キーのマッピング
STD_COLS = {
    "id": "No",
    "age_band": "年代（資料請求時）",
    "revenue": "売上金額",
    "sales_owner": "営業担当者(別名)",
    "conv_date": "Pardot コンバージョン日",
    "lead_source": "リードソース",
    "trigger": "資料請求のきっかけ",
    "utm_source": "utm_source",
    "utm_medium": "utm_medium",
    "utm_content": "utm_content",
    "utm_campaign": "utm_campaign",
    "assets_band": "純 金融資産",
    "stage": "リード進捗",
    "origin": "集客起点",
}

ASSET_ORDER = [
    "2000万円未満",
    "5000万円未満",
    "1億円未満",
    "5億円未満",
    "5億円以上",
    "不明",
]

AGE_ORDER = [
    "20代",
    "30代",
    "40代",
    "50代",
    "60代",
    "70∼74歳",
    "75歳以上",
    "不明",
]

CONTRIB_COL_CANDIDATES = [
    "YDA_新規獲得キャンペーン貢献",
    "Pmax貢献",
    "リスティング貢献",
    "オーガニック貢献",
    "コラム貢献",
    "Google広告貢献",
    "Yahoo!広告貢献",
    "facebook貢献",
    "Microsoft広告貢献",
    "ヘッジファンドキャンペーン貢献",
    "資産運用キャンペーン貢献",
    "社名キャンペーン貢献",
    "リマケキャンペーン貢献",
    "1Mドル訴求キャンペーン",
]


@dataclass(frozen=True)
class ColumnMap:
    mapping: Dict[str, str]

    @staticmethod
    def default_from_df_columns(cols: List[str]) -> "ColumnMap":
        m = {}
        for internal, excel_name in STD_COLS.items():
            if excel_name in cols:
                m[internal] = excel_name
        return ColumnMap(mapping=m)
