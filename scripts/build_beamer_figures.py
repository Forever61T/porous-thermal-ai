"""Redraw frozen result tables for Beamer; no training or new scientific scores."""
from pathlib import Path
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--project-root',type=Path,default=Path(__file__).resolve().parents[1])
parser.add_argument('--output-dir',type=Path)
args=parser.parse_args();P=args.project_root.resolve();F=args.output_dir or P/'slides/figures';F.mkdir(parents=True,exist_ok=True)
if not (P/'data/interim/no1_images.npz').exists():
 raise SystemExit('Run python scripts/run_all.py in the scientific repository first.')
T=P/'results/phase3/tables';m=pd.read_csv(T/'metrics_summary.csv');a=pd.read_csv(T/'ablation_summary.csv').set_index('ablation')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':16,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':220})
models=['Physics','CalibratedPhysics','PhysicsStructure3p','RF','Hybrid'];names=['Physics','Calibrated\n(1p)','Structure\n(3p)','RF','Hybrid'];colors=['#777777','#B77D30','#6A568F','#2478A7','#C65539']
for r,name in [('grouped_in_distribution','iid'),('middle_phi_interpolation','middle'),('high_phi_extrapolation','high'),('anisotropic_family_shift','family')]:
 d=m[(m.protocol==r)&(m.fraction==1)].set_index('model').loc[models];fig,ax=plt.subplots(figsize=(7.4,3.8));ax.bar(range(5),d.MAE_mean,yerr=d.MAE_std,color=colors,capsize=4)
 ax.set_xticks(range(5),names);ax.set_ylabel('MAE (k / k_p)');ax.set_ylim(0,float((d.MAE_mean+d.MAE_std).max())*1.25)
 for j,v in enumerate(d.MAE_mean):ax.text(j,v+max(d.MAE_mean)*.055,f'{v:.3f}',ha='center',fontsize=17)
 fig.tight_layout();fig.savefig(F/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(7.4,3.8));d=a.loc[['A0_porosity','A1_basic_geometry','A2_full_structure']];ax.bar(range(3),d.MAE_mean,yerr=d.MAE_std,color=['#909BA3','#80ABBB','#2478A7'],capsize=4);ax.set_xticks(range(3),['Porosity','+ size / interface','+ paths / direction']);ax.set_ylabel('RF MAE (k / k_p)');ax.set_ylim(0,7)
for j,v in enumerate(d.MAE_mean):ax.text(j,v+.6,f'{v:.3f}',ha='center',fontsize=18)
fig.tight_layout();fig.savefig(F/'ablation.pdf',bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(7.4,3.8));g=m.query('protocol == "grouped_in_distribution"')
for k,color in zip(['Physics','RF','Hybrid'],[colors[0],colors[3],colors[4]]):
 d=g[g.model==k].sort_values('fraction');ax.errorbar(100*d.fraction,d.MAE_mean,yerr=d.MAE_std,label=k,marker='o',capsize=3,color=color)
ax.set(xticks=[25,50,75,100],xlabel='Training pool (%)',ylabel='MAE (k / k_p)');ax.legend(ncol=3,fontsize=13);fig.tight_layout();fig.savefig(F/'learning.pdf',bbox_inches='tight');plt.close(fig)
z=np.load(P/'data/interim/no1_images.npz');ids=list(z['sample_ids'])
for rot in [0,1]:
 sid=f'anisotropic_p1_r00_rot{rot}';image=z['images'][ids.index(sid)];Image.fromarray(np.where(image,0,255).astype('uint8')).resize((512,512),Image.Resampling.NEAREST).save(F/f'pair{rot}.png')
print('Eight presentation figures generated from frozen data; no models fitted.')
