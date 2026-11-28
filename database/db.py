"""Database access for PIRS. Imports data/Dataset into an empty database."""
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import (Boolean, Column, DateTime, Float, Integer, MetaData,
                        String, Table, Text, create_engine, delete, func,
                        insert, select, update)

VERSION = 'PIRS-db-complete-v6'
ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / 'data' / 'Dataset'
DB_PATH = ROOT / 'data' / 'pirs.db'
SUCCESS_PCT = float(os.getenv('PIRS_SUCCESS_PCT', '50'))
SUPPORTED_FORMATS = {'.csv', '.tsv', '.xlsx', '.xls', '.json', '.jsonl', '.parquet'}
COLUMNS = ['tajuk', 'pembayang', 'maksud', 'makna', 'tema', 'era', 'sumber', 'lesen']
meta = MetaData()
pantun = Table(
    'pantun', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('tajuk', String(200)), Column('pembayang', Text, nullable=False),
    Column('maksud', Text, nullable=False), Column('makna', Text),
    Column('tema', String(200)), Column('era', String(60)),
    Column('sumber', String(300)), Column('lesen', String(200)),
    Column('verified', Boolean, default=False), Column('created_at', DateTime),
)
search_log = Table(
    'search_log', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('ts', DateTime), Column('query', Text), Column('n_results', Integer),
    Column('top_pct', Float), Column('latency_ms', Float),
)
feedback = Table(
    'feedback', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('ts', DateTime), Column('search_id', Integer),
    Column('pantun_id', Integer), Column('helpful', Boolean),
)
_engine = None


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _clean(value):
    if isinstance(value, (list, tuple, set)):
        return ', '.join(filter(None, (_clean(v) for v in value)))
    if isinstance(value, dict):
        return str(value)
    if value is None or pd.isna(value):
        return ''
    return str(value).strip()


def get_engine():
    global _engine
    if _engine is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        url = os.getenv('PIRS_DB_URL') or f'sqlite:///{DB_PATH.as_posix()}'
        kwargs = ({'connect_args': {'check_same_thread': False}}
                  if url.startswith('sqlite') else {'pool_pre_ping': True})
        _engine = create_engine(url, **kwargs)
    return _engine


def read_dataset_file(file):
    ext = file.suffix.lower()
    if ext in {'.csv', '.tsv'}:
        sep = '\t' if ext == '.tsv' else ','
        try:
            return pd.read_csv(file, sep=sep, encoding='utf-8-sig', keep_default_na=False)
        except UnicodeDecodeError:
            return pd.read_csv(file, sep=sep, encoding='cp1252', keep_default_na=False)
    if ext in {'.xls', '.xlsx'}:
        return read_excel_records(file)
    if ext in {'.json', '.jsonl'}:
        return pd.read_json(file, lines=(ext == '.jsonl'))
    if ext == '.parquet':
        return pd.read_parquet(file)
    raise ValueError(f'Unsupported file format: {ext}')


def _headers(df):
    df = df.copy()
    df.columns = [re.sub(r'[^\w]+', '_', str(c).strip().lower()).strip('_') for c in df.columns]
    return df


def _key(value):
    text = _clean(value)
    return re.sub(r'\.0$', '', text)


def read_excel_records(file):
    """Prefer explicitly separated verse sheets; join metadata from the main sheet."""
    sheets = pd.read_excel(file, sheet_name=None)
    main_name = next((n for n in sheets if n.strip().lower() == 'pantun'), next(iter(sheets)))
    main = _headers(sheets[main_name])
    # Known headerless workbook from the reported console output.
    if 'pantun' not in main and 'santun seni bicara' in file.stem.lower() and len(main.columns) == 5:
        main = pd.read_excel(file, sheet_name=main_name, header=None)
        main.columns = ['bil', 'pantun', 'kerat_code', 'asal', 'sumber']
    if 'pantun' not in main:
        return main
    if 'sumber' in main:
        sources = list(dict.fromkeys(v for v in main['sumber'].map(_clean) if v))
        fallback = sources[0] if len(sources) == 1 else file.stem
    else:
        fallback = file.stem
    if 'sumber' not in main:
        main['sumber'] = fallback
    else:
        main['sumber'] = main['sumber'].map(_clean).replace('', fallback)
    structured = []
    for name, frame in sheets.items():
        if not re.fullmatch(r'pantun\s*\d+\s*kerat', name.strip(), re.I):
            continue
        frame = _headers(frame)
        cols = sorted((c for c in frame if re.fullmatch(r'baris_?\d+', c)),
                      key=lambda c: int(re.search(r'\d+', c).group()))
        if not cols or len(cols) % 2 or 'bil' not in frame:
            continue
        if [int(re.search(r'\d+', c).group()) for c in cols] != list(range(1, len(cols)+1)):
            continue
        for row in frame.to_dict('records'):
            lines = [_clean(row.get(c)) for c in cols]
            if all(lines):
                middle = len(lines)//2
                structured.append((_key(row['bil']), '\n'.join(lines[:middle]), '\n'.join(lines[middle:]), _clean(row.get('tema'))))
    if not structured:
        return main
    ids = [x[0] for x in structured]
    if len(ids) != len(set(ids)):
        print(f'WARNING: {file.name}: repeated verse-sheet IDs; using main sheet')
        return main
    lookup = {k: (p,m,t) for k,p,m,t in structured}
    if 'bil' in main and main['bil'].map(_key).ne('').all() and main['bil'].map(_key).is_unique:
        main_ids = main['bil'].map(_key).tolist()
    elif set(ids) == {str(i) for i in range(1, len(main)+1)}:
        # Verify positional correspondence by comparing normalized full verses.
        norm = lambda t: re.sub(r'[^\w]+', '', t.casefold())
        matches = sum(norm(_clean(v)) == norm(' '.join(lookup[str(i)][:2]))
                      for i,v in enumerate(main['pantun'], 1))
        if matches / max(1, len(main)) < .90:
            print(f'WARNING: {file.name}: verse sheet alignment uncertain; using main sheet')
            return main
        main_ids = [str(i) for i in range(1, len(main)+1)]
    else:
        print(f'WARNING: {file.name}: no reliable verse-sheet alignment; using main sheet')
        return main
    main['pembayang'] = [lookup.get(k, ('','',''))[0] for k in main_ids]
    main['maksud'] = [lookup.get(k, ('','',''))[1] for k in main_ids]
    # Main sheet retains original theme and source; fill empty themes if possible.
    if 'tema' not in main:
        main['tema'] = ''
    main['tema'] = [_clean(t) or lookup.get(k, ('','',''))[2] for k,t in zip(main_ids, main['tema'])]
    print(f'{file.name}: used structured verse sheets for {sum(k in lookup for k in main_ids)}/{len(main)} rows')
    return main


def split_pantun(value):
    """Split explicit lines or punctuation; leave ambiguous rows for review."""
    def halves(lines):
        if len(lines) >= 2 and len(lines) % 2 == 0:
            m = len(lines)//2
            return '\n'.join(lines[:m]), '\n'.join(lines[m:])
        return '', ''
    if isinstance(value, (list, tuple)):
        return halves([_clean(v) for v in value if _clean(v)])
    text = _clean(value)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.I)
    text = text.replace('\\r\\n', '\n').replace('\\n', '\n')
    lines = [v.strip() for v in text.splitlines() if v.strip()]
    if len(lines) > 1:
        return halves(lines)
    for sep in (' / ', ' | ', '|', '/'):
        if sep in text:
            parts = [v.strip() for v in text.split(sep) if v.strip()]
            if len(parts) >= 2 and len(parts) % 2 == 0:
                return halves(parts)
    # A single semicolon is the usual pembayang/maksud boundary.
    if text.count(';') == 1:
        p, m = (v.strip() for v in text.split(';', 1))
        if p and m:
            # Only infer comma-based line breaks when both halves agree.
            if p.count(',') == m.count(','):
                p = re.sub(r',\s*', ',\n', p)
                m = re.sub(r',\s*', ',\n', m)
            return p + ';', m
    if ';' not in text:
        # Questions sometimes mark the middle rather than a semicolon.
        q = re.split(r'(?<=[?!])\s+(?=\S)', text)
        if len(q) == 2 and q[0].count(',') == q[1].count(','):
            return tuple(re.sub(r',\s*', ',\n', v) for v in q)
        parts = [v.strip() for v in re.split(r'(?<=,)\s*', text) if v.strip()]
        if len(parts) in (2,4,6,8,10,12):
            return halves(parts)
    return '', ''


def preprocess_dataset(df, filename):
    df = df.copy()
    df.columns = [re.sub(r'[^\w]+', '_', str(c).strip().lower()).strip('_') for c in df.columns]
    if df.columns.duplicated().any():
        raise ValueError(f'{filename}: duplicate column names')
    print(f'{filename}: columns {df.columns.tolist()}')
    aliases = {
        'tajuk': ('title', 'judul', 'nama_pantun'),
        'pembayang': ('sampiran', 'pembayang_pantun'),
        'maksud': ('isi', 'isi_pantun'),
        'makna': ('meaning', 'explanation', 'huraian', 'penjelasan', 'maksud_pantun'),
        'tema': ('theme', 'category', 'kategori', 'jenis', 'tema_pantun'),
        'era': ('period', 'zaman'),
        'sumber': ('source', 'rujukan'),
        'lesen': ('license', 'licence'),
        'pantun': ('teks_pantun', 'pantun_penuh', 'pantun_lengkap', 'teks', 'poem', 'pantun_text', 'full_pantun'),
    }
    for target, alternatives in aliases.items():
        for alias in alternatives:
            if alias not in df.columns:
                continue
            if target not in df.columns:
                df[target] = df[alias]
            else:
                empty = df[target].map(_clean).eq('')
                df.loc[empty, target] = df.loc[empty, alias]
    line_cols = []
    for i in range(1, 5):
        candidates = (f'baris_{i}', f'baris{i}', f'line_{i}', f'line{i}', f'ayat_{i}', f'ayat{i}')
        line_cols.append(next((c for c in candidates if c in df.columns), None))
    has_lines = all(c is not None for c in line_cols)
    if not ({'pembayang', 'maksud'}.issubset(df.columns) or 'pantun' in df.columns or has_lines):
        raise ValueError(f'Unknown pantun layout. Available columns: {df.columns.tolist()}')
    rows, rejected = [], []
    rejected_records = []
    for pos, record in enumerate(df.to_dict('records'), start=2):
        row = {c: _clean(record.get(c)) for c in COLUMNS}
        for c in ('pembayang', 'maksud'):
            if isinstance(record.get(c), (list, tuple)):
                row[c] = '\n'.join(_clean(v) for v in record[c] if _clean(v))
        if not row['pembayang'] or not row['maksud']:
            p, m = split_pantun(record.get('pantun'))
            if not p and has_lines:
                parts = [_clean(record.get(c)) for c in line_cols]
                if all(parts):
                    p, m = split_pantun(parts)
            row['pembayang'] = row['pembayang'] or p
            row['maksud'] = row['maksud'] or m
        if not row['pembayang'] or not row['maksud']:
            rejected.append(pos)
            rejected_records.append({'file': filename, 'row_position': pos, 'pantun': _clean(record.get('pantun'))})
            continue
        for c, default in {'tajuk': 'Pantun', 'era': 'Tidak dinyatakan', 'sumber': Path(filename).stem}.items():
            row[c] = row[c] or default
        rows.append(row)
    if rejected:
        print(f'WARNING: {filename}: {len(rejected)} incomplete or unrecognized rows; first affected row positions: {rejected[:20]}')
    result = pd.DataFrame(rows, columns=COLUMNS)
    result.attrs['rejected'] = rejected_records
    return result


def load_dataset_files() -> pd.DataFrame:
    if not DATASET_DIR.is_dir():
        raise FileNotFoundError(f'Dataset folder not found: {DATASET_DIR}')
    discovered = sorted(p for p in DATASET_DIR.rglob('*') if p.is_file())
    files = [p for p in discovered if p.suffix.lower() in SUPPORTED_FORMATS
             and not p.name.startswith('~$')]
    if not files:
        names = [str(p.relative_to(DATASET_DIR)) for p in discovered]
        raise FileNotFoundError(f'No supported dataset files found in: {DATASET_DIR}\n'
                                f'Files detected: {names}\n'
                                f'Supported extensions: {sorted(SUPPORTED_FORMATS)}')
    datasets = []
    skipped = []
    review = []
    for file in files:
        try:
            df = preprocess_dataset(read_dataset_file(file), file.name)
        except Exception as exc:
            skipped.append((str(file), str(exc)))
            print(f'WARNING: Cannot import {file}: {exc}')
            continue
        review.extend(df.attrs.pop('rejected', []))
        print(f'Loaded {len(df)} valid records from {file.name}')
        if not df.empty:
            datasets.append(df)
        else:
            skipped.append((str(file), "No valid rows"))
    if review:
        report = DB_PATH.parent / 'pantun_import_review.csv'
        report.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(review).to_csv(report, index=False, encoding='utf-8-sig')
        print(f'Review report: {report} ({len(review)} rows)')
    if not datasets:
        raise ValueError(f"No valid pantun records found. File errors: {skipped}")
    for name, reason in skipped:
        print(f"WARNING: File not imported: {name}: {reason}")
    print(f"Files imported: {len(datasets)}/{len(files)}")
    combined = (pd.concat(datasets, ignore_index=True)
                .drop_duplicates(subset=['pembayang', 'maksud'])
                .reset_index(drop=True))
    if combined.empty:
        raise ValueError('No valid pantun records found.')
    print(f'Duplicate records removed: {sum(len(d) for d in datasets) - len(combined)}')
    print(f'Total unique valid records: {len(combined)}')
    return combined


def init_db(seed: bool = True) -> None:
    eng = get_engine()
    meta.create_all(eng)
    with eng.begin() as con:
        empty = con.execute(select(func.count()).select_from(pantun)).scalar() == 0
        if seed and empty:
            df = load_dataset_files()
            df['verified'] = True
            df['created_at'] = _now()
            records = df.to_dict('records')
            for start in range(0, len(records), 1000):
                con.execute(insert(pantun), records[start:start + 1000])
            print(f'Imported {len(records)} pantun into database.')


def load_pantun(verified_only: bool = True) -> pd.DataFrame:
    q = select(pantun)
    if verified_only:
        q = q.where(pantun.c.verified.is_(True))
    with get_engine().connect() as con:
        return pd.read_sql(q.order_by(pantun.c.id), con)


def add_pantun(record: dict, verified: bool = False) -> int:
    row = {c: _clean(record.get(c)) for c in COLUMNS}
    row.update(verified=verified, created_at=_now())
    with get_engine().begin() as con:
        return int(con.execute(insert(pantun).values(**row)).inserted_primary_key[0])


def bulk_add(df: pd.DataFrame, verified: bool = False) -> int:
    rows = [{**{c: _clean(r.get(c)) for c in COLUMNS}, 'verified': verified,
             'created_at': _now()} for r in df.to_dict('records')]
    with get_engine().begin() as con:
        if rows:
            con.execute(insert(pantun), rows)
    return len(rows)


def apply_changes(edited: pd.DataFrame) -> None:
    with get_engine().begin() as con:
        for r in edited.itertuples():
            if r.delete:
                con.execute(delete(pantun).where(pantun.c.id == int(r.id)))
            else:
                con.execute(update(pantun).where(pantun.c.id == int(r.id))
                            .values(verified=bool(r.verified)))


def log_search(query: str, n_results: int, top_pct: float, latency_ms: float) -> int:
    with get_engine().begin() as con:
        res = con.execute(insert(search_log).values(ts=_now(), query=query[:500],
                          n_results=n_results, top_pct=top_pct, latency_ms=latency_ms))
        return int(res.inserted_primary_key[0])


def log_feedback(search_id: int | None, pantun_id: int, helpful: bool) -> None:
    with get_engine().begin() as con:
        con.execute(insert(feedback).values(ts=_now(), search_id=search_id,
                                            pantun_id=pantun_id, helpful=helpful))


def usage_stats() -> dict:
    with get_engine().connect() as con:
        logs = pd.read_sql(select(search_log), con)
        fb = pd.read_sql(select(feedback), con)
    out = {'searches': len(logs), 'successful': 0, 'avg_latency_ms': 0.0,
           'p95_latency_ms': 0.0, 'feedback': len(fb), 'helpful_rate': None,
           'per_day': pd.DataFrame(columns=['day', 'searches']), 'log': logs}
    if len(logs):
        out['successful'] = int((logs['top_pct'].fillna(0) >= SUCCESS_PCT).sum())
        out['avg_latency_ms'] = float(logs['latency_ms'].mean())
        out['p95_latency_ms'] = float(logs['latency_ms'].quantile(0.95))
        out['per_day'] = (logs.assign(day=pd.to_datetime(logs['ts']).dt.date)
                          .groupby('day').size().reset_index(name='searches'))
    if len(fb):
        out['helpful_rate'] = float(fb['helpful'].mean())
    return out


def database_info() -> dict:
    eng = get_engine()
    with eng.connect() as con:
        total = int(con.execute(select(func.count()).select_from(pantun)).scalar() or 0)
        verified = int(con.execute(select(func.count()).select_from(pantun)
                       .where(pantun.c.verified.is_(True))).scalar() or 0)
    return {'database_path': str(eng.url.database) if eng.url.get_backend_name() == 'sqlite'
            else eng.url.get_backend_name(), 'dataset_directory': str(DATASET_DIR),
            'total_pantun': total, 'verified_pantun': verified,
            'unverified_pantun': total - verified}


if __name__ == '__main__':
    print(f'Running database module: {Path(__file__).resolve()}')
    print(f'Dataset folder: {DATASET_DIR}')
    init_db()
    print(database_info())
    print(load_pantun().head())
