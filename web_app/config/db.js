// Konfigurasi Basis Data POS Terdistribusi

const DB_CONFIG = {
    database: process.env.DB_NAME || 'pos_jkt',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASS || 'supersecretpassword',
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5433')
};

const HQ_DB_CONFIG = {
    database: process.env.HQ_DB_NAME || 'pos_pusat',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASS || 'supersecretpassword',
    host: process.env.HQ_DB_HOST || 'localhost',
    port: parseInt(process.env.HQ_DB_PORT || '5431')
};

const APP_TYPE = process.env.APP_TYPE || 'cabang';
const BRANCH_NAME = process.env.BRANCH_NAME || 'JKT';

module.exports = {
    DB_CONFIG,
    HQ_DB_CONFIG,
    APP_TYPE,
    BRANCH_NAME
};
