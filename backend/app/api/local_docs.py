"""A self-contained API reference; no Swagger/ReDoc CDN or external assets."""
from html import escape

def render_api_reference(schema):
    rows = []
    for path, operations in schema["paths"].items():
        for method, operation in operations.items():
            if method not in {"get", "post", "put", "delete", "patch", "head", "options"}:
                continue
            rows.append(
                "<tr><td><strong>" + escape(method.upper()) + "</strong></td>"
                "<td><code>" + escape(path) + "</code></td>"
                "<td>" + escape(operation.get("summary", "")) + "</td></tr>"
            )
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DataMap Studio — local API reference</title>
<style>
body{font:15px/1.6 system-ui,sans-serif;max-width:1050px;margin:40px auto;padding:0 24px;color:#243536;background:#f6f7f8}
h1{color:#225c53}a{color:#225c53}table{border-collapse:collapse;width:100%;background:white}
th,td{text-align:left;padding:12px;border-bottom:1px solid #dce3e1}th{background:#e9efe2}
code{overflow-wrap:anywhere}p{margin:18px 0}.table{overflow:auto}
</style></head><body><a href="/">Back to DataMap Studio</a>
<h1>Local API reference</h1><p>This reference and all application assets are served from this computer.
No internet connection, CDN, cloud service or account is required.</p>
<p><a href="/openapi.json">Open the complete OpenAPI schema (local JSON)</a></p>
<div class="table"><table><thead><tr><th>Method</th><th>Path</th><th>Purpose</th></tr></thead>
<tbody>""" + "".join(rows) + "</tbody></table></div></body></html>"
