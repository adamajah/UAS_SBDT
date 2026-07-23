import time
import psycopg2
from psycopg2 import extras
import sys
import os

# Konfigurasi Koneksi Database (membaca Env Var untuk Portabilitas di Docker & Host)
DB_CONFIGS = {
    'pusat': {
        'dbname': os.environ.get('DB_NAME_PUSAT', 'pos_pusat'),
        'user': os.environ.get('DB_USER_PUSAT', 'postgres'),
        'password': os.environ.get('DB_PASS_PUSAT', 'supersecretpassword'),
        'host': os.environ.get('DB_HOST_PUSAT', 'localhost'),
        'port': int(os.environ.get('DB_PORT_PUSAT', 5431))
    },
    'jkt': {
        'dbname': os.environ.get('DB_NAME_JKT', 'pos_jkt'),
        'user': os.environ.get('DB_USER_JKT', 'postgres'),
        'password': os.environ.get('DB_PASS_JKT', 'supersecretpassword'),
        'host': os.environ.get('DB_HOST_JKT', 'localhost'),
        'port': int(os.environ.get('DB_PORT_JKT', 5433))
    },
    'bdg': {
        'dbname': os.environ.get('DB_NAME_BDG', 'pos_bdg'),
        'user': os.environ.get('DB_USER_BDG', 'postgres'),
        'password': os.environ.get('DB_PASS_BDG', 'supersecretpassword'),
        'host': os.environ.get('DB_HOST_BDG', 'localhost'),
        'port': int(os.environ.get('DB_PORT_BDG', 5434))
    }
}

# ANSI Colors untuk output terminal yang premium
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log_info(msg):
    print(f"{Colors.OKBLUE}[INFO] {msg}{Colors.ENDC}")

def log_success(msg):
    print(f"{Colors.OKGREEN}[SUCCESS] {msg}{Colors.ENDC}")

def log_warning(msg):
    print(f"{Colors.WARNING}[WARN] {msg}{Colors.ENDC}")

def log_error(msg):
    print(f"{Colors.FAIL}[ERROR] {msg}{Colors.ENDC}")

def get_connection(db_key):
    try:
        conn = psycopg2.connect(**DB_CONFIGS[db_key])
        return conn
    except Exception as e:
        return None

def sync_branch_to_pusat(branch_key):
    """
    Sinkronisasi transaksi dan detail transaksi dari Cabang ke Pusat
    Menggunakan mekanisme state-based:
    1. Tarik transaksi lokal di Cabang yang is_synced = FALSE.
    2. Masukkan ke Pusat.
    3. Jika berhasil dimasukkan ke Pusat, ubah status is_synced = TRUE di Cabang.
    """
    branch_conn = get_connection(branch_key)
    pusat_conn = get_connection('pusat')

    if not branch_conn:
        log_warning(f"Tidak dapat terhubung ke Cabang {branch_key.upper()} (Offline)")
        return

    if not pusat_conn:
        log_warning(f"Database Pusat (HQ) Offline. Transaksi lokal Cabang {branch_key.upper()} ditunda (Buffered).")
        branch_conn.close()
        return

    try:
        # Gunakan transaction block
        branch_cur = branch_conn.cursor(cursor_factory=extras.RealDictCursor)
        pusat_cur = pusat_conn.cursor()

        # 1. Ambil transaksi yang belum disinkronkan
        branch_cur.execute("SELECT id, id_cabang, waktu, total_harga FROM transaksi WHERE is_synced = FALSE")
        unsynced_txs = branch_cur.fetchall()

        if not unsynced_txs:
            branch_cur.close()
            branch_conn.close()
            pusat_cur.close()
            pusat_conn.close()
            return

        log_info(f"Menemukan {len(unsynced_txs)} transaksi baru di Cabang {branch_key.upper()} untuk disinkronkan...")

        for tx in unsynced_txs:
            tx_id = tx['id']
            # Ambil detail transaksi
            branch_cur.execute(
                "SELECT id, id_transaksi, id_produk, jumlah, subtotal FROM detail_transaksi WHERE id_transaksi = %s",
                (tx_id,)
            )
            details = branch_cur.fetchall()

            # 2. Masukkan ke Database Pusat
            # Gunakan ON CONFLICT DO NOTHING untuk idempotensi
            pusat_cur.execute(
                """
                INSERT INTO transaksi (id, id_cabang, waktu, total_harga) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (tx['id'], tx['id_cabang'], tx['waktu'], tx['total_harga'])
            )

            for detail in details:
                pusat_cur.execute(
                    """
                    INSERT INTO detail_transaksi (id, id_transaksi, id_produk, jumlah, subtotal)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (detail['id'], detail['id_transaksi'], detail['id_produk'], detail['jumlah'], detail['subtotal'])
                )

            # 3. Update status is_synced di Cabang
            branch_cur.execute(
                "UPDATE transaksi SET is_synced = TRUE WHERE id = %s",
                (tx_id,)
            )
        
        # Commit di kedua DB jika semua baris diproses tanpa error
        pusat_conn.commit()
        branch_conn.commit()
        log_success(f"Sinkronisasi berhasil! {len(unsynced_txs)} transaksi dari Cabang {branch_key.upper()} telah disinkronkan ke Pusat.")

    except Exception as e:
        pusat_conn.rollback()
        branch_conn.rollback()
        log_error(f"Gagal melakukan sinkronisasi untuk Cabang {branch_key.upper()}: {e}")
    finally:
        branch_cur.close()
        branch_conn.close()
        pusat_cur.close()
        pusat_conn.close()

def main():
    print(f"{Colors.HEADER}{Colors.BOLD}=====================================================")
    print("  SBDT POS - SINKRONISASI DAEMON (CABANG -> PUSAT)   ")
    print(f"====================================================={Colors.ENDC}")
    log_info("Memulai sinkronisasi asinkron transaksi...")
    
    interval = 5 # detik
    try:
        while True:
            for branch in ['jkt', 'bdg']:
                sync_branch_to_pusat(branch)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n")
        log_info("Sinkronisasi Daemon dihentikan oleh User.")
        sys.exit(0)

if __name__ == '__main__':
    main()
