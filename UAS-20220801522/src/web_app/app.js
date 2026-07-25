const express = require('express');
const path = require('path');
const dbConfig = require('./config/db');

const app = express();

// 1. Setup EJS View Engine & Public Asset Directory
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.static(path.join(__dirname, 'public')));

// 2. Setup Parsers untuk form post data
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// 3. Inject Global variables & pesan ke View Engine (EJS Locals)
app.use((req, res, next) => {
    res.locals.app_type = dbConfig.APP_TYPE;
    res.locals.branch_name = dbConfig.BRANCH_NAME;
    res.locals.db_name = dbConfig.DB_CONFIG.database;
    res.locals.db_host = dbConfig.DB_CONFIG.host;
    res.locals.db_port = dbConfig.DB_CONFIG.port;
    
    // Ambil pesan notifikasi dari kueri parameter
    res.locals.success_msg = req.query.success || null;
    res.locals.error_msg = req.query.error || null;
    next();
});

// 4. Import & Mount Modular Route Handlers
const kasirRouter = require('./routes/kasir');
const dashboardRouter = require('./routes/dashboard');

if (dbConfig.APP_TYPE === 'pusat') {
    // Jalur HQ Dashboard Pusat
    app.get('/', (req, res) => res.redirect('/hq'));
    app.use(dashboardRouter);
} else {
    // Jalur Kasir Cabang
    app.use(kasirRouter);
}

// 5. Start Web Server
const PORT = parseInt(process.env.PORT || '5000');
app.listen(PORT, '0.0.0.0', () => {
    console.log(`[POS Terdistribusi] Node.js ${dbConfig.APP_TYPE.toUpperCase()} (${dbConfig.BRANCH_NAME}) aktif pada port ${PORT}`);
});
