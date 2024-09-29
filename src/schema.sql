-- schema.sql

CREATE TABLE IF NOT EXISTS urllist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS wordlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT UNIQUE,
    is_filtered BOOLEAN
);

CREATE TABLE IF NOT EXISTS wordlocation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    urlid INTEGER,
    wordid INTEGER,
    location INTEGER,
    FOREIGN KEY (urlid) REFERENCES urllist(id),
    FOREIGN KEY (wordid) REFERENCES wordlist(id)
);

CREATE TABLE IF NOT EXISTS linkBetweenURL (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_urlid INTEGER,
    to_urlid INTEGER,
    FOREIGN KEY (from_urlid) REFERENCES urllist(id),
    FOREIGN KEY (to_urlid) REFERENCES urllist(id)
);

CREATE TABLE IF NOT EXISTS linkwords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wordid INTEGER,
    linkid INTEGER,
    FOREIGN KEY (wordid) REFERENCES wordlist(id),
    FOREIGN KEY (linkid) REFERENCES linkBetweenURL(id)
);
