const { Client } = require('pg');

// Konfigurasi Koneksi Database dari Environment Variables (dengan local fallback)
const DB_CONFIGS = {
    pusat: {
        database: process.env.DB_NAME_PUSAT || 'pos_pusat',
        user: process.env.DB_USER_PUSAT || 'postgres',
        password: process.env.DB_PASS_PUSAT || 'supersecretpassword',
        host: process.env.DB_HOST_PUSAT || 'localhost',
        port: parseInt(process.env.DB_PORT_PUSAT || '5431')
    },
    jkt: {
        database: process.env.DB_NAME_JKT || 'pos_jkt',
        user: process.env.DB_USER_JKT || 'postgres',
        password: process.env.DB_PASS_JKT || 'supersecretpassword',
        host: process.env.DB_HOST_JKT || 'localhost',
        port: parseInt(process.env.DB_PORT_JKT || '5433')
    },
    bdg: {
        database: process.env.DB_NAME_BDG || 'pos_bdg',
        user: process.env.DB_USER_BDG || 'postgres',
        password: process.env.DB_PASS_BDG || 'supersecretpassword',
        host: process.env.DB_HOST_BDG || 'localhost',
        port: parseInt(process.env.DB_PORT_BDG || '5434')
    }
};

// ANSI Colors untuk logging premium
const Colors = {
    HEADER: '\x1b[95m',
    OKBLUE: '\x1b[94m',
    OKGREEN: '\x1b[92m',
    WARNING: '\x1b[93m',
    FAIL: '\x1b[91m',
    ENDC: '\x1b[0m',
    BOLD: '\x1b[1m'
};

function logInfo(msg) {
    console.log(`${Colors.OKBLUE}[INFO] ${msg}${Colors.ENDC}`);
}

function logSuccess(msg) {
    console.log(`${Colors.OKGREEN}[SUCCESS] ${msg}${Colors.ENDC}`);
}

function logWarning(msg) {
    console.log(`${Colors.WARNING}[WARN] ${msg}${Colors.ENDC}`);
}

function logError(msg) {
    console.log(`${Colors.FAIL}[ERROR] ${msg}${Colors.ENDC}`);
}

async function getClient(key) {
    const config = DB_CONFIGS[key];
    const client = new Client({
        ...config,
        connectionTimeoutMillis: 2000
    });
    try {
        await client.connect();
        return client;
    } catch (err) {
        return null;
    }
}

async function syncBranchToPusat(branchKey) {
    let branchClient = null;
    let pusatClient = null;

    try {
        branchClient = await getClient(branchKey);
        if (!branchClient) {
            logWarning(`Tidak dapat terhubung ke Cabang ${branchKey.toUpperCase()} (Offline)`);
            return;
        }

        // Ambil transaksi lokal Cabang yang is_synced = FALSE
        const txRes = await branchClient.query(
            "SELECT id, id_cabang, waktu, total_harga FROM transaksi WHERE is_synced = FALSE"
        );
        
        const unsyncedTxs = txRes.rows;
        if (unsyncedTxs.length === 0) {
            await branchClient.end();
            return;
        }

        pusatClient = await getClient('pusat');
        if (!pusatClient) {
            logWarning(`Database Pusat (HQ) Offline. Transaksi lokal Cabang ${branchKey.toUpperCase()} ditunda (Buffered).`);
            await branchClient.end();
            return;
        }

        logInfo(`Menemukan ${unsyncedTxs.length} transaksi baru di Cabang ${branchKey.toUpperCase()} untuk disinkronkan...`);

        // Sinkronisasi data per transaksi menggunakan transaction block
        for (const tx of unsyncedTxs) {
            const txId = tx.id;
            
            // Ambil detail transaksi lokal
            const detailRes = await branchClient.query(
                "SELECT id, id_transaksi, id_produk, jumlah, subtotal FROM detail_transaksi WHERE id_transaksi = $1",
                [txId]
            );
            const details = detailRes.rows;

            try {
                // Begin transaction di Pusat
                await pusatClient.query("BEGIN");

                // Insert Transaksi di Pusat (ON CONFLICT DO NOTHING untuk idempotensi)
                await pusatClient.query(
                    `INSERT INTO transaksi (id, id_cabang, waktu, total_harga) 
                     VALUES ($1, $2, $3, $4)
                     ON CONFLICT (id) DO NOTHING`,
                    [tx.id, tx.id_cabang, tx.waktu, tx.total_harga]
                );

                // Insert Detail Transaksi di Pusat
                for (const detail of details) {
                    await pusatClient.query(
                        `INSERT INTO detail_transaksi (id, id_transaksi, id_produk, jumlah, subtotal)
                         VALUES ($1, $2, $3, $4, $5)
                         ON CONFLICT (id) DO NOTHING`,
                        [detail.id, detail.id_transaksi, detail.id_produk, detail.jumlah, detail.subtotal]
                    );
                }

                // Commit di Pusat
                await pusatClient.query("COMMIT");

                // Update status is_synced di database lokal Cabang
                await branchClient.query(
                    "UPDATE transaksi SET is_synced = TRUE WHERE id = $1",
                    [txId]
                );
                
            } catch (err) {
                await pusatClient.query("ROLLBACK");
                throw err; // Lempar keluar untuk logging
            }
        }

        logSuccess(`Sinkronisasi berhasil! ${unsyncedTxs.length} transaksi dari Cabang ${branchKey.toUpperCase()} telah disinkronkan ke Pusat.`);

    } catch (err) {
        logError(`Gagal melakukan sinkronisasi untuk Cabang ${branchKey.toUpperCase()}: ${err.message}`);
    } finally {
        if (branchClient) {
            try { await branchClient.end(); } catch (e) {}
        }
        if (pusatClient) {
            try { await pusatClient.end(); } catch (e) {}
        }
    }
}

async function run() {
    console.log(`${Colors.HEADER}${Colors.BOLD}=====================================================`);
    console.log("  SBDT POS - NODE.JS SINKRONISASI DAEMON (CABANG)   ");
    console.log(`=====================================================${Colors.ENDC}`);
    logInfo("Memulai sinkronisasi asinkron transaksi...");

    const interval = 1000; // 1 detik
    
    const tick = async () => {
        await syncBranchToPusat('jkt');
        await syncBranchToPusat('bdg');
        setTimeout(tick, interval);
    };

    tick();
}

run().catch(err => {
    logError(`Daemon error: ${err.message}`);
    process.exit(1);
});
