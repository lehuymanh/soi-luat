PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS documents(
  id INTEGER PRIMARY KEY,
  file_path TEXT NOT NULL UNIQUE,
  sha256 TEXT NOT NULL UNIQUE,
  so_hieu TEXT,
  so_hieu_search TEXT,
  loai TEXT,
  co_quan TEXT,
  ngay_ban_hanh TEXT,
  ngay_hieu_luc TEXT,
  hieu_luc TEXT CHECK(hieu_luc IN ('con','het','chua_ro')),
  source_status TEXT NOT NULL,
  extraction_method TEXT NOT NULL,
  struct_score REAL,
  multi_document_suspected INTEGER NOT NULL DEFAULT 0,
  fallback_doan INTEGER NOT NULL DEFAULT 0,
  reviewed_by TEXT,
  reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS pages(
  id INTEGER PRIMARY KEY,
  doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  page_no INTEGER NOT NULL,
  kind TEXT NOT NULL,
  extraction_method TEXT NOT NULL,
  ocr_status TEXT NOT NULL,
  ocr_engine TEXT,
  ocr_version TEXT,
  ocr_conf REAL,
  raw_text TEXT,
  normalized_text TEXT,
  search_accent TEXT,
  search_text TEXT,
  reviewed_text TEXT,
  verification_status TEXT NOT NULL,
  reviewed_by TEXT,
  reviewed_at TEXT,
  bbox_json TEXT,
  UNIQUE(doc_id, page_no)
);

CREATE TABLE IF NOT EXISTS units(
  id INTEGER PRIMARY KEY,
  doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  parent_id INTEGER REFERENCES units(id) ON DELETE CASCADE,
  path TEXT NOT NULL,
  level TEXT NOT NULL,
  title TEXT,
  title_search TEXT NOT NULL DEFAULT '',
  raw_text TEXT NOT NULL,
  normalized_text TEXT NOT NULL,
  search_accent TEXT NOT NULL DEFAULT '',
  search_text TEXT NOT NULL,
  context_search TEXT NOT NULL DEFAULT '',
  context_accent TEXT NOT NULL DEFAULT '',
  reviewed_text TEXT,
  page_from INTEGER,
  page_to INTEGER,
  boundary_confidence REAL,
  extraction_method TEXT NOT NULL,
  verification_status TEXT NOT NULL,
  from_table INTEGER NOT NULL DEFAULT 0,
  fine_min INTEGER,
  fine_max INTEGER,
  fine_source_unit INTEGER REFERENCES units(id) ON DELETE SET NULL,
  reviewed_by TEXT,
  reviewed_at TEXT,
  UNIQUE(doc_id, path)
);

CREATE TABLE IF NOT EXISTS unit_labels(
  unit_id INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
  label TEXT NOT NULL CHECK(label IN (
    'NGHIA_VU','CAM','THOI_HAN','DIEU_KIEN',
    'QUYEN','CHE_TAI','DINH_NGHIA'
  )),
  PRIMARY KEY (unit_id, label)
);

CREATE TABLE IF NOT EXISTS page_regions(
  id INTEGER PRIMARY KEY,
  page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  unit_id INTEGER REFERENCES units(id) ON DELETE SET NULL,
  x0 REAL, y0 REAL, x1 REAL, y1 REAL,
  image_path TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS units_fts USING fts5(
  title_search,
  search_accent,
  search_text,
  context_search,
  context_accent,
  content='units',
  content_rowid='id',
  tokenize='unicode61 remove_diacritics 0'
);

CREATE TABLE IF NOT EXISTS links(
  id INTEGER PRIMARY KEY,
  sanction_unit INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
  duty_unit INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
  method TEXT NOT NULL,
  confirmed INTEGER NOT NULL DEFAULT 0,
  reviewed_by TEXT,
  reviewed_at TEXT,
  UNIQUE(sanction_unit, duty_unit)
);

CREATE TABLE IF NOT EXISTS synonyms(
  id INTEGER PRIMARY KEY,
  term TEXT NOT NULL,
  alt TEXT NOT NULL,
  kind TEXT NOT NULL,
  approved INTEGER NOT NULL DEFAULT 0,
  reviewed_by TEXT,
  reviewed_at TEXT,
  UNIQUE(term, alt)
);

-- Vector theo nghĩa của Điều gốc (tuỳ chọn, soiluat-importer --nhung); float16, DIM chiều.
CREATE TABLE IF NOT EXISTS unit_vectors(
  unit_id INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
  model TEXT NOT NULL,
  vec BLOB NOT NULL,
  PRIMARY KEY (unit_id, model)
);

-- Khoá/giá trị nội bộ (vd. phiên bản seed từ điển đã nạp).
CREATE TABLE IF NOT EXISTS app_meta(
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS import_jobs(
  id INTEGER PRIMARY KEY,
  status TEXT NOT NULL CHECK(status IN (
    'queued','running','done','failed','skipped_duplicate'
  )),
  phase TEXT,
  file_path TEXT,
  sha256 TEXT,
  existing_file_path TEXT,
  pages_done INTEGER NOT NULL DEFAULT 0,
  pages_total INTEGER,
  error TEXT,
  started_at TEXT,
  finished_at TEXT
);

CREATE TABLE IF NOT EXISTS query_log(
  id INTEGER PRIMARY KEY,
  query_raw TEXT NOT NULL,
  result_count INTEGER NOT NULL,
  selected_unit INTEGER REFERENCES units(id) ON DELETE SET NULL,
  selected_doc_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
  selected_path TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subject_rules(
  id INTEGER PRIMARY KEY,
  phrase TEXT NOT NULL,
  phrase_fold TEXT NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN ('uu_tien','ha_uu_tien')),
  approved INTEGER NOT NULL DEFAULT 0,
  UNIQUE(phrase, kind)
);

CREATE TABLE IF NOT EXISTS effect_hints(
  id INTEGER PRIMARY KEY,
  source_doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  source_unit_id INTEGER REFERENCES units(id) ON DELETE SET NULL,
  target_so_hieu TEXT,
  kind TEXT NOT NULL CHECK(kind IN ('thay_the','bai_bo')),
  snippet TEXT NOT NULL,
  confirmed INTEGER NOT NULL DEFAULT 0,
  reviewed_by TEXT,
  reviewed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_docs_so_hieu_search ON documents(so_hieu_search);
CREATE INDEX IF NOT EXISTS idx_units_doc ON units(doc_id);
CREATE INDEX IF NOT EXISTS idx_units_path ON units(doc_id, path);
CREATE INDEX IF NOT EXISTS idx_units_parent ON units(parent_id);
CREATE INDEX IF NOT EXISTS idx_labels_unit ON unit_labels(unit_id);
CREATE INDEX IF NOT EXISTS idx_links_duty ON links(duty_unit);
CREATE INDEX IF NOT EXISTS idx_links_sanction ON links(sanction_unit);
CREATE INDEX IF NOT EXISTS idx_pages_doc ON pages(doc_id);

CREATE TRIGGER IF NOT EXISTS units_ai AFTER INSERT ON units BEGIN
  INSERT INTO units_fts(rowid, title_search, search_accent, search_text, context_search, context_accent)
  VALUES (new.id, new.title_search, new.search_accent, new.search_text, new.context_search, new.context_accent);
END;

CREATE TRIGGER IF NOT EXISTS units_ad AFTER DELETE ON units BEGIN
  INSERT INTO units_fts(units_fts, rowid, title_search, search_accent, search_text, context_search, context_accent)
  VALUES ('delete', old.id, old.title_search, old.search_accent, old.search_text, old.context_search, old.context_accent);
END;

CREATE TRIGGER IF NOT EXISTS units_au AFTER UPDATE ON units BEGIN
  INSERT INTO units_fts(units_fts, rowid, title_search, search_accent, search_text, context_search, context_accent)
  VALUES ('delete', old.id, old.title_search, old.search_accent, old.search_text, old.context_search, old.context_accent);
  INSERT INTO units_fts(rowid, title_search, search_accent, search_text, context_search, context_accent)
  VALUES (new.id, new.title_search, new.search_accent, new.search_text, new.context_search, new.context_accent);
END;
