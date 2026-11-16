CREATE TABLE IF NOT EXISTS tk (ten TEXT PRIMARY KEY, ho_ten TEXT, lop TEXT, stt INTEGER, vai TEXT DEFAULT 'hs', muoi TEXT, bam TEXT,
  doi_mk INTEGER DEFAULT 1, khoa INTEGER DEFAULT 0, sai INTEGER DEFAULT 0, khoa_den INTEGER DEFAULT 0, lan_cuoi TEXT, tao_luc TEXT);
CREATE TABLE IF NOT EXISTS de (slug TEXT PRIMARY KEY, ten TEXT, lop TEXT DEFAULT '', so_luot INTEGER DEFAULT 2, nhom TEXT DEFAULT '',
  con TEXT DEFAULT '', khoa TEXT, trang_thai TEXT DEFAULT 'dang_mo', tao_luc TEXT);
CREATE TABLE IF NOT EXISTS bai (id INTEGER PRIMARY KEY AUTOINCREMENT, tk TEXT, de TEXT, nhom TEXT, lan INTEGER, bat_dau TEXT,
  nop_luc TEXT, tra_loi TEXT, diem REAL, cham TEXT, chuyen_tab INTEGER DEFAULT 0, thoi_gian INTEGER);
CREATE INDEX IF NOT EXISTS bai_tk ON bai(tk, nhom);
CREATE TABLE IF NOT EXISTS luot_them (tk TEXT, nhom TEXT, so INTEGER, PRIMARY KEY (tk, nhom));
