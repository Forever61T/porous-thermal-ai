"""Scientific figures from saved predictions, not hand-entered scores."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from src.common import ROOT, config
from src.phase3.experiments import TABLES, OUT
from src.physics.thermal_models import solve_fvm, bruggeman

FIGURES=OUT/'figures'
COLORS={'Physics':'#777777','CalibratedPhysics':'#B77D30','PhysicsStructure3p':'#6A568F',
        'RF':'#2478A7','Hybrid':'#C65539','Ridge':'#48A389'}
NAMES={'Physics':'Physics (porosity)','CalibratedPhysics':'Physics (1p calibrated)',
       'PhysicsStructure3p':'Physics (3p structure)','RF':'RF (9 descriptors)',
       'Hybrid':'Physics + residual RF','Ridge':'Ridge (9 descriptors)'}
REGIONS={'grouped_in_distribution':'Grouped, in distribution',
         'middle_phi_interpolation':'Unseen middle porosity: 0.60',
         'high_phi_extrapolation':'High-porosity extrapolation: 0.90',
         'anisotropic_family_shift':'Unseen anisotropic family'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                     'axes.spines.right':False,'savefig.dpi':180})


def save(fig,name):
    fig.savefig(FIGURES/f'{name}.png',bbox_inches='tight')
    fig.savefig(FIGURES/f'{name}.pdf',bbox_inches='tight')
    plt.close(fig)


def box(ax,x,y,w,h,text,face='#F1F5F8',size=10):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.01',fc=face,ec='#B0BAC2',lw=1))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=size)


def build_figures(include_external=False):
    FIGURES.mkdir(parents=True,exist_ok=True)
    cfg=config('phase3'); m=pd.read_csv(TABLES/'metrics_summary.csv')
    a=pd.read_csv(TABLES/'ablation_summary.csv'); p=pd.read_csv(TABLES/'predictions.csv')
    df=pd.read_csv(ROOT/'data/processed/no1_samples.csv')
    fig,ax=plt.subplots(figsize=(12,5)); ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    boxes=[(.01,.65,.25,.25,'Generate binary geometry\nGaussian fields, 64 x 64\n180 mothers + 90-degree pairs'),
           (.37,.65,.25,.25,'Resolve heat equation\nFVM, 128 x 128\nk_s / k_p = 100'),
           (.73,.65,.25,.25,'Numerical reference\nk_eff from heat flux\nNOT measured aerogel data'),
           (.01,.12,.25,.30,'Geometry-only descriptors\nPorosity, paths, orientation\nNo temperature/flux inputs'),
           (.37,.12,.25,.30,'Fit on training mothers only\nPhysics / RF / residual Hybrid\nNo hyperparameter search'),
           (.73,.12,.25,.30,'Evaluate applicability\nAblation, sample size, regions\nMean +/- SD; limitations')]
    for args in boxes:box(ax,*args)
    for start,end in [((.26,.77),(.36,.77)),((.62,.77),(.72,.77)),((.13,.65),(.13,.43)),
                      ((.26,.27),(.36,.27)),((.62,.27),(.72,.27)),((.85,.65),(.51,.43)),((.85,.65),(.85,.43))]:
        ax.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle='->',color='#435466',lw=1.5))
    ax.text(.87,.54,'Test labels:\nscore only',fontsize=9,ha='left',va='center')
    ax.set_title('Method: morphology-resolved reference + physics/data comparison',pad=15,weight='bold')
    save(fig,'01_method_flow')

    # Rotation pair: identical porosity and length/interface summaries, different heat paths.
    z=np.load(ROOT/'data/interim/no1_images.npz'); ids=list(z['sample_ids'])
    pair=['anisotropic_p1_r00_rot0','anisotropic_p1_r00_rot1']
    fig,axs=plt.subplots(2,2,figsize=(10,9),layout='constrained')
    for j,sid in enumerate(pair):
        row=df[df.sample_id==sid].iloc[0]; image=z['images'][ids.index(sid)]
        resolved=solve_fvm(np.repeat(np.repeat(image,2,0),2,1),return_field=True)
        axs[0,j].imshow(image,cmap='gray_r',vmin=0,vmax=1)
        axs[0,j].set_title(f'Direction {j+1}: solid black, pore white\nphi={row.porosity:.5f}; k_FVM={row.k_fvm:.3f}')
        axs[0,j].set_xlabel('Heat flow: left (T=1) to right (T=0)')
        im=axs[1,j].imshow(resolved['temperature'],cmap='inferno',vmin=0,vmax=1)
        axs[1,j].set_title(f'Temperature field; porosity EMT={float(bruggeman(row.porosity)):.3f}\nsolid spanning fraction={row.solid_span_fraction:.3f}')
        for ax in axs[:,j]:ax.set_xticks([]);ax.set_yticks([])
    fig.colorbar(im,ax=list(axs[1,:]),label='Normalized temperature',shrink=.75)
    fig.suptitle('Same porosity, different conduction paths',weight='bold')
    save(fig,'02_rotation_and_temperature')

    fig,ax=plt.subplots(figsize=(8,4.6)); labels=['A0_porosity','A1_basic_geometry','A2_full_structure']
    vals=a.set_index('ablation').loc[labels]
    ax.bar(np.arange(3),vals.MAE_mean,yerr=vals.MAE_std,capsize=4,color=['#909BA3','#80ABBB','#2478A7'])
    ax.set_xticks(range(3),['A0: porosity','A1: + length / interface','A2: + paths / direction'])
    ax.set(ylabel='MAE (dimensionless k / k_p)',title='Geometry statistics alone do not recover conduction paths')
    for i,v in enumerate(vals.MAE_mean):ax.text(i,v+.35,f'{v:.3f}',ha='center')
    ax.set_ylim(0,max(vals.MAE_mean+vals.MAE_std)+1)
    fig.text(.12,.01,'10 grouped splits; RF settings fixed; bars = mean, whiskers = split SD',fontsize=9)
    save(fig,'03_structure_ablation')

    imp=pd.read_csv(TABLES/'permutation_summary.csv').sort_values('delta_MAE_mean')
    fig,axs=plt.subplots(1,2,figsize=(13,5))
    axs[0].barh(imp.feature,imp.delta_MAE_mean,xerr=imp.delta_MAE_std,color='#2478A7',capsize=3)
    axs[0].set(xlabel='Test MAE increase after permutation',title='Prediction importance (correlated inputs)')
    blocks=[f'without_block_{b}' for b in cfg['descriptor_blocks']]
    block=a.set_index('ablation').loc[blocks]; full=a.set_index('ablation').loc['A2_full_structure','MAE_mean']
    axs[1].barh(list(cfg['descriptor_blocks']),block.MAE_mean-full,color='#6A568F')
    axs[1].axvline(0,c='k',lw=.7);axs[1].set(xlabel='Mean MAE increase after block retraining',title='Removal diagnostic: path information matters')
    fig.tight_layout();save(fig,'04_descriptor_diagnostics')

    fig,ax=plt.subplots(figsize=(8.5,5)); g=m[m.protocol=='grouped_in_distribution']
    for model in ['Physics','CalibratedPhysics','PhysicsStructure3p','RF','Hybrid']:
        d=g[g.model==model].sort_values('fraction')
        ax.errorbar(100*d.fraction,d.MAE_mean,yerr=d.MAE_std,marker='o',capsize=3,color=COLORS[model],label=NAMES[model])
    ax.set(xlabel='Training pool used (%)',ylabel='MAE (dimensionless k / k_p)',xticks=[25,50,75,100],
           title='No consistent small-data advantage from this residual prior')
    ax.legend(fontsize=9);fig.text(.13,.01,'36 / 72 / 108 / 144 training mothers; 36 test mothers per split; 10 split seeds',fontsize=9)
    save(fig,'05_learning_curve')

    fig,axs=plt.subplots(2,2,figsize=(12,9))
    models=['Physics','CalibratedPhysics','PhysicsStructure3p','RF','Hybrid']
    for ax,(region,title) in zip(axs.flat,REGIONS.items()):
        d=m[(m.protocol==region)&(m.fraction==1)].set_index('model').loc[models]
        ax.bar(range(len(models)),d.MAE_mean,yerr=d.MAE_std,color=[COLORS[x] for x in models],capsize=3)
        ax.set_xticks(range(len(models)),['Raw\nphysics','1p\nphysics','3p\nphysics','RF','Hybrid'])
        ax.set(title=title,ylabel='MAE (k / k_p)')
        for j,v in enumerate(d.MAE_mean):ax.text(j,v+max(d.MAE_mean)*.035,f'{v:.3f}',ha='center',fontsize=9)
        ax.set_ylim(0,max(d.MAE_mean+d.MAE_std)*1.24)
    fig.suptitle('Performance depends on the prediction region',weight='bold')
    fig.text(.1,.015,'Top left: split SD. Other panels: fixed region, SD over forest seeds only (not independent OOD tasks).',fontsize=9)
    fig.tight_layout(rect=(0,.035,1,.95));save(fig,'06_prediction_regions')

    runs=pd.read_csv(TABLES/'metrics_by_run.csv'); r=runs[(runs.protocol=='grouped_in_distribution')&(runs.fraction==1)]
    fig,axs=plt.subplots(1,3,figsize=(13,4.5)); models=['Physics','CalibratedPhysics','PhysicsStructure3p','Ridge','RF','Hybrid']
    for ax,metric in zip(axs,['MAE','RMSE','R2']):
        ax.boxplot([r[r.model==model][metric].to_numpy() for model in models],tick_labels=['Raw','1p','3p','Ridge','RF','Hybrid'],showfliers=True)
        ax.set(title=metric,xlabel='Fixed models, 10 grouped splits')
        if metric!='R2':ax.set_ylabel('Dimensionless k / k_p')
    fig.suptitle('Split sensitivity (overlapping held-out groups; not independent trials)',fontsize=11)
    fig.tight_layout();save(fig,'07_repeated_validation')

    d=p[(p.protocol=='grouped_in_distribution')&(p.seed==cfg['seed'])&(p.fraction==1)&(p.model=='CalibratedPhysics')].merge(df[['sample_id','solid_span_fraction','anisotropy']],on='sample_id')
    fig,axs=plt.subplots(1,2,figsize=(11,4.5))
    for ax,feature in zip(axs,['solid_span_fraction','anisotropy']):
        sc=ax.scatter(d[feature],d.physics_residual,c=d.target_porosity,cmap='viridis',s=24)
        ax.axhline(0,c='gray',lw=1);ax.set(xlabel=feature,ylabel='FVM - calibrated physics',title='Geometry-dependent analytical model error')
    fig.colorbar(sc,ax=list(axs),label='Porosity',shrink=.8)
    save(fig,'08_residual_structure')

    if include_external:
        real=pd.read_csv(ROOT/'data/processed/no2_core_screened.csv'); stats=pd.read_csv(TABLES/'reality_correlations.csv')
        fig,axs=plt.subplots(2,2,figsize=(12,8)); paper_colors={pid:i for i,pid in enumerate(sorted(real.paper_id.unique()))}
        for ax,(_,row) in zip(axs.flat,stats.iterrows()):
            d=real.copy()
            if row.subset in ['diameter','size']:d=d[d.pore_metric==row.subset]
            d=d.dropna(subset=[row.feature,'k_W_mK'])
            ax.scatter(d[row.feature],1000*d.k_W_mK,c=d.paper_id.map(paper_colors),cmap='tab20',vmin=0,vmax=19,s=30,alpha=.85)
            xlabels={'density_kg_m3':'Density (kg / m^3)','phi_observed':'Recorded porosity','pore_nm':'Pore indicator (nm)'}
            ax.set(xlabel=xlabels[row.feature],ylabel='Measured k (mW / m K)',
                   title=f'{row.subset}: n={int(row.n_rows)}, papers={int(row.n_papers)}\npooled Spearman={row.pooled_spearman:.3f}')
        fig.suptitle('External reality check: descriptive trends, not transfer validation',weight='bold')
        fig.text(.1,.01,'Colors distinguish papers. Measurement T / p missing for all rows. Pore indicators remain separated.',fontsize=9)
        fig.tight_layout(rect=(0,.035,1,.95));save(fig,'09_reality_check')

    fig,ax=plt.subplots(figsize=(13,7));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    box(ax,.07,.79,.86,.13,'Prediction request: is it inside the sampled geometry / porosity domain?\nFirst check physical assumptions, phase contrast and descriptor coverage.',size=12)
    columns=[(.02,'Pure RF','Same generated families / porosity levels\n10-split MAE = '+f"{m.query('protocol == \"grouped_in_distribution\" and fraction == 1 and model == \"RF\"').MAE_mean.iloc[0]:.3f}"+'\n\nPath descriptors supply the main gain.\nRF and Hybrid are nearly tied here.\nSmall-data benefit of Hybrid not stable.','#DFEDF5'),
             (.35,'Hybrid (conditional)','Unseen middle porosity 0.60\nMAE RF / Hybrid = '+f"{m.query('protocol == \"middle_phi_interpolation\" and model == \"RF\"').MAE_mean.iloc[0]:.3f} / {m.query('protocol == \"middle_phi_interpolation\" and model == \"Hybrid\"').MAE_mean.iloc[0]:.3f}"+'\n\nSmooth physical backbone helps here.\nResidual must remain transferable.\nNot a universal OOD improvement.','#FAE9E3'),
             (.68,'Physics (conditional)','High porosity, pore-phase limit\nRaw physics MAE = '+f"{m.query('protocol == \"high_phi_extrapolation\" and model == \"Physics\"').MAE_mean.iloc[0]:.3f}"+'\n\n3p shape physics best on family shift.\nPorosity-only physics misses direction.\nNeed valid physics + shape assumptions.','#EDE8F3')]
    for x,title,txt,face in columns:
        box(ax,x,.24,.30,.46,title+'\n\n'+txt,face,size=10)
        ax.annotate('',xy=(x+.15,.71),xytext=(.5,.79),arrowprops=dict(arrowstyle='->',color='#435466'))
    box(ax,.07,.03,.86,.12,'Real aerogel outside this map: 3D / Knudsen / radiation / temperature / contact effects absent.\nUnknown physics or distant geometry -> obtain new reference data; do not trust a leaderboard.',size=11)
    ax.set_title('AI / Physics Applicability Map — evidence from this idealized 2D dataset',weight='bold',pad=15)
    save(fig,'10_applicability_map')

    mesh=pd.read_csv(TABLES/'mesh_audit_30_cases.csv'); d=mesh[mesh.factor==2]
    fig,ax=plt.subplots(figsize=(8,4.5))
    for family,color in zip(['fine','coarse','anisotropic'],['#2478A7','#48A389','#C65539']):
        v=d[d.family==family];ax.scatter(v.target_porosity,100*v.relative_to_256,label=family,color=color,s=45,alpha=.75)
    ax.set(xlabel='Target porosity',ylabel='|k_128 - k_256| / k_256 (%)',title='30-case numerical refinement audit (unchanged pixel geometry)')
    ax.legend();save(fig,'11_numerical_refinement')
