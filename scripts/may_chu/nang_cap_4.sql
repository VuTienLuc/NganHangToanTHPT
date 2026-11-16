CREATE TABLE IF NOT EXISTS loi_nhan (id INTEGER PRIMARY KEY AUTOINCREMENT, tk TEXT, noi_dung TEXT, tu TEXT, tao_luc TEXT, xem_luc TEXT);
CREATE INDEX IF NOT EXISTS loi_nhan_tk ON loi_nhan(tk);
