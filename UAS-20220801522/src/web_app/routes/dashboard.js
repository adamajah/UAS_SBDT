const express = require('express');
const router = express.Router();
const dbConfig = require('../config/db');
const dbHelper = require('../utils/db_helper');

// GET Halaman Dashboard Pusat (HQ)
router.get('/hq', async (req, res) => {
    try {
        // 1. Ambil Katalog Produk Pusat
        const products = await dbHelper.query(
            dbConfig.DB_CONFIG,
            "SELECT id, nama, harga, stok FROM produk ORDER BY id"
        );

        // 2. Ambil Umpan Transaksi Global Terkonsolidasi
        const transactions = await dbHelper.query(
            dbConfig.DB_CONFIG,
            "SELECT id, id_cabang, waktu, total_harga FROM transaksi ORDER BY waktu DESC LIMIT 20"
        );

        // 3. Hitung Statistik Omzet & Volume Transaksi
        const summaryRows = await dbHelper.query(
            dbConfig.DB_CONFIG,
            "SELECT COUNT(*) as count, COALESCE(SUM(total_harga), 0) as total FROM transaksi"
        );
        const summary = summaryRows[0];

        // 4. Breakdown Pendapatan Per Cabang
        const statsRows = await dbHelper.query(
            dbConfig.DB_CONFIG,
            "SELECT id_cabang, COALESCE(SUM(total_harga), 0) as total FROM transaksi GROUP BY id_cabang"
        );

        const branchStats = {};
        statsRows.forEach(r => {
            branchStats[r.id_cabang] = parseFloat(r.total);
        });

        const total_jkt = branchStats['JKT'] || 0.0;
        const total_bdg = branchStats['BDG'] || 0.0;

        res.render('dashboard', {
            products,
            transactions,
            summary: {
                count: parseInt(summary.count),
                total: parseFloat(summary.total)
            },
            total_jkt,
            total_bdg
        });
    } catch (err) {
        res.render('error', { error_details: err.message });
    }
});

// POST Tambah Produk Baru di Pusat (Memicu Replikasi)
router.post('/hq/product/add', async (req, res) => {
    const { nama, harga, stok } = req.body;
    try {
        await dbHelper.query(
            dbConfig.DB_CONFIG,
            "INSERT INTO produk (nama, harga, stok) VALUES ($1, $2, $3)",
            [nama, parseFloat(harga), parseInt(stok)]
        );
        res.redirect(`/hq?success=Produk+${encodeURIComponent(nama)}+berhasil+ditambahkan!+Replikasi+logikal+berjalan.`);
    } catch (err) {
        res.redirect(`/hq?error=Gagal+tambah+produk:+${encodeURIComponent(err.message)}`);
    }
});

// POST Update Harga & Stok di Pusat
router.post('/hq/product/update', async (req, res) => {
    const { id, harga, stok } = req.body;
    try {
        await dbHelper.query(
            dbConfig.DB_CONFIG,
            "UPDATE produk SET harga = $1, stok = $2 WHERE id = $3",
            [parseFloat(harga), parseInt(stok), parseInt(id)]
        );
        res.redirect(`/hq?success=Produk+ID+${id}+berhasil+diupdate!`);
    } catch (err) {
        res.redirect(`/hq?error=Gagal+update+produk:+${encodeURIComponent(err.message)}`);
    }
});

// POST Hapus Produk di Pusat
router.post('/hq/product/delete/:id', async (req, res) => {
    const pId = parseInt(req.params.id);
    try {
        await dbHelper.query(
            dbConfig.DB_CONFIG,
            "DELETE FROM produk WHERE id = $1",
            [pId]
        );
        res.redirect(`/hq?success=Produk+ID+${pId}+berhasil+dihapus+dari+katalog+Pusat!`);
    } catch (err) {
        res.redirect(`/hq?error=Gagal+hapus+produk:+${encodeURIComponent(err.message)}`);
    }
});

module.exports = router;
