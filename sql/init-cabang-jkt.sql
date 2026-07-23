-- DDL untuk Database Cabang Jakarta (db_cabang_jkt)

-- 1. Tabel Produk (Sebagai target replikasi dari Pusat)
CREATE TABLE IF NOT EXISTS produk (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(100) NOT NULL,
    harga NUMERIC(12, 2) NOT NULL CHECK (harga >= 0),
    stok INT NOT NULL DEFAULT 0 CHECK (stok >= 0)
);

-- 2. Tabel Transaksi Cabang (Local & Fragmented Data)
CREATE TABLE IF NOT EXISTS transaksi (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_cabang VARCHAR(10) NOT NULL DEFAULT 'JKT',
    waktu TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_harga NUMERIC(12, 2) NOT NULL DEFAULT 0,
    is_synced BOOLEAN DEFAULT FALSE -- Flag sinkronisasi asinkron ke Pusat
);

-- 3. Tabel Detail Transaksi
CREATE TABLE IF NOT EXISTS detail_transaksi (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_transaksi UUID NOT NULL REFERENCES transaksi(id) ON DELETE CASCADE,
    id_produk INT NOT NULL REFERENCES produk(id),
    jumlah INT NOT NULL CHECK (jumlah > 0),
    subtotal NUMERIC(12, 2) NOT NULL
);
