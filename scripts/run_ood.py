"""Run fixed light OOD diagnostics; never rewrites Phase 3 numerical results."""
import json, time
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import roc_auc_score
import _bootstrap
from src.common import ROOT, config, save_json, sha256, environment
from src.models.ml import estimator
from src.physics.thermal_models import fit_bruggeman, predict_bruggeman
from src.evaluation.ood import DistanceReference, tree_spread, calibration_threshold


def run():
    started=time.perf_counter();cfg=config('phase3');audit=config('ood')
    out=ROOT/'results/ood';out.mkdir(exist_ok=True)
    paths=[ROOT/'configs/no1.json',ROOT/'configs/phase3.json',ROOT/'data/processed/no1_samples.csv',
           ROOT/'results/phase3/tables/metrics_summary.csv',ROOT/'results/phase3/tables/splits.json']
    before={str(p.relative_to(ROOT)):sha256(p) for p in paths}
    indexed=pd.read_csv(paths[2]).set_index('sample_id',drop=False)
    plans=json.loads(paths[-1].read_text())['splits']
    plans=[p for p in plans if p['fraction']==1.]
    records=[];scores=[];split_records=[];features=cfg['A2']
    for p in plans:
        pool=indexed.loc[p['train_ids']].reset_index(drop=True);test=indexed.loc[p['test_ids']].reset_index(drop=True)
        # Fixed OOD geometry partitions across forest seeds. IID repeats retain
        # their distinct outer splits, with reproducible inner calibration.
        inner_seed=(p['seed'] if p['protocol']=='grouped_in_distribution' else cfg['seed'])+audit['calibration_seed_offset']
        fit_i,cal_i=next(GroupShuffleSplit(n_splits=1,test_size=audit['calibration_fraction'],random_state=inner_seed).split(pool,groups=pool.geometry_group))
        fit=pool.iloc[fit_i];cal=pool.iloc[cal_i]
        group_sets=[set(d.geometry_group) for d in [fit,cal,test]]
        assert not any(group_sets[i]&group_sets[j] for i,j in [(0,1),(0,2),(1,2)])
        split_records.append(dict(protocol=p['protocol'],seed=p['seed'],fit_ids=fit.sample_id.tolist(),
                                  calibration_ids=cal.sample_id.tolist(),test_ids=test.sample_id.tolist(),
                                  fit_groups=len(group_sets[0]),calibration_groups=len(group_sets[1]),test_groups=len(group_sets[2]),group_overlap=0))
        distance=DistanceReference().fit(fit[features]);nn_cal=distance.score(cal[features]);nn_test=distance.score(test[features])
        params=fit_bruggeman(fit,fit.k_fvm.to_numpy())
        phys_fit=predict_bruggeman(fit,params);phys_cal=predict_bruggeman(cal,params);phys_test=predict_bruggeman(test,params)
        for name in ['RF','Hybrid']:
            target=fit.k_fvm.to_numpy()-(phys_fit if name=='Hybrid' else 0)
            forest=estimator('RF',cfg,p['seed']).fit(fit[features],target)
            local=[]
            for role,d,nn,physics in [('calibration',cal,nn_cal,phys_cal),('test',test,nn_test,phys_test)]:
                pred=forest.predict(d[features])+(physics if name=='Hybrid' else 0)
                f=pd.DataFrame(dict(protocol=p['protocol'],seed=p['seed'],model=name,role=role,
                                    sample_id=d.sample_id.to_numpy(),geometry_group=d.geometry_group.to_numpy(),
                                    truth=d.k_fvm.to_numpy(),prediction=pred,nn_distance=nn,tree_std=tree_spread(forest,d[features])))
                f['absolute_error']=abs(f.prediction-f.truth);f['relative_error_pct']=100*f.absolute_error/abs(f.truth)
                scores.append(f);local.append(f)
            # Mother-level diagnostics: rotation pairs never count as independent.
            gc=local[0].groupby('geometry_group').agg(absolute_error=('absolute_error','mean'),relative_error_pct=('relative_error_pct','mean'),nn_distance=('nn_distance','max'),tree_std=('tree_std','max'))
            gt=local[1].groupby('geometry_group').agg(absolute_error=('absolute_error','mean'),relative_error_pct=('relative_error_pct','mean'),nn_distance=('nn_distance','max'),tree_std=('tree_std','max'))
            for method in audit['scores']:
                threshold=calibration_threshold(local[0][method].to_numpy(),cal.geometry_group.to_numpy(),audit['alert_quantile'])
                flags=gt[method]>threshold
                auc=roc_auc_score(np.r_[np.zeros(len(gc)),np.ones(len(gt))],np.r_[gc[method],gt[method]])
                rho=float(spearmanr(gt[method],gt.absolute_error).statistic) if gt[method].nunique()>1 else np.nan
                records.append(dict(protocol=p['protocol'],seed=p['seed'],model=name,method=method,
                                    threshold=threshold,calibration_alert_rate=float((gc[method]>threshold).mean()),
                                    test_alert_rate=float(flags.mean()),region_AUROC=float(auc),error_spearman=rho,
                                    test_score_median=float(gt[method].median()),calibration_score_median=float(gc[method].median()),
                                    test_MAE=float(gt.absolute_error.mean()),calibration_MAE=float(gc.absolute_error.mean()),
                                    test_MAPE_pct=float(gt.relative_error_pct.mean()),calibration_MAPE_pct=float(gc.relative_error_pct.mean()),
                                    flagged_MAE=float(gt.loc[flags,'absolute_error'].mean()),unflagged_MAE=float(gt.loc[~flags,'absolute_error'].mean())))
    runs=pd.DataFrame(records);runs.to_csv(out/'metrics_by_run.csv',index=False)
    combined=pd.concat(scores,ignore_index=True);combined.to_csv(out/'scores.csv',index=False)
    metrics=[c for c in runs.columns if c not in ['protocol','seed','model','method']]
    summary=runs.groupby(['protocol','model','method'])[metrics].agg(['mean','std']);summary.columns=['_'.join(c) for c in summary.columns];summary.reset_index().to_csv(out/'metrics_summary.csv',index=False)
    save_json(out/'splits.json',dict(config=audit,plans=split_records))
    after={str(p.relative_to(ROOT)):sha256(p) for p in paths};assert before==after
    save_json(out/'run_manifest.json',dict(config=audit,phase3_config=cfg,inputs=after,environment=environment(),
                                         canonical_results_unchanged=True,n_outer_plans=len(plans),n_metric_rows=len(runs),
                                         runtime_seconds=time.perf_counter()-started,group_overlap=0,
                                         interpretation='Diagnostic models use fit/cal/test; not replacements for full-fit Phase 3 models. Tree SD is not calibrated uncertainty.'))
    print(summary[['test_alert_rate_mean','region_AUROC_mean','error_spearman_mean','test_MAE_mean','test_MAPE_pct_mean']].to_string())
    print('OOD_DIAGNOSTIC_PASS; canonical 49 rows unchanged; seconds',round(time.perf_counter()-started,2))


if __name__=='__main__':run()
