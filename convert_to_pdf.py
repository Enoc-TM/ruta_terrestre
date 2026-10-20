import os
import subprocess
import markdown
import shutil

downloads_dir = os.path.expanduser(r"~\Downloads")
project_dir = r"c:\Users\USUARIO\3D Objects\optiruta_transporte"
edge_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

files_to_convert = [
    {
        "source_md": os.path.join(project_dir, "EXPLICACION_PASO_A_PASO.md"),
        "target_pdf": os.path.join(downloads_dir, "EXPLICACION_PASO_A_PASO.pdf"),
        "target_md": os.path.join(downloads_dir, "EXPLICACION_PASO_A_PASO.md"),
        "title": "Explicación Paso a Paso del Código — TransLogística Express Ibagué"
    },
    {
        "source_md": os.path.join(project_dir, "GUIA_SUSTENTACION.md"),
        "target_pdf": os.path.join(downloads_dir, "GUIA_SUSTENTACION.pdf"),
        "target_md": os.path.join(downloads_dir, "GUIA_SUSTENTACION.md"),
        "title": "Guía de Sustentación Académica — Optimización de Rutas y Carga Ibagué"
    }
]

CSS_STYLE = """
@page {
    size: A4;
    margin: 18mm 16mm 18mm 16mm;
}
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.55;
    color: #1f2937;
    background-color: #ffffff;
    font-size: 10pt;
}
h1 {
    color: #1e3a8a;
    font-size: 19pt;
    border-bottom: 2px solid #3b82f6;
    padding-bottom: 6px;
    margin-top: 0;
    margin-bottom: 12px;
}
h2 {
    color: #1e40af;
    font-size: 13.5pt;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 4px;
    margin-top: 18px;
    margin-bottom: 8px;
    page-break-after: avoid;
}
h3 {
    color: #1d4ed8;
    font-size: 11.5pt;
    margin-top: 14px;
    margin-bottom: 6px;
    page-break-after: avoid;
}
h4 {
    color: #2563eb;
    font-size: 10.5pt;
    margin-top: 10px;
    margin-bottom: 4px;
    page-break-after: avoid;
}
p {
    margin-top: 0;
    margin-bottom: 8px;
}
ul, ol {
    margin-top: 0;
    margin-bottom: 8px;
    padding-left: 22px;
}
li {
    margin-bottom: 4px;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
    margin-bottom: 14px;
    font-size: 8.8pt;
    page-break-inside: avoid;
}
th, td {
    border: 1px solid #cbd5e1;
    padding: 6px 8px;
    text-align: left;
}
th {
    background-color: #1e293b;
    color: #ffffff;
    font-weight: 600;
}
tr:nth-child(even) {
    background-color: #f8fafc;
}
code {
    font-family: Consolas, "Courier New", monospace;
    background-color: #f1f5f9;
    color: #b91c1c;
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 9pt;
}
pre {
    background-color: #0f172a;
    color: #f8fafc;
    padding: 10px 14px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 8.5pt;
    line-height: 1.4;
    page-break-inside: avoid;
    margin-top: 8px;
    margin-bottom: 12px;
}
pre code {
    background-color: transparent;
    color: #e2e8f0;
    padding: 0;
    font-size: inherit;
}
blockquote {
    margin: 10px 0;
    padding: 8px 14px;
    background-color: #eff6ff;
    border-left: 4px solid #3b82f6;
    color: #1e40af;
    font-style: italic;
    page-break-inside: avoid;
}
hr {
    border: 0;
    border-top: 1px solid #e2e8f0;
    margin: 16px 0;
}
.header-badge {
    display: inline-block;
    background-color: #2563eb;
    color: white;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 8.5pt;
    font-weight: bold;
    margin-bottom: 10px;
}
"""

for item in files_to_convert:
    print(f"\nProcesando: {item['source_md']}")
    with open(item["source_md"], "r", encoding="utf-8") as f:
        md_content = f.read()

    html_body = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>{item['title']}</title>
    <style>
{CSS_STYLE}
    </style>
</head>
<body>
    <div class="header-badge">TransLogística Express — Ibagué (Tolima)</div>
    {html_body}
</body>
</html>"""

    temp_html = item["source_md"].replace(".md", "_temp.html")
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(full_html)

    target_pdf = item["target_pdf"]
    cmd = [
        edge_exe,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={target_pdf}",
        temp_html
    ]

    print(f"Generando PDF: {target_pdf}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(target_pdf) and os.path.getsize(target_pdf) > 0:
        print(f"PDF generado: {target_pdf} ({os.path.getsize(target_pdf)/1024:.1f} KB)")
    else:
        print(f"Error PDF: {res.stderr}")

    shutil.copy2(item["source_md"], item["target_md"])
    print(f"Markdown copiado: {item['target_md']}")

    if os.path.exists(temp_html):
        os.remove(temp_html)

print("\nConversion a PDF completada.")
