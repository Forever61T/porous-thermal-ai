"""Fixed-model morphology experiments, not hyperparameter selection.

All implementation is our own. Reuses this project's Phase 2 solvers/estimators.
Group splitting follows sklearn GroupShuffleSplit; test-set permutation is a
prediction diagnostic, not a feature selection step. No author code is executed.
"""
import json
import math
import time
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from scipy.stats import spearmanr
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.inspection import permutation_importance
from src.common import ROOT, config, save_json, sha256, environment
from src.data.generate_no1 import generate_no1
from src.models.ml import estimator
from src.physics.thermal_models import bruggeman, fit_bruggeman, predict_bruggeman, solve_fvm, bounds

OUT = ROOT / 'results/phase3'
TABLES = OUT / 'tables'


def measures(y, pred):
    return dict(MAE=float(mean_absolute_error(y, pred)),
                RMSE=float(np.sqrt(mean_squared_error(y, pred))),
                R2=float(r2_score(y, pred)))


def summary(frame, keys, values=('MAE', 'RMSE', 'R2')):
    result = frame.groupby(keys, sort=False)[list(values)].agg(['mean', 'std', 'count'])
    result.columns = [f'{a}_{b}' for a, b in result.columns]
    return result.reset_index()


def write_csv(name, frame):
    frame.to_csv(TABLES / name, index=False)


def make_plans(df, cfg):
    ids = np.arange(len(df)); groups = df.geometry_group.to_numpy(); plans = []
    for repeat in range(cfg['group_repeats']):
        seed = cfg['seed'] + repeat
        tr, te = next(GroupShuffleSplit(n_splits=1, test_size=cfg['test_fraction'],
                                      random_state=seed).split(ids, groups=groups))
        order = np.random.default_rng(seed + 1000).permutation(np.unique(groups[tr]))
        for fraction in cfg['train_fractions']:
            chosen = order[:max(2, math.ceil(fraction * len(order)))]; sub = tr[np.isin(groups[tr], chosen)]
            plans.append(dict(protocol='grouped_in_distribution', seed=seed, fraction=fraction,
                              train_ids=df.iloc[sub].sample_id.tolist(), test_ids=df.iloc[te].sample_id.tolist()))
        conditions = {
            'middle_phi_interpolation': df.target_porosity == .6,
            'high_phi_extrapolation': df.target_porosity == .9,
            'anisotropic_family_shift': df.family == 'anisotropic',
        }
        for protocol, testmask in conditions.items():
            plans.append(dict(protocol=protocol, seed=seed, fraction=1.,
                              train_ids=df.loc[~testmask, 'sample_id'].tolist(),
                              test_ids=df.loc[testmask, 'sample_id'].tolist()))
    for p in plans:
        train = df.set_index('sample_id').loc[p['train_ids']]
        test = df.set_index('sample_id').loc[p['test_ids']]
        if set(train.geometry_group) & set(test.geometry_group):
            raise AssertionError('Mother structure crosses train/test')
        p.update(n_train=len(train), n_test=len(test), n_train_groups=train.geometry_group.nunique(),
                 n_test_groups=test.geometry_group.nunique(), n_overlapping_groups=0)
    return plans


def fit_core(train, test, cfg, seed):
    y = train.k_fvm.to_numpy(); features = cfg['A2']
    p1 = fit_bruggeman(train, y); p3 = fit_bruggeman(train, y, structure=True)
    cal_train = predict_bruggeman(train, p1); cal_test = predict_bruggeman(test, p1)
    rf = estimator('RF', cfg, seed).fit(train[features], y)
    ridge = estimator('Ridge', cfg, seed).fit(train[features], y)
    residual_rf = estimator('RF', cfg, seed).fit(train[features], y - cal_train)
    prediction = {
        'Mean': np.full(len(test), y.mean()),
        'Physics': bruggeman(test.porosity.to_numpy()),
        'CalibratedPhysics': cal_test,
        'PhysicsStructure3p': predict_bruggeman(test, p3),
        'Ridge': ridge.predict(test[features]),
        'RF': rf.predict(test[features]),
        'Hybrid': cal_test + residual_rf.predict(test[features]),
    }
    residual_test = test.k_fvm.to_numpy() - cal_test
    residual_train_pred = residual_rf.predict(train[features])
    residual_test_pred = prediction['Hybrid'] - cal_test
    diagnostics = dict(train_residual_std=float(np.std(y-cal_train)),
                       test_residual_std=float(np.std(residual_test)),
                       train_residual_R2=float(r2_score(y-cal_train, residual_train_pred)),
                       test_residual_R2=float(r2_score(residual_test, residual_test_pred)),
                       zero_residual_test_MAE=float(np.mean(np.abs(residual_test))),
                       learned_residual_test_MAE=float(np.mean(np.abs(residual_test-residual_test_pred))))
    params=dict(physics_1p=p1, physics_3p=p3)
    bundle=dict(rf=rf,ridge=ridge,residual_rf=residual_rf,parameters=params,features=features)
    return prediction, rf, params, diagnostics, bundle


def evaluate_real_data(cfg):
    """No No.2 training. Paper-level resampling for descriptive correlations."""
    df = pd.read_csv(ROOT/'data/processed/no2_core_screened.csv')
    # Only screened core. Recorded porosity, never porosity inferred from density.
    variables = [('density_kg_m3', 'all'), ('phi_observed', 'observed_only'),
                 ('pore_nm', 'diameter'), ('pore_nm', 'size')]
    rows=[]; paper_rows=[]
    rng = np.random.default_rng(cfg['seed'] + 30000)
    for feature, subset in variables:
        d = df.copy()
        if subset in ['diameter', 'size']: d = d[d.pore_metric == subset]
        d = d.dropna(subset=[feature, 'k_W_mK']); groups = list(d.groupby('paper_id', sort=True))
        x=d[feature].to_numpy(); y=d.k_W_mK.to_numpy()
        pooled=float(spearmanr(x, y).statistic)
        # Within-paper rank centering removes between-paper level differences,
        # but not variation in composition/conditions within each paper.
        xr=d.groupby('paper_id')[feature].rank(pct=True)
        yr=d.groupby('paper_id').k_W_mK.rank(pct=True)
        xc=xr-xr.groupby(d.paper_id).transform('mean'); yc=yr-yr.groupby(d.paper_id).transform('mean')
        den=np.sqrt(np.sum(xc**2)*np.sum(yc**2))
        within=float(np.sum(xc*yc)/den) if den > 0 else np.nan
        paper_means=d.groupby('paper_id')[[feature, 'k_W_mK']].mean()
        pm_rho=float(spearmanr(paper_means[feature], paper_means.k_W_mK).statistic)
        bs=[]
        for _ in range(cfg['bootstrap_repeats']):
            selected=rng.integers(0, len(groups), len(groups))
            b=pd.concat([groups[i][1] for i in selected], ignore_index=True)
            if b[feature].nunique()>1 and b.k_W_mK.nunique()>1:
                bs.append(float(spearmanr(b[feature], b.k_W_mK).statistic))
        low, high=np.quantile(bs, [.025, .975])
        rows.append(dict(feature=feature, subset=subset, n_rows=len(d), n_papers=len(groups),
                         pooled_spearman=pooled, centered_within_paper_rank_correlation=within,
                         equal_paper_mean_spearman=pm_rho, bootstrap_low=low, bootstrap_high=high,
                         n_T_known=int(d.measurement_temperature_K.notna().sum()),
                         n_p_known=int(d.measurement_pressure_Pa.notna().sum())))
        for paper, p in groups:
            valid=len(p)>=4 and p[feature].nunique()>1 and p.k_W_mK.nunique()>1
            paper_rows.append(dict(feature=feature, subset=subset, paper_id=paper, title=p.title.iloc[0],
                                   n=len(p), eligible_n4=valid,
                                   spearman=float(spearmanr(p[feature], p.k_W_mK).statistic) if valid else np.nan))
    write_csv('reality_correlations.csv', pd.DataFrame(rows))
    write_csv('reality_within_paper.csv', pd.DataFrame(paper_rows))


def mesh_check(df, cfg):
    z=np.load(ROOT/'data/interim/no1_images.npz')
    lookup={sid:i for i,sid in enumerate(z['sample_ids'])}; rows=[]
    selected=df[df.geometry_group.str.endswith('r00')]
    for _, record in selected.iterrows():
        image=z['images'][lookup[record.sample_id]]; case=[]
        for factor in [1, 2, 4]:
            refined=np.repeat(np.repeat(image, factor, 0), factor, 1)
            solved=solve_fvm(refined)
            case.append(dict(sample_id=record.sample_id, family=record.family,
                             target_porosity=record.target_porosity, factor=factor,
                             grid=64*factor, **solved))
        for row in case:
            row['relative_to_256']=abs(row['k_fvm']-case[-1]['k_fvm'])/case[-1]['k_fvm']
        if not np.isclose(case[1]['k_fvm'], record.k_fvm, rtol=1e-10, atol=1e-10):
            raise AssertionError('Stored label not reproduced')
        rows.extend(case)
    write_csv('mesh_audit_30_cases.csv', pd.DataFrame(rows))


def bootstrap_model_differences(predictions, cfg):
    """Conditional test-group uncertainty, not independent training replications."""
    first=predictions[(predictions.seed==cfg['seed']) & (predictions.fraction==1.)]
    rows=[]; rng=np.random.default_rng(cfg['seed']+20000)
    for protocol, d in first.groupby('protocol', sort=True):
        pivot=d.pivot(index=['sample_id', 'geometry_group', 'truth'], columns='model', values='prediction').reset_index()
        for model in ['Physics', 'CalibratedPhysics', 'PhysicsStructure3p', 'Hybrid']:
            diff=(abs(pivot[model]-pivot.truth)-abs(pivot.RF-pivot.truth))
            gd=diff.groupby(pivot.geometry_group).mean().to_numpy()
            indices=rng.integers(0, len(gd), (cfg['bootstrap_repeats'], len(gd)))
            sample=gd[indices].mean(axis=1); lo,hi=np.quantile(sample,[.025,.975])
            rows.append(dict(protocol=protocol, model=model, reference='RF',
                             delta_MAE=float(gd.mean()), bootstrap_low=float(lo), bootstrap_high=float(hi),
                             n_test_groups=len(gd), seed=cfg['seed']))
    write_csv('conditional_group_bootstrap.csv', pd.DataFrame(rows))


def run(include_external=False):
    started=time.perf_counter(); TABLES.mkdir(parents=True, exist_ok=True)
    cfg=config('phase3')
    # Preserve everything previously used to choose the course topic.
    frozen=[ROOT/'configs/no1.json', ROOT/'results/tables/metrics_summary.csv',
            ROOT/'results/tables/splits.json', ROOT/'data/processed/no1_samples.csv',
            ]
    if include_external:
        frozen.append(ROOT/'data/processed/no2_core_screened.csv')
    before={str(p.relative_to(ROOT)):sha256(p) for p in frozen}
    generate_no1()  # validates the old immutable cache/config
    df=pd.read_csv(ROOT/'data/processed/no1_samples.csv')
    plans=make_plans(df,cfg)
    save_json(TABLES/'splits.json', dict(config=cfg, data_sha256=sha256(ROOT/'data/processed/no1_samples.csv'), splits=plans))
    metrics=[]; predictions=[]; ablations=[]; permutations=[]; diagnostics=[]; params=[]; ranges=[]
    indexed=df.set_index('sample_id', drop=False)
    for i, plan in enumerate(plans):
        tr=indexed.loc[plan['train_ids']].reset_index(drop=True)
        te=indexed.loc[plan['test_ids']].reset_index(drop=True)
        key={k:plan[k] for k in ['protocol','seed','fraction','n_train','n_test','n_train_groups','n_test_groups']}
        y=te.k_fvm.to_numpy()
        pred,rf,p,d,bundle=fit_core(tr,te,cfg,plan['seed']); params.append(dict(**key,**p)); diagnostics.append(dict(**key,**d))
        if plan['seed']==cfg['seed'] and plan['fraction']==1.:
            model_dir=OUT/'models';model_dir.mkdir(exist_ok=True)
            joblib.dump(dict(**bundle,plan=plan),model_dir/f"{plan['protocol']}.joblib")
        low,high=bounds(te.porosity.to_numpy())
        for model,v in pred.items():
            metrics.append(dict(**key,model=model,**measures(y,v),
                                n_negative=int((v<0).sum()),n_bound_violations=int(((v<low-1e-8)|(v>high+1e-8)).sum())))
            predictions.append(pd.DataFrame(dict(protocol=plan['protocol'],seed=plan['seed'],fraction=plan['fraction'],
                                                model=model,sample_id=te.sample_id,geometry_group=te.geometry_group,
                                                family=te.family,porosity=te.porosity,target_porosity=te.target_porosity,
                                                truth=y,prediction=v,physics_residual=y-pred['CalibratedPhysics'])))
        if plan['fraction']==1.:
            for feature in cfg['A2']:
                ranges.append(dict(**key, feature=feature, train_min=tr[feature].min(),train_max=tr[feature].max(),
                                   test_min=te[feature].min(),test_max=te[feature].max(),
                                   test_fraction_outside_range=float(((te[feature]<tr[feature].min())|(te[feature]>tr[feature].max())).mean())))
        if plan['protocol']=='grouped_in_distribution' and plan['fraction']==1.:
            feature_sets={'A0_porosity':cfg['A0'], 'A1_basic_geometry':cfg['A1'], 'A2_full_structure':cfg['A2']}
            feature_sets.update({f'without_{f}':[x for x in cfg['A2'] if x!=f] for f in cfg['A2'] if f!='porosity'})
            feature_sets.update({f'without_block_{name}':[x for x in cfg['A2'] if x not in block]
                                 for name,block in cfg['descriptor_blocks'].items()})
            for name,fs in feature_sets.items():
                model=rf if name=='A2_full_structure' else estimator('RF',cfg,plan['seed']).fit(tr[fs],tr.k_fvm)
                ablations.append(dict(**key,ablation=name,n_features=len(fs),features=';'.join(fs),**measures(y,model.predict(te[fs]))))
            imp=permutation_importance(rf,te[cfg['A2']],y,n_repeats=cfg['permutation_repeats'],
                                       random_state=plan['seed'],scoring='neg_mean_absolute_error',n_jobs=1)
            for j,feature in enumerate(cfg['A2']):
                for repeat,val in enumerate(imp.importances[j]):
                    permutations.append(dict(seed=plan['seed'],feature=feature,repeat=repeat,delta_MAE=val))
            # Deterministic function of porosity added as a diagnostic, not tuned/selected.
            train_aug=tr[cfg['A2']].copy(); test_aug=te[cfg['A2']].copy()
            train_aug['physics_1p']=predict_bruggeman(tr,p['physics_1p']);test_aug['physics_1p']=pred['CalibratedPhysics']
            aug=estimator('RF',cfg,plan['seed']).fit(train_aug,tr.k_fvm)
            ablations.append(dict(**key,ablation='A2_plus_redundant_physics',n_features=10,
                                  features=';'.join(train_aug.columns),**measures(y,aug.predict(test_aug))))
        if (i+1)%7==0: print(f'Phase3 fixed experiment: {i+1}/{len(plans)} plans',flush=True)
    m=pd.DataFrame(metrics); pred=pd.concat(predictions,ignore_index=True); a=pd.DataFrame(ablations)
    write_csv('metrics_by_run.csv',m)
    write_csv('metrics_summary.csv',summary(m,['protocol','fraction','model']))
    write_csv('predictions.csv',pred)
    write_csv('ablation_by_run.csv',a)
    write_csv('ablation_summary.csv',summary(a,['ablation']))
    write_csv('permutation_by_run.csv',pd.DataFrame(permutations))
    # First average five permutations per split, then calculate across-split SD.
    pi=pd.DataFrame(permutations).groupby(['seed','feature'],as_index=False).delta_MAE.mean()
    write_csv('permutation_summary.csv',summary(pi,['feature'],('delta_MAE',)))
    write_csv('residual_diagnostics.csv',pd.DataFrame(diagnostics))
    write_csv('feature_ranges.csv',pd.DataFrame(ranges))
    write_csv('feature_spearman.csv',df[cfg['A2']+['k_fvm']].corr(method='spearman').reset_index())
    save_json(TABLES/'parameters.json',params)
    pivot=m.pivot(index=['protocol','seed','fraction'],columns='model',values='MAE')
    paired=pivot.reset_index()[['protocol','seed','fraction']].copy()
    for model in ['Physics','CalibratedPhysics','PhysicsStructure3p','Hybrid']:
        paired[model+'_minus_RF']=pivot[model].to_numpy()-pivot.RF.to_numpy()
    write_csv('paired_MAE_differences.csv',paired)
    full=pred[pred.fraction==1.].copy(); full['absolute_error']=abs(full.prediction-full.truth)
    sub=full.groupby(['protocol','seed','model','target_porosity','family'],as_index=False).absolute_error.mean()
    write_csv('subdomain_MAE.csv',sub)
    stratified=[]
    for phi,dphi in df.groupby('target_porosity'):
        for feature in cfg['A2'][1:]:
            value=float(spearmanr(dphi[feature],dphi.k_fvm).statistic) if dphi[feature].nunique()>1 else np.nan
            stratified.append(dict(target_porosity=phi,feature=feature,n=len(dphi),spearman=value))
    write_csv('no1_within_porosity_correlations.csv',pd.DataFrame(stratified))
    components=[]
    for plan in plans:
        if plan['fraction']!=1. or plan['seed']!=cfg['seed']:continue
        tr=indexed.loc[plan['train_ids']]
        d=pred[(pred.protocol==plan['protocol'])&(pred.fraction==1.)&(pred.seed==cfg['seed'])]
        pivot=d.pivot(index=['sample_id','truth'],columns='model',values='prediction').reset_index()
        for variable,values in [('truth',pivot.truth),('RF',pivot.RF),('CalibratedPhysics',pivot.CalibratedPhysics),
                                ('true_residual',pivot.truth-pivot.CalibratedPhysics),
                                ('learned_correction',pivot.Hybrid-pivot.CalibratedPhysics)]:
            components.append(dict(protocol=plan['protocol'],variable=variable,mean=float(values.mean()),
                                   std=float(values.std()),minimum=float(values.min()),maximum=float(values.max()),
                                   train_truth_min=float(tr.k_fvm.min()),train_truth_max=float(tr.k_fvm.max())))
    write_csv('prediction_components_first_seed.csv',pd.DataFrame(components))
    bootstrap_model_differences(pred,cfg)
    print('Phase3: 30-case numerical audit',flush=True)
    mesh_check(df,cfg)
    if include_external:
        evaluate_real_data(cfg)
    # Compare identical first-five runs against frozen Phase2, rather than rewrite old results.
    old=pd.read_csv(ROOT/'results/tables/metrics_by_split.csv')
    mapping={'geometry_group':'grouped_in_distribution','porosity_ood':'high_phi_extrapolation','family_ood':'anisotropic_family_shift'}
    modelmap={'RF_structure':'RF','Hybrid_RF':'Hybrid','Ridge_structure':'Ridge',
              'Physics':'Physics','CalibratedPhysics':'CalibratedPhysics','PhysicsStructure3p':'PhysicsStructure3p','Mean':'Mean'}
    old=old[(old.dataset=='no1') & old.model.isin(modelmap)] .copy()
    old['protocol']=old.protocol.map(mapping);old['model']=old.model.map(modelmap)
    join=m.merge(old,on=['protocol','seed','fraction','model'],suffixes=('_new','_old'))
    maxdiff=max(float(np.max(abs(join[f'{metric}_new']-join[f'{metric}_old']))) for metric in ['MAE','RMSE','R2'])
    after={str(p.relative_to(ROOT)):sha256(p) for p in frozen}
    if before!=after:raise AssertionError('Phase2 frozen assets changed')
    if maxdiff>1e-9:raise AssertionError('Phase2 comparable results changed')
    save_json(TABLES/'run_manifest.json',dict(config=cfg,environment=environment(),
        frozen_phase2_hashes=after,phase2_matching_rows=len(join),phase2_max_metric_difference=maxdiff,
        code_hashes={str(p.relative_to(ROOT)):sha256(p) for p in sorted((ROOT/'src').rglob('*.py'))},
        inputs={str(p.relative_to(ROOT)):sha256(p) for p in ([ROOT/'data/interim/no1_images.npz'] + ([ROOT/'data/processed/no2_core_screened.csv'] if include_external else []))},
        n_plans=len(plans),n_predictions=len(pred),runtime_seconds=time.perf_counter()-started))
    print(f'Phase3 experiments complete: {time.perf_counter()-started:.1f} s; old results preserved.',flush=True)
