const { Client } = require('pg');

/**
 * Eksekusi Kueri Basis Data Tunggal
 * Helper ini otomatis mengelola lifecycle koneksi (connect & end)
 * sehingga mencegah kebocoran koneksi database.
 */
async function query(dbConfig, sql, params = []) {
    const client = new Client({
        ...dbConfig,
        connectionTimeoutMillis: 2000
    });
    try {
        await client.connect();
        const res = await client.query(sql, params);
        return res.rows;
    } finally {
        await client.end().catch(() => {});
    }
}

/**
 * Eksekusi Kueri dalam satu Transaction Block (BEGIN - COMMIT / ROLLBACK)
 * Helper ini menerima callback function `executeQueries` yang berisi rentetan kueri.
 */
async function executeTransaction(dbConfig, executeQueries) {
    const client = new Client({
        ...dbConfig,
        connectionTimeoutMillis: 2000
    });
    try {
        await client.connect();
        await client.query('BEGIN');
        
        // Jalankan seluruh kueri lewat callback
        const result = await executeQueries(client);
        
        await client.query('COMMIT');
        return result;
    } catch (err) {
        await client.query('ROLLBACK').catch(() => {});
        throw err;
    } finally {
        await client.end().catch(() => {});
    }
}

/**
 * Melakukan ping tes koneksi ke Database Pusat (HQ)
 */
async function checkHqOnline(hqConfig) {
    const client = new Client({
        ...hqConfig,
        connectionTimeoutMillis: 1000
    });
    try {
        await client.connect();
        await client.end();
        return true;
    } catch (err) {
        return false;
    }
}

module.exports = {
    query,
    executeTransaction,
    checkHqOnline
};
