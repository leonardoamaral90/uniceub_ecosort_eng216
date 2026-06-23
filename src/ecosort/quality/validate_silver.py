from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import great_expectations as ge
import pandas as pd

from ecosort.class_map import EXPECTED_CLASSES
from ecosort.config import Settings, get_settings


def validate_silver_candidate(settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    candidate_dir = settings.silver_dir / "_candidate" / "residuos"
    if not candidate_dir.exists():
        raise RuntimeError("Silver candidate não encontrada para validação.")

    df = pd.read_parquet(candidate_dir)
    if df.empty:
        raise RuntimeError("Silver candidate está vazia.")

    ge_df = ge.from_pandas(df)
    results = []
    results.append(ge_df.expect_column_values_to_not_be_null("image_id"))
    results.append(ge_df.expect_column_values_to_not_be_null("class_label"))
    results.append(ge_df.expect_column_values_to_not_be_null("recyclable"))
    results.append(ge_df.expect_column_values_to_be_in_set("class_label_normalized", sorted(EXPECTED_CLASSES)))
    results.append(ge_df.expect_column_values_to_be_of_type("recyclable", "bool"))
    results.append(ge_df.expect_column_values_to_be_between("confidence", min_value=0.0, max_value=1.0))

    success = all(bool(r.success) for r in results)
    validation_payload = {
        "success": success,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "records": len(df),
        "expectations": [r.to_json_dict() for r in results],
    }

    docs_dir = settings.ge_docs_dir
    docs_dir.mkdir(parents=True, exist_ok=True)
    json_path = docs_dir / "validation_result.json"
    html_path = docs_dir / "index.html"
    json_path.write_text(json.dumps(validation_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    html_path.write_text(_render_html(validation_payload), encoding="utf-8")

    if not success:
        raise RuntimeError(f"Great Expectations falhou. Consulte {html_path}")

    print(f"[ge] Validação concluída com sucesso. Data Docs: {html_path}")
    return {"success": success, "records": len(df), "docs": str(html_path)}


def _render_html(payload: dict) -> str:
    rows = []
    for item in payload["expectations"]:
        rows.append(
            "<tr>"
            f"<td>{item.get('expectation_config', {}).get('expectation_type')}</td>"
            f"<td>{'✅' if item.get('success') else '❌'}</td>"
            f"<td><pre>{json.dumps(item.get('result', {}), ensure_ascii=False, indent=2)}</pre></td>"
            "</tr>"
        )
    status = "✅ SUCESSO" if payload["success"] else "❌ FALHA"
    return f"""
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>EcoSort — Great Expectations Data Docs</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2937; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 10px; vertical-align: top; }}
    th {{ background: #f3f4f6; }}
    pre {{ white-space: pre-wrap; margin: 0; }}
    .status {{ font-size: 24px; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>EcoSort — Great Expectations Data Docs</h1>
  <p class="status">{status}</p>
  <p><strong>Validado em:</strong> {payload['validated_at']}</p>
  <p><strong>Registros:</strong> {payload['records']}</p>
  <table>
    <thead><tr><th>Expectativa</th><th>Status</th><th>Resultado</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""


if __name__ == "__main__":
    print(validate_silver_candidate())
