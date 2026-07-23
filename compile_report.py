import os
import subprocess
import markdown

def main():
    md_file = 'laporan_tugas_akhir.md'
    html_file = 'laporan_tugas_akhir.html'
    pdf_file = 'laporan_tugas_akhir.pdf'

    if not os.path.exists(md_file):
        print(f"Error: {md_file} tidak ditemukan!")
        return

    print("Membaca laporan_tugas_akhir.md...")
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Pisahkan bab berdasarkan pemisah '---' (untuk cover, pengesahan, kata pengantar, abstrak)
    sections_md = md_content.split('\n---\n')
    
    sections_html = []
    for i, sec in enumerate(sections_md):
        sec = sec.strip()
        if not sec:
            continue
        
        # Konversi markdown ke html
        sec_html = markdown.markdown(sec, extensions=['extra'])
        
        # Bungkus ke dalam section untuk format page break
        if i == 0:
            # Halaman Sampul / Cover
            sections_html.append(f'<div class="cover-page">{sec_html}</div>')
        else:
            sections_html.append(f'<div class="report-page">{sec_html}</div>')

    full_html = "\n\n".join(sections_html)

    # Buat HTML terbungkus CSS formal standar Skripsi Indonesia (A4 Portrait, TNR, Margin 4 4 3 3)
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Laporan Tugas Akhir - SBDT POS</title>
    <style>
        @page {{
            size: A4 portrait;
            margin-top: 3cm;
            margin-bottom: 3cm;
            margin-right: 3cm;
            margin-left: 4cm; /* Margin kiri 4cm untuk penjilidan skripsi */
            @bottom-center {{
                content: counter(page);
                font-family: 'Times New Roman', Times, serif;
                font-size: 11pt;
                color: #000000;
            }}
        }}

        body {{
            font-family: 'Times New Roman', Times, serif;
            color: #000000;
            line-height: 1.5; /* Spasi 1.5 standard skripsi */
            font-size: 12pt;
            text-align: justify;
        }}

        .cover-page {{
            page-break-after: always;
            text-align: center;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding-top: 1cm;
        }}

        .cover-page h1 {{
            font-size: 14pt;
            font-weight: bold;
            text-transform: uppercase;
            line-height: 1.3;
            margin-bottom: 2cm;
            text-align: center;
        }}

        .cover-page p {{
            font-size: 12pt;
            text-indent: 0;
            margin-bottom: 1.5cm;
            text-align: center;
        }}

        .cover-page strong {{
            display: block;
            font-size: 12pt;
            margin-top: 0.5cm;
            text-align: center;
        }}

        .report-page {{
            page-break-after: always;
        }}

        h1, h2, h3, h4 {{
            font-family: 'Times New Roman', Times, serif;
            color: #000000;
            font-weight: bold;
        }}

        /* Format BAB */
        h2 {{
            font-size: 14pt;
            text-transform: uppercase;
            text-align: center;
            margin-top: 1.5cm;
            margin-bottom: 0.8cm;
            page-break-before: always;
        }}

        /* Format Sub-bab */
        h3 {{
            font-size: 12pt;
            text-align: left;
            margin-top: 0.8cm;
            margin-bottom: 0.4cm;
        }}

        p {{
            text-indent: 1.2cm; /* Alinea paragraf skripsi */
            margin-top: 0;
            margin-bottom: 0.4cm;
        }}

        ul, ol {{
            margin-top: 0.2cm;
            margin-bottom: 0.4cm;
            padding-left: 1.5cm;
        }}

        li {{
            margin-bottom: 0.2cm;
            text-align: justify;
        }}

        /* Hapus indentasi paragraf setelah heading */
        h2 + p, h3 + p, h4 + p {{
            text-indent: 1.2cm;
        }}

        /* Format Tabel */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 0.5cm;
            margin-bottom: 0.5cm;
        }}
        th, td {{
            padding: 0.5rem;
            border: 1px solid #000000;
            font-size: 11pt;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
            text-align: center;
        }}

        code {{
            font-family: 'Courier New', monospace;
            background-color: #f4f4f4;
            padding: 0.1rem 0.3rem;
            border-radius: 3px;
            font-size: 10.5pt;
        }}
        
        pre {{
            background-color: #f9f9f9;
            border: 1px solid #ccc;
            padding: 0.5cm;
            overflow: auto;
            margin-bottom: 0.5cm;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}

        /* Styling Gambar Dokumentasi di PDF */
        img {{
            display: block;
            margin-left: auto;
            margin-right: auto;
            max-width: 100%;
            max-height: 9cm; /* Menjaga agar gambar pas di satu halaman A4 */
            margin-top: 0.4cm;
            margin-bottom: 0.4cm;
            border: 1px solid #000000;
        }}
    </style>
</head>
<body>
    {full_html}
</body>
</html>
"""

    print(f"Menulis file HTML sementara {html_file}...")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_template)

    print("Mengonversi HTML ke PDF menggunakan WeasyPrint...")
    try:
        subprocess.run(['weasyprint', html_file, pdf_file], check=True)
        print(f"\n🎉 Berhasil! Laporan Tugas Akhir disimpan di: {pdf_file}")
    except Exception as e:
        print(f"Error saat menjalankan WeasyPrint: {e}")
    finally:
        # Hapus file HTML sementara
        if os.path.exists(html_file):
            os.remove(html_file)

if __name__ == '__main__':
    main()
