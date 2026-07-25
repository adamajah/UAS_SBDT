-- DDL untuk Database Pusat (HQ)

-- 1. Tabel Produk (Master Data - Replicated to Cabang)
CREATE TABLE IF NOT EXISTS produk (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(100) NOT NULL,
    harga NUMERIC(12, 2) NOT NULL CHECK (harga >= 0),
    stok INT NOT NULL DEFAULT 0 CHECK (stok >= 0)
);

-- 2. Tabel Transaksi (Consolidated Data - Consolidated from Cabang)
CREATE TABLE IF NOT EXISTS transaksi (
    id UUID PRIMARY KEY,
    id_cabang VARCHAR(10) NOT NULL, -- 'JKT' atau 'BDG'
    waktu TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_harga NUMERIC(12, 2) NOT NULL DEFAULT 0
);

-- 3. Tabel Detail Transaksi
CREATE TABLE IF NOT EXISTS detail_transaksi (
    id UUID PRIMARY KEY,
    id_transaksi UUID NOT NULL REFERENCES transaksi(id) ON DELETE CASCADE,
    id_produk INT NOT NULL REFERENCES produk(id),
    jumlah INT NOT NULL CHECK (jumlah > 0),
    subtotal NUMERIC(12, 2) NOT NULL
);

-- Membuat Publication untuk Replikasi Produk (Pusat -> Cabang)
-- Catatan: Hanya perlu dibuat sekali
-- Jika publication sudah ada, Postgres akan menampilkan warning, gunakan exception handling di script setup.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'produk_pub') THEN
        CREATE PUBLICATION produk_pub FOR TABLE produk;
    END IF;
END $$;
