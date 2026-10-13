"""Read authors' raw workbook without altering it. Source is recorded in raw/README.md."""
import openpyxl
import pandas as pd
from src.common import ROOT, sha256

RAW_HASH = 'c0bdd68dd694abe35cad2c04373b6d36c091041942be3f2398153453e2b58c8e'

def load_raw():
    path = ROOT / 'data/raw/P16_Silica_Aerogel_raw.xlsx'
    if sha256(path) != RAW_HASH:
        raise ValueError('Raw data SHA256 mismatch: preserve the original file and investigate.')
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = book['Comprehensive'].iter_rows(max_col=126, values_only=True)
    headers = next(rows)
    seen = {}
    unique = []
    for h in headers:
        seen[h] = seen.get(h, 0) + 1
        unique.append(h if seen[h] == 1 else f'{h}__duplicate_{seen[h]}')
    records = []
    for excel_row, row in enumerate(rows, 2):
        if row[0] is not None:
            rec = dict(zip(unique, row))
            rec['excel_row'] = excel_row
            records.append(rec)
    book.close()
    return pd.DataFrame(records)
