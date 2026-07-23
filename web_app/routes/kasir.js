const express = require('express');
const router = express.Router();
const { v4: uuidv4 } = require('uuid');
const dbConfig = require('../config/db');
const dbHelper = require('../utils/db_helper');

// GET Halaman Kasir Lokal Cabang
router.get('/', async (req, res) => {
    try {
        // 1. Ambil Katalog Produk Lokal
        const products = await dbHelper.query(
            dbConfig.DB_CONFIG, 
            "SELECT id, nama, harga, stok FROM produk ORDER BY id"
        );

        // 2. Ambil Riwayat Transaksi Lokal Cabang ini
        const transactions = await dbHelper.query(
            dbConfig.DB_CONFIG,
            "SELECT id, waktu, total_harga, is_synced FROM transaksi ORDER BY waktu DESC LIMIT 10"
        );

        // 3. Cek Status Koneksi HQ (Eventual Consistency status)
        const hq_online = await dbHelper.checkHqOnline(dbConfig.HQ_DB_CONFIG);

        res.render('kasir', { products, transactions, hq_online });
    } catch (err) {
        res.render('error', { error_details: err.message });
    }
});

// POST Simulasi Checkout (Simpan ke DB Lokal)
router.post('/checkout', async (req, res) => {
    const { product_ids, quantities } = req.body;
    
    if (!product_ids || product_ids.length === 0) {
        return res.redirect('/?error=Keranjang+belanja+kosong!');
    }

    try {
        const ids = Array.isArray(product_ids) ? product_ids : [product_ids];
        const qtys = Array.isArray(quantities) ? quantities : [quantities];

        // Jalankan seluruh alur checkout dalam satu transaction block
        const txId = await dbHelper.executeTransaction(dbConfig.DB_CONFIG, async (client) => {
            const currentTxId = uuidv4();
            let totalHarga = 0.0;
            const orderItems = [];

            for (let i = 0; i < ids.length; i++) {
                const pId = parseInt(ids[i]);
                const qty = parseInt(qtys[i]);
                if (isNaN(qty) || qty <= 0) continue;

                // Kunci baris untuk mencegah race condition pemotongan stok
                const prodRes = await client.query(
                    "SELECT id, nama, harga, stok FROM produk WHERE id = $1 FOR UPDATE",
                    [pId]
                );
                const product = prodRes.rows[0];

                if (!product) {
                    throw new Error(`Produk dengan ID ${pId} tidak ditemukan.`);
                }

                if (product.stok < qty) {
                    throw new Error(`Stok ${product.nama} tidak mencukupi (Stok: ${product.stok}, Diminta: ${qty}).`);
                }

                const subtotal = parseFloat(product.harga) * qty;
                totalHarga += subtotal;

                orderItems.push({
                    id: uuidv4(),
                    id_produk: pId,
                    jumlah: qty,
                    subtotal: subtotal
                });

                // Update stok di DB lokal
                await client.query("UPDATE produk SET stok = stok - $1 WHERE id = $2", [qty, pId]);
            }

            if (totalHarga === 0) {
                throw new Error("Tidak ada item valid untuk dibeli.");
            }

            // Insert Transaksi Cabang (is_synced = FALSE)
            await client.query(
                "INSERT INTO transaksi (id, id_cabang, total_harga, is_synced) VALUES ($1, $2, $3, FALSE)",
                [currentTxId, dbConfig.BRANCH_NAME, totalHarga]
            );

            // Insert Detail Transaksi Cabang
            for (const item of orderItems) {
                await client.query(
                    "INSERT INTO detail_transaksi (id, id_transaksi, id_produk, jumlah, subtotal) VALUES ($1, $2, $3, $4, $5)",
                    [item.id, currentTxId, item.id_produk, item.jumlah, item.subtotal]
                );
            }

            return currentTxId;
        });

        res.redirect(`/?success=Transaksi+berhasil+dicatat+secara+lokal!+ID:+${txId}`);
    } catch (err) {
        res.redirect(`/?error=Transaksi+Gagal:+${encodeURIComponent(err.message)}`);
    }
});

module.exports = router;
