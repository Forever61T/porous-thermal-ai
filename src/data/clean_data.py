"""Conservative independent audit; inspired by database fields, not author cleaning code.

Source: jameskferri/Aerogel_ML_Neo4j/backends/raw_si_aerogels.xlsx.
We do NOT use backends/data_cleanup.py: ranges, inequalities and ambient process
conditions are not silently turned into measurement numbers.
"""
import hashlib
import numbers
import re
import unicodedata
import numpy as np
import pandas as pd
from src.common import ROOT, config, save_json
from src.data.load_data import load_raw, RAW_HASH

NUMERIC = {
    'k_W_mK': 'Thermal Conductivity (W/mK)',
    'density_g_cm3': 'Bulk Density (g/cm3)',
    'porosity_percent': 'Porosity (%)',
    'diameter_nm': 'Average Pore Diameter (nm)',
    'size_nm': 'Average Pore Size (nm)',
    'BET_m2_g': 'Surface Area (m2/g)',
    'precursor_M': 'Si Precursor Concentration (M)',
    'co_precursor_M': 'Si Co-Precursor Concentration (M)',
    'hybrid_precursor_M': 'Co-Precursor Concentration (M)',
    'dopant_M': 'Dopant Concentration (M)',
}

def present(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return False
    s = str(value).strip().lower()
    return s not in {'', 'nan', 'none', 'n/a', 'na', 'unknown'} and not re.fullmatch(r'[-–—\s]+', s)

def numeric(value):
    # Native Excel numbers only: reproducibly recover the previous 193-label definition.
    return float(value) if isinstance(value, numbers.Real) and not isinstance(value, bool) and np.isfinite(value) else np.nan

def paper_key(title):
    normalized = ' '.join(unicodedata.normalize('NFKC', str(title)).casefold().split())
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:12]

def stats(series):
    s = series.dropna()
    if len(s) == 0:
        return dict(n=0, missing_pct=100.0)
    return dict(n=int(len(s)), missing_pct=float(100*(1-len(s)/len(series))),
                min=float(s.min()), q25=float(s.quantile(.25)), median=float(s.median()),
                q75=float(s.quantile(.75)), max=float(s.max()))

def audit_no2():
    raw = load_raw()
    out = ROOT/'data/processed'
    out.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({'sample_id': raw.excel_row.map(lambda x:f'row_{x}'),
                       'excel_row': raw.excel_row, 'material': raw['Final Material'],
                       'title': raw['Title'], 'year': raw['Year']})
    df['paper_id'] = df.title.map(paper_key)
    logs = []
    for col, header in NUMERIC.items():
        df[col] = raw[header].map(numeric)
        for i, value in raw[header].items():
            if present(value) and np.isnan(df.loc[i,col]):
                logs.append(dict(excel_row=int(raw.loc[i,'excel_row']), field=header,
                                 original=str(value), new_value='', action='not_parsed',
                                 reason='Not a native finite Excel number; no range averaging or inequality stripping'))
    df['density_kg_m3'] = df.density_g_cm3*1000
    df['phi_observed'] = df.porosity_percent/100
    for col, header, factor, dest in [('density_g_cm3', NUMERIC['density_g_cm3'],1000,'density_kg_m3'),
                                      ('porosity_percent',NUMERIC['porosity_percent'],.01,'phi_observed')]:
        for i in df.index[df[col].notna()]:
            logs.append(dict(excel_row=int(df.loc[i,'excel_row']),field=header,original=df.loc[i,col],
                             new_value=float(df.loc[i,col]*factor),action='unit_conversion',
                             reason=f'Explicit column header conversion to {dest}; multiply by {factor}'))
    df['pore_nm'] = df.diameter_nm.combine_first(df.size_nm)
    df['pore_metric'] = np.where(df.diameter_nm.notna(),'diameter',np.where(df.size_nm.notna(),'size','missing'))
    # Keep both original pore metrics; they are not proven to be interchangeable.
    for i in df.index[df.pore_nm.notna()]:
        logs.append(dict(excel_row=int(df.loc[i,'excel_row']),field='pore_nm',original=df.loc[i,'pore_metric'],
                         new_value=float(df.loc[i,'pore_nm']),action='indicator_selection',
                         reason='Prefer diameter; fallback size, retain provenance. No nm/um conversion without source evidence.'))
    df['precursor'] = raw['Si Precursor'].map(lambda x:str(x).strip() if present(x) else np.nan)
    df['drying_method'] = raw['Drying Method'].map(lambda x:str(x).strip() if present(x) else np.nan)
    df['composition_identity_present'] = df.precursor.notna()
    df['composition_quantified_present'] = df.precursor_M.notna()
    df['measurement_temperature_K'] = np.nan
    df['measurement_pressure_Pa'] = np.nan
    df['phi_density_scenario'] = 1-df.density_kg_m3/config('no2')['scenario_skeletal_density_kg_m3']
    # These provisional screens do not establish that the remaining units are correct.
    df['k_unit_flag'] = df.k_W_mK.gt(1.0)
    df['density_flag'] = df.density_kg_m3.le(0) | df.density_kg_m3.ge(2200)
    df['pore_flag'] = df.pore_nm.le(0)
    df['porosity_flag'] = df.phi_observed.le(0) | df.phi_observed.ge(1)
    masks = {
      'k_native':df.k_W_mK.notna(),
      'core83_raw':df[['k_W_mK','density_kg_m3','pore_nm']].notna().all(axis=1),
    }
    masks['core_screened'] = masks['core83_raw'] & df.k_W_mK.between(.0001,1) & ~df.density_flag & ~df.pore_flag
    masks['observed_phi_screened'] = masks['core_screened'] & df.phi_observed.notna() & ~df.porosity_flag
    df['dataset_membership'] = [';'.join(n for n,m in masks.items() if m[i]) for i in df.index]
    for i in df.index:
        reasons = []
        if df.loc[i,'k_unit_flag']: reasons.append('k > 1 W/mK under header; suspected unit mismatch, not automatically corrected')
        if df.loc[i,'density_flag']: reasons.append('density outside assumed silica skeletal-density range')
        if df.loc[i,'pore_flag']: reasons.append('nonpositive pore indicator')
        if df.loc[i,'porosity_flag']: reasons.append('porosity outside (0,1)')
        for reason in reasons:
            logs.append(dict(excel_row=int(df.loc[i,'excel_row']),field='row_screen',original=str(df.loc[i,'k_W_mK']),
                             new_value='unchanged',action='flag_not_fix',reason=reason))
    df.to_csv(out/'no2_audited_all.csv',index=False)
    for name,mask in masks.items():
        df.loc[mask].to_csv(out/f'no2_{name}.csv',index=False)
    pd.DataFrame(logs).to_csv(out/'cleaning_events.csv',index=False)
    df.loc[df.k_unit_flag,['sample_id','title','material','k_W_mK']].to_csv(out/'unit_review_queue.csv',index=False)
    distribution = []
    for name, mask in [('all997',pd.Series(True,index=df.index)),('k193',masks['k_native']),('core83',masks['core83_raw'])]:
        for col in ['k_W_mK','density_kg_m3','porosity_percent','diameter_nm','size_nm','pore_nm','BET_m2_g','measurement_temperature_K','measurement_pressure_Pa']:
            distribution.append(dict(population=name,field=col,**stats(df.loc[mask,col])))
        for col in ['precursor','drying_method']:
            s=df.loc[mask,col]
            distribution.append(dict(population=name,field=col,n=int(s.notna().sum()),missing_pct=float(100*s.isna().mean())))
    pd.DataFrame(distribution).to_csv(ROOT/'results/tables/no2_distributions.csv',index=False)
    sources = df.loc[masks['k_native']].groupby(['paper_id','title'],dropna=False).agg(n_k=('sample_id','size'),
               n_unit_flags=('k_unit_flag','sum')).reset_index().sort_values('n_k',ascending=False)
    sources.to_csv(ROOT/'results/tables/no2_papers.csv',index=False)
    composition_headers=['Si Precursor','Additional Si Co-Precursor(s)','Hybrid Aerogel Co-Precursor','Dopant',
                         'Si Precursor Concentration (M)','Si Co-Precursor Concentration (M)',
                         'Co-Precursor Concentration (M)','Dopant Concentration (M)']
    composition_coverage=[]
    for population,mask in [('all997',pd.Series(True,index=df.index)),('k193',masks['k_native']),('core83',masks['core83_raw'])]:
        for header in composition_headers:
            series=raw.loc[mask,header]
            n=int(series.map(present).sum());n_numeric=int(series.map(numeric).notna().sum())
            composition_coverage.append(dict(population=population,field=header,n_reported=n,
                missing_pct=float(100*(1-n/len(series))),n_native_numeric=n_numeric))
    pd.DataFrame(composition_coverage).to_csv(ROOT/'results/tables/no2_composition_coverage.csv',index=False)
    duplicates=int(df.loc[masks['core_screened']].duplicated(['paper_id','k_W_mK','density_kg_m3','pore_nm'],keep='first').sum())
    for col in ['precursor','drying_method','pore_metric']:
        df.loc[masks['k_native'],col].fillna('MISSING').value_counts().rename_axis(col).reset_index(name='n').to_csv(ROOT/f'results/tables/no2_{col}_categories.csv',index=False)
    counts = {n:dict(n=int(m.sum()),papers=int(df.loc[m,'paper_id'].nunique())) for n,m in masks.items()}
    core = masks['core83_raw']
    intersections = {'k_density':int((masks['k_native']&df.density_kg_m3.notna()).sum())}
    for label,cols in {
        'core_plus_phi':['phi_observed'], 'core_plus_BET':['BET_m2_g'],
        'core_plus_phi_BET':['phi_observed','BET_m2_g'],
        'core_plus_phi_BET_identity_drying':['phi_observed','BET_m2_g','precursor','drying_method'],
        'core_plus_phi_BET_quantified_drying':['phi_observed','BET_m2_g','precursor_M','drying_method'],
        'core_plus_T_pressure':['measurement_temperature_K','measurement_pressure_Pa'],
    }.items():
        m = core & df[cols].notna().all(axis=1)
        intersections[label] = dict(n=int(m.sum()),papers=int(df.loc[m,'paper_id'].nunique()))
    summary=dict(raw_rows=len(df),raw_papers=int(df.paper_id.nunique()),raw_sha256=RAW_HASH,
      counts=counts,intersections=intersections,k_unit_flags=int(df.k_unit_flag.sum()),
      both_pore_metrics_in_core=int((core&df.diameter_nm.notna()&df.size_nm.notna()).sum()),
      measurement_T_p_available=False,
      processing_temperature_available_in_k193=int(raw.loc[masks['k_native'],'Drying Temp (°C)'].map(present).sum()),
      processing_pressure_available_in_k193=int(raw.loc[masks['k_native'],'Drying Pressure (MPa)'].map(present).sum()),
      suspicious_header='Drying Pressure (MPa) is duplicated; duplicate kept separately',
      caveat='Header-based unit conversions only. No high-k automatic correction. Screened rows are provisional, not source-validated.',
      log_events=len(logs))
    summary['duplicate_core_feature_label_within_paper']=duplicates
    save_json(ROOT/'results/tables/no2_audit_summary.json',summary)
    save_json(ROOT/'data/raw/SHA256SUMS.json',{'P16_Silica_Aerogel_raw.xlsx':RAW_HASH})
    text = f'''# 数据清洗记录（程序生成）

原表 {len(df)} 行、{summary['raw_papers']} 个标准化论文标题。原文件只读、SHA256 校验通过。并未删除原表的任何记录。

1. Excel 原生有限数值才进入数值列；范围、文字、单位字符串与不等式保留在事件日志，作为未解析，不取平均、不去不等号。
2. 明示单位：g/cm³ → kg/m³ ×1000；百分孔隙率 → 分数 ×0.01。k 按 W/mK 表头暂读；nm 保持 nm，没有凭数值猜测 nm/μm。
3. {summary['k_unit_flags']} 条 k>1 暂时标记单位待核验，值不改。它们在 raw/k_native/core83_raw 中保留，在 core_screened 中排除。不是确认实验异常，也不是全部 ÷1000。
4. pore_nm 优先 diameter，缺失时用 size，并保留 pore_metric 和两个原数值。指标语义不同是实质限制。
5. 测量 T、p 原表没有独立字段，保持缺失。干燥 T、p 是工艺条件，不能当成导热测试条件。
6. precursor 有名称仅表示身份信息；浓度只有主硅前驱体的浓度，不能称完整配方。未报告 co-precursor 不等于不存在。
7. 数值实验不做目标均值填补。No.2 主实验采用 k+density+pore 完整行；训练时的派生 phi 用 2200 kg/m³ 骨架密度，只是条件场景假设。

子集计数：

```json
{__import__('json').dumps(counts,ensure_ascii=False,indent=2)}
```

逐事件原值→新值→理由见 `cleaning_events.csv`；逐行归属见 `no2_audited_all.csv` 的 dataset_membership；原始论文标题和材料 ID 均保留。异常队列见 `unit_review_queue.csv`。
'''
    (out/'data_cleaning_log.md').write_text(text,encoding='utf-8')
    return summary
