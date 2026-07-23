import os
import subprocess
import markdown

def main():
    md_file = 'slides_presentasi.md'
    html_file = 'slides_presentasi.html'
    pdf_file = 'slides_presentasi.pdf'

    if not os.path.exists(md_file):
        print(f"Error: {md_file} tidak ditemukan!")
        return

    print("Membaca slides_presentasi.md...")
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Pisahkan slide berdasarkan pemisah '---'
    slides_md = md_content.split('\n---\n')
    
    slides_html = []
    for i, slide in enumerate(slides_md):
        # Bersihkan spasi kosong di awal/akhir
        slide = slide.strip()
        if not slide:
            continue
        
        # Konversi markdown slide ke html
        slide_html = markdown.markdown(slide, extensions=['extra'])
        
        # Bungkus ke dalam kelas slide untuk page-break
        slides_html.append(f'<div class="slide" id="slide-{i+1}">{slide_html}</div>')

    full_slides_html = "\n\n".join(slides_html)

    # Buat HTML terbungkus CSS premium untuk presentasi landscape (A4 Landscape / 16:9)
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>SBDT POS - Slide Presentasi</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        @page {{
            size: 297mm 167mm; /* Rasio 16:9 Landscape */
            margin: 1.5cm 2cm;
            @bottom-right {{
                content: counter(page);
                font-family: 'Inter', sans-serif;
                font-size: 0.8rem;
                color: #a0aec0;
            }}
            @bottom-left {{
                content: "SBDT POS Terdistribusi - Tugas Akhir";
                font-family: 'Inter', sans-serif;
                font-size: 0.8rem;
                color: #a0aec0;
            }}
        }}

        body {{
            font-family: 'Inter', sans-serif;
            color: #1a202c;
            background-color: #ffffff;
            line-height: 1.5;
            margin: 0;
            padding: 0;
            font-size: 15px;
        }}

        .slide {{
            page-break-after: always;
            box-sizing: border-box;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }}

        /* Slide Cover */
        #slide-1 {{
            justify-content: center;
            align-items: center;
            text-align: center;
            height: 100%;
            padding-top: 1.5cm;
        }}
        #slide-1 h1 {{
            font-size: 2.4rem;
            font-weight: 800;
            color: #4f46e5;
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }}
        #slide-1 p {{
            font-size: 1.2rem;
            color: #4a5568;
            margin-top: 0.5rem;
            margin-bottom: 1.5rem;
        }}
        #slide-1 ul {{
            list-style: none;
            padding: 0;
            margin: 0;
            font-size: 1rem;
            color: #718096;
        }}
        #slide-1 li {{
            margin-bottom: 0.35rem;
        }}

        h1, h2, h3 {{
            color: #1a202c;
            margin-top: 0;
        }}

        h2 {{
            font-size: 1.8rem;
            font-weight: 800;
            color: #4f46e5;
            border-bottom: 2px solid #edf2f7;
            padding-bottom: 0.5rem;
            margin-bottom: 1.2rem;
        }}

        p, li {{
            font-size: 1.05rem;
            color: #2d3748;
        }}

        ul, ol {{
            margin-top: 0.5rem;
            margin-bottom: 1rem;
            padding-left: 1.5rem;
        }}

        li {{
            margin-bottom: 0.5rem;
        }}

        strong {{
            color: #1a202c;
            font-weight: 600;
        }}

        /* Blockquote untuk Catatan Pembicara */
        blockquote {{
            margin-top: auto; /* Tarik catatan pembicara ke bawah slide */
            margin-left: 0;
            margin-right: 0;
            padding: 0.75rem 1rem;
            background-color: #f7fafc;
            border-left: 4px solid #a0aec0;
            border-radius: 4px;
            font-size: 0.85rem;
            color: #4a5568;
            box-sizing: border-box;
        }}
        blockquote p {{
            font-size: 0.85rem;
            color: #4a5568;
            margin: 0;
        }}

        /* Styling tabel topologi */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 0.5rem;
            margin-bottom: 1rem;
        }}
        th, td {{
            padding: 0.6rem 0.8rem;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
            font-size: 0.95rem;
        }}
        th {{
            background-color: #f8fafc;
            color: #4a5568;
            font-weight: 700;
        }}

        /* Kode & Badge */
        code {{
            font-family: 'Courier New', monospace;
            background-color: #edf2f7;
            padding: 0.15rem 0.35rem;
            border-radius: 3px;
            font-size: 0.9rem;
            color: #c53030;
        }}
        
        pre {{
            background-color: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 0.75rem;
            overflow: auto;
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
            color: #2d3748;
        }}
    </style>
</head>
<body>
    {full_slides_html}
</body>
</html>
"""

    print(f"Menulis file HTML sementara {html_file}...")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_template)

    print("Mengonversi HTML ke PDF menggunakan WeasyPrint...")
    try:
        subprocess.run(['weasyprint', html_file, pdf_file], check=True)
        print(f"\n🎉 Berhasil! Slide presentasi disimpan di: {pdf_file}")
    except Exception as e:
        print(f"Error saat menjalankan WeasyPrint: {e}")
    finally:
        # Hapus file HTML sementara
        if os.path.exists(html_file):
            os.remove(html_file)

if __name__ == '__main__':
    main()
