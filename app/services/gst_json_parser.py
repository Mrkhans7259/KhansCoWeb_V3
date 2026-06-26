import json


def parse_gst_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return_type = data.get("return_type", "Unknown")

    summary = {
        "return_type": return_type,
        "gstin": data.get("gstin", "-"),
        "legal_name": data.get("legal_name", "-"),
        "trade_name": data.get("trade_name", "-"),
        "financial_year": data.get("financial_year", "-"),
        "period": data.get("period", "-"),
        "invoice_count": 0,
        "taxable_value": 0,
        "igst": 0,
        "cgst": 0,
        "sgst": 0,
        "cess": 0,
        "status": data.get("status", "parsed"),
        "arn": data.get("arn", "-"),
        "filing_date": data.get("filing_date", "-"),
        "raw_keys": list(data.keys()) if isinstance(data, dict) else []
    }

    if return_type == "GSTR-1":
        sections = ["b2b", "b2c", "b2cl", "b2cs", "cdnr", "cdnur", "exp"]

        for section in sections:
            rows = data.get(section, [])
            if isinstance(rows, list):
                summary["invoice_count"] += len(rows)

                for row in rows:
                    summary["taxable_value"] += float(row.get("taxable_value", 0) or 0)
                    summary["igst"] += float(row.get("igst", 0) or 0)
                    summary["cgst"] += float(row.get("cgst", 0) or 0)
                    summary["sgst"] += float(row.get("sgst", 0) or 0)
                    summary["cess"] += float(row.get("cess", 0) or 0)

    elif return_type == "GSTR-3B":
        summary["invoice_count"] = "-"
        summary["taxable_value"] = float(data.get("outward_taxable_value", 0) or 0)
        summary["igst"] = float(data.get("igst", 0) or 0)
        summary["cgst"] = float(data.get("cgst", 0) or 0)
        summary["sgst"] = float(data.get("sgst", 0) or 0)
        summary["cess"] = float(data.get("cess", 0) or 0)

    return summary
