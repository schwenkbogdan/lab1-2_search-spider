-- Создание таблицы pages
CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,
    title TEXT,
    content TEXT,
    indexed_date DATETIME
);

-- Создание таблицы words
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT UNIQUE
);

-- Создание таблицы page_words
CREATE TABLE IF NOT EXISTS page_words (
    page_id INTEGER,
    word_id INTEGER,
    frequency INTEGER,
    FOREIGN KEY (page_id) REFERENCES pages(id),
    FOREIGN KEY (word_id) REFERENCES words(id)
);

-- Создание таблицы links
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_page_id INTEGER,
    to_page_id INTEGER,
    FOREIGN KEY (from_page_id) REFERENCES pages(id),
    FOREIGN KEY (to_page_id) REFERENCES pages(id)
);
