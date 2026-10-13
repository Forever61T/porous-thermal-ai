"""NEW synthetic data, not the inaccessible original Wei/QSGS dataset.

Gaussian random fields define geometry; FVM independently solves the PDE for labels.
The Bruggeman baseline is NEVER used to generate labels.
"""
import time
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter
from src.common import ROOT,config,save_json,sha256
from src.features.build_features import descriptors
from src.physics.thermal_models import solve_fvm,bounds

def make_geometry(grid,phi,sigma,seed):
    field=gaussian_filter(np.random.default_rng(seed).normal(size=(grid,grid)),sigma=sigma,mode='wrap')
    nsolid=round((1-phi)*grid*grid)
    solid=np.zeros(grid*grid,dtype=bool)
    solid[np.argsort(field.ravel(),kind='stable')[-nsolid:]]=True
    return solid.reshape(grid,grid)

def generate_no1():
    cfg=config('no1');meta=ROOT/'data/interim/no1_generation_manifest.json'
    labels=ROOT/'data/processed/no1_samples.csv';images_path=ROOT/'data/interim/no1_images.npz'
    if meta.exists() and labels.exists() and images_path.exists():
        import json
        old=json.loads(meta.read_text())
        if old['config']!=cfg or old['images_sha256']!=sha256(images_path) or old['labels_sha256']!=sha256(labels):
            raise ValueError('No1 cache config/hash mismatch. Preserve it and explicitly regenerate in a separate experiment.')
        return dict(status='validated_cache',**old)
    started=time.perf_counter();records=[];images=[]
    for fi,(family,sigma) in enumerate(cfg['families'].items()):
        for pi,phi in enumerate(cfg['porosities']):
            for rep in range(cfg['replicates']):
                seed=cfg['seed']+fi*10000+pi*100+rep
                original=make_geometry(cfg['grid'],phi,sigma,seed)
                group=f'{family}_p{pi}_r{rep:02d}'
                for rot in [0,1]:
                    s=np.rot90(original,rot).copy()
                    image=np.repeat(np.repeat(s,cfg['label_refinement'],0),cfg['label_refinement'],1)
                    physics=solve_fvm(image,cfg['solid_k'],cfg['gas_k'])
                    row=dict(sample_id=f'{group}_rot{rot}',geometry_group=group,family=family,
                             target_porosity=phi,rotation_quarters=rot,generation_seed=seed,
                             **descriptors(s),**physics)
                    low,high=bounds(row['porosity'],cfg['solid_k'],cfg['gas_k'])
                    if not low-1e-8<=physics['k_fvm']<=high+1e-8:
                        raise AssertionError('FVM label violates series/parallel bounds')
                    if physics['flux_balance_relative']>1e-8:raise AssertionError('FVM energy imbalance')
                    records.append(row);images.append(s)
                if len(records)%30==0:print(f'No1 FVM labels: {len(records)}/360',flush=True)
    df=pd.DataFrame(records);df.to_csv(labels,index=False)
    np.savez_compressed(images_path,images=np.asarray(images,dtype=np.uint8),sample_ids=df.sample_id.to_numpy(dtype=str))
    # Predeclared numerical refinement audit: six stratified cases, same pixel geometry.
    selected=[0,2*cfg['replicates']*2,2*cfg['replicates']*4,
              2*cfg['replicates']*5,2*cfg['replicates']*10,2*cfg['replicates']*14]
    refinement=[]
    for i in selected:
        values=[]
        for factor in [1,2,4]:
            s=np.repeat(np.repeat(images[i],factor,0),factor,1)
            value=solve_fvm(s,cfg['solid_k'],cfg['gas_k'])
            values.append(value['k_fvm'])
            refinement.append(dict(sample_id=df.iloc[i].sample_id,factor=factor,grid=cfg['grid']*factor,**value))
        for entry in refinement[-3:]:
            entry['relative_to_4x']=abs(entry['k_fvm']-values[-1])/values[-1]
    pd.DataFrame(refinement).to_csv(ROOT/'results/tables/no1_mesh_refinement.csv',index=False)
    summary=dict(config=cfg,n_samples=len(df),n_independent_geometry_groups=int(df.geometry_group.nunique()),
        label_origin='This project: conservative FVM, 128x128; left/right Dirichlet, top/bottom insulated',
        geometry_origin='This project: thresholded Gaussian random fields plus 90-degree rotation pairs',
        authors_original_data=False,label_units='dimensionless k/kg; ks/kg=100',
        runtime_seconds=time.perf_counter()-started,images_sha256=sha256(images_path),labels_sha256=sha256(labels),
        max_flux_imbalance=float(df.flux_balance_relative.max()),
        max_2x_vs_4x_relative_error=float(max(e['relative_to_4x'] for e in refinement if e['factor']==2)),
        unconnected_solid_samples=int((df.solid_span_fraction==0).sum()))
    save_json(meta,summary);save_json(ROOT/'results/tables/no1_audit_summary.json',summary)
    return summary
