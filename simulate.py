import sys
import os
import psycopg2
from psycopg2 import extras
import time

# Konfigurasi Koneksi Database (menggunakan port localhost karena dijalankan dari Host)
DB_CONFIGS = {
    'pusat': {
        'dbname': 'pos_pusat',
        'user': 'postgres',
        'password': 'supersecretpassword',
        'host': 'localhost',
        'port': 5431
    },
    'jkt': {
        'dbname': 'pos_jkt',
        'user': 'postgres',
        'password': 'supersecretpassword',
        'host': 'localhost',
        'port': 5433
    },
    'bdg': {
        'dbname': 'pos_bdg',
        'user': 'postgres',
        'password': 'supersecretpassword',
        'host': 'localhost',
        'port': 5434
    }
}

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_connection(db_key):
    try:
        conn = psycopg2.connect(**DB_CONFIGS[db_key])
        return conn
    except Exception as e:
        return None

def wait_for_databases():
    print(f"{Colors.OKBLUE}[1/4] Menunggu semua database siap...{Colors.ENDC}")
    for name, config in DB_CONFIGS.items():
        while True:
            conn = get_connection(name)
            if conn:
                conn.close()
                print(f"  - Database {name.upper()} : {Colors.OKGREEN}ONLINE{Colors.ENDC}")
                break
            else:
                print(f"  - Database {name.upper()} : {Colors.WARNING}WAITING...{Colors.ENDC}")
                time.sleep(2)

def execute_sql_file(db_key, file_path):
    conn = get_connection(db_key)
    if not conn:
        print(f"{Colors.FAIL}Gagal terhubung ke {db_key.upper()} untuk menjalankan SQL.{Colors.ENDC}")
        return False
    try:
        conn.autocommit = True
        cur = conn.cursor()
        with open(file_path, 'r') as f:
            sql = f.read()
        cur.execute(sql)
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"{Colors.FAIL}Error executing {file_path} on {db_key.upper()}: {e}{Colors.ENDC}")
        if conn:
            conn.close()
        return False

def setup_databases():
    wait_for_databases()
    print(f"\n{Colors.OKBLUE}[2/4] Menginisialisasi Skema Tabel...{Colors.ENDC}")
    
    # Run DDLs
    if execute_sql_file('pusat', 'sql/init-pusat.sql'):
        print(f"  - Skema db_pusat: {Colors.OKGREEN}SELESAI{Colors.ENDC}")
    if execute_sql_file('jkt', 'sql/init-cabang-jkt.sql'):
        print(f"  - Skema db_cabang_jkt: {Colors.OKGREEN}SELESAI{Colors.ENDC}")
    if execute_sql_file('bdg', 'sql/init-cabang-bdg.sql'):
        print(f"  - Skema db_cabang_bdg: {Colors.OKGREEN}SELESAI{Colors.ENDC}")

    print(f"\n{Colors.OKBLUE}[3/4] Mengatur Replikasi Logikal (Pusat -> Cabang)...{Colors.ENDC}")
    
    # Setup Subscription di Cabang Jakarta
    conn_jkt = get_connection('jkt')
    if conn_jkt:
        try:
            conn_jkt.autocommit = True
            cur = conn_jkt.cursor()
            cur.execute("SELECT 1 FROM pg_subscription WHERE subname = 'produk_sub_jkt'")
            if not cur.fetchone():
                print("  - Membuat Subscription di Cabang Jakarta...")
                cur.execute(
                    """
                    CREATE SUBSCRIPTION produk_sub_jkt 
                    CONNECTION 'host=db_pusat port=5432 user=postgres password=supersecretpassword dbname=pos_pusat' 
                    PUBLICATION produk_pub WITH (copy_data = true);
                    """
                )
                print(f"    Subscription JKT: {Colors.OKGREEN}CREATED{Colors.ENDC}")
            else:
                print(f"    Subscription JKT: {Colors.OKGREEN}ALREADY EXISTS{Colors.ENDC}")
            cur.close()
            conn_jkt.close()
        except Exception as e:
            print(f"{Colors.FAIL}Gagal membuat subscription di JKT: {e}{Colors.ENDC}")
            if conn_jkt:
                conn_jkt.close()

    # Setup Subscription di Cabang Bandung
    conn_bdg = get_connection('bdg')
    if conn_bdg:
        try:
            conn_bdg.autocommit = True
            cur = conn_bdg.cursor()
            cur.execute("SELECT 1 FROM pg_subscription WHERE subname = 'produk_sub_bdg'")
            if not cur.fetchone():
                print("  - Membuat Subscription di Cabang Bandung...")
                cur.execute(
                    """
                    CREATE SUBSCRIPTION produk_sub_bdg 
                    CONNECTION 'host=db_pusat port=5432 user=postgres password=supersecretpassword dbname=pos_pusat' 
                    PUBLICATION produk_pub WITH (copy_data = true);
                    """
                )
                print(f"    Subscription BDG: {Colors.OKGREEN}CREATED{Colors.ENDC}")
            else:
                print(f"    Subscription BDG: {Colors.OKGREEN}ALREADY EXISTS{Colors.ENDC}")
            cur.close()
            conn_bdg.close()
        except Exception as e:
            print(f"{Colors.FAIL}Gagal membuat subscription di BDG: {e}{Colors.ENDC}")
            if conn_bdg:
                conn_bdg.close()

    print(f"\n{Colors.OKGREEN}[4/4] Inisialisasi Sistem POS SBDT Selesai!{Colors.ENDC}")

def seed_products():
    print(f"{Colors.OKBLUE}Menambahkan Produk Awal di Database Pusat (HQ)...{Colors.ENDC}")
    conn = get_connection('pusat')
    if not conn:
        print(f"{Colors.FAIL}Gagal terhubung ke Database Pusat!{Colors.ENDC}")
        return
    try:
        cur = conn.cursor()
        products = [
            ("Kopi Susu Gula Aren", 18000.00, 100),
            ("Roti Bakar Cokelat", 15000.00, 50),
            ("Indomie Goreng Jumbo", 10000.00, 80),
            ("Teh Manis Hangat", 5000.00, 200)
        ]
        for p in products:
            # Cari jika sudah ada
            cur.execute("SELECT 1 FROM produk WHERE nama = %s", (p[0],))
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO produk (nama, harga, stok) VALUES (%s, %s, %s)",
                    p
                )
                print(f"  - Produk Ditambahkan: {p[0]} (Harga: Rp{p[1]:,}, Stok: {p[2]})")
            else:
                print(f"  - Produk {p[0]} sudah ada di DB Pusat.")
        conn.commit()
        cur.close()
        conn.close()
        print(f"{Colors.OKGREEN}Seeding produk selesai! Replikasi logikal akan menyebarkan data ini ke Cabang secara otomatis.{Colors.ENDC}")
    except Exception as e:
        conn.rollback()
        print(f"{Colors.FAIL}Gagal melakukan seeding produk: {e}{Colors.ENDC}")
        conn.close()

def create_transaction(branch, product_id, qty):
    if branch not in ['jkt', 'bdg']:
        print(f"{Colors.FAIL}Cabang tidak valid. Gunakan 'jkt' atau 'bdg'.{Colors.ENDC}")
        return

    conn = get_connection(branch)
    if not conn:
        print(f"{Colors.FAIL}Gagal terhubung ke Database Cabang {branch.upper()}!{Colors.ENDC}")
        return

    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        
        # 1. Dapatkan info produk dari database cabang (membuktikan replikasi katalog berhasil)
        cur.execute("SELECT id, nama, harga, stok FROM produk WHERE id = %s", (product_id,))
        product = cur.fetchone()
        
        if not product:
            print(f"{Colors.FAIL}Produk dengan ID {product_id} tidak ditemukan di database Cabang {branch.upper()}.{Colors.ENDC}")
            cur.close()
            conn.close()
            return
        
        if product['stok'] < qty:
            print(f"{Colors.WARNING}Stok tidak mencukupi. Stok saat ini: {product['stok']}, Pembelian: {qty}{Colors.ENDC}")
            cur.close()
            conn.close()
            return

        # Hitung subtotal
        subtotal = float(product['harga']) * qty
        
        # 2. Insert Transaksi Lokal
        cur.execute(
            """
            INSERT INTO transaksi (id_cabang, total_harga)
            VALUES (%s, %s) RETURNING id, waktu;
            """,
            (branch.upper(), subtotal)
        )
        tx_row = cur.fetchone()
        tx_id = tx_row['id']
        tx_waktu = tx_row['waktu']

        # 3. Insert Detail Transaksi Lokal
        cur.execute(
            """
            INSERT INTO detail_transaksi (id_transaksi, id_produk, jumlah, subtotal)
            VALUES (%s, %s, %s, %s);
            """,
            (tx_id, product_id, qty, subtotal)
        )

        # 4. Potong Stok Lokal di Cabang
        cur.execute(
            "UPDATE produk SET stok = stok - %s WHERE id = %s",
            (qty, product_id)
        )

        conn.commit()
        print(f"\n{Colors.OKGREEN}=== TRANSAKSI BERHASIL DICATAT DI CABANG {branch.upper()} ==={Colors.ENDC}")
        print(f"ID Transaksi : {tx_id}")
        print(f"Waktu        : {tx_waktu}")
        print(f"Produk       : {product['nama']} (ID: {product_id})")
        print(f"Jumlah       : {qty} x Rp{float(product['harga']):,}")
        print(f"Total        : Rp{subtotal:,}")
        print(f"Status Sync  : {Colors.WARNING}PENDING (Akan disinkronkan oleh sync_agent.py){Colors.ENDC}")
        print("===================================================\n")

        cur.close()
        conn.close()
    except Exception as e:
        conn.rollback()
        print(f"{Colors.FAIL}Transaksi gagal dibuat: {e}{Colors.ENDC}")
        conn.close()

def print_table(title, headers, rows):
    print(f"\n{Colors.BOLD}{Colors.UNDERLINE}{title}{Colors.ENDC}")
    if not rows:
        print("  (Tabel Kosong)")
        return
    
    # Calculate widths
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(str(cell)))
            
    # Format line
    border = "+" + "+".join(["-" * (w + 2) for w in widths]) + "+"
    print(border)
    print("| " + " | ".join([f"{h:<{widths[idx]}}" for idx, h in enumerate(headers)]) + " |")
    print(border)
    for row in rows:
        print("| " + " | ".join([f"{str(cell):<{widths[idx]}}" for idx, cell in enumerate(row)]) + " |")
    print(border)

def show_status():
    print(f"\n{Colors.HEADER}=====================================================")
    print("           STATUS DATABASE POS TERDISTRIBUSI         ")
    print(f"====================================================={Colors.ENDC}")
    
    for db_name in ['pusat', 'jkt', 'bdg']:
        conn = get_connection(db_name)
        if not conn:
            print(f"\n{Colors.FAIL}Database {db_name.upper()} : OFFLINE{Colors.ENDC}")
            continue
        
        print(f"\n{Colors.OKGREEN}Database {db_name.upper()} : ONLINE{Colors.ENDC}")
        try:
            cur = conn.cursor()
            
            # Tampilkan Produk
            cur.execute("SELECT id, nama, harga, stok FROM produk ORDER BY id")
            p_rows = cur.fetchall()
            p_headers = ["ID", "Nama Produk", "Harga", "Stok"]
            print_table(f"Produk ({db_name.upper()})", p_headers, p_rows)
            
            # Tampilkan Transaksi
            if db_name == 'pusat':
                cur.execute("SELECT id, id_cabang, waktu, total_harga FROM transaksi ORDER BY waktu DESC")
                tx_headers = ["ID Transaksi", "Cabang", "Waktu", "Total Harga"]
            else:
                cur.execute("SELECT id, id_cabang, waktu, total_harga, is_synced FROM transaksi ORDER BY waktu DESC")
                tx_headers = ["ID Transaksi", "Cabang", "Waktu", "Total Harga", "Synced?"]
            tx_rows = cur.fetchall()
            print_table(f"Transaksi ({db_name.upper()})", tx_headers, tx_rows)
            
            cur.close()
            conn.close()
        except Exception as e:
            print(f"  Error query database {db_name.upper()}: {e}")
            conn.close()

def main():
    if len(sys.argv) < 2:
        print_usage()
        return

    cmd = sys.argv[1]
    if cmd == 'setup':
        setup_databases()
    elif cmd == 'seed':
        seed_products()
    elif cmd == 'create-tx':
        if len(sys.argv) < 5:
            print(f"{Colors.FAIL}Error: Argumen kurang untuk membuat transaksi.{Colors.ENDC}")
            print("Penggunaan: python simulate.py create-tx <jkt/bdg> <product_id> <qty>")
            return
        branch = sys.argv[2].lower()
        try:
            product_id = int(sys.argv[3])
            qty = int(sys.argv[4])
        except ValueError:
            print(f"{Colors.FAIL}ID Produk dan Qty harus berupa angka.{Colors.ENDC}")
            return
        create_transaction(branch, product_id, qty)
    elif cmd == 'status':
        show_status()
    else:
        print_usage()

def print_usage():
    print(f"\n{Colors.BOLD}SBDT POS Distributed Simulator CLI{Colors.ENDC}")
    print("Penggunaan:")
    print("  python simulate.py setup          - Menyiapkan skema DB & konfigurasi replikasi logikal")
    print("  python simulate.py seed           - Menambahkan catalog produk di db_pusat")
    print("  python simulate.py status         - Menampilkan isi tabel di semua database (pusat, jkt, bdg)")
    print("  python simulate.py create-tx <cabang> <product_id> <qty>")
    print("                                    - Membuat transaksi baru di cabang ('jkt' atau 'bdg')")
    print("\nContoh:")
    print("  python simulate.py create-tx jkt 1 5")

if __name__ == '__main__':
    main()
