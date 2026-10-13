"""Phase 4 presentation/report authoring from frozen tables. No model fitting."""
from pathlib import Path
import json,shutil,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import _bootstrap
from src.common import ROOT
PROJECT=ROOT
FINAL=ROOT
TABLES=PROJECT/'results/phase3/tables'
FIG=ROOT/'reports/figures'
FIG.mkdir(parents=True,exist_ok=True)
METRICS=pd.read_csv(TABLES/'metrics_summary.csv')
ABLATION=pd.read_csv(TABLES/'ablation_summary.csv').set_index('ablation')
MODEL_NAMES={'Physics':'Physics','CalibratedPhysics':'Calibrated Physics',
             'PhysicsStructure3p':'Structure Physics (3p)','RF':'Pure ML (RF)','Hybrid':'Hybrid'}
COLORS=['#777777','#B77D30','#6A568F','#2478A7','#C65539']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':220})

def metric(region,model):return METRICS[(METRICS.protocol==region)&(METRICS.fraction==1)&(METRICS.model==model)].iloc[0]
def table(rows,headers):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(str(x) for x in r)+' |\n' for r in rows)
def pm(r,k='MAE'):return f'{r[k+"_mean"]:.3f} ± {r[k+"_std"]:.3f}'
def fig(name,caption):return f'\n![{caption}](figures/{name}.png)\n\n**{caption}。**\n'

def figures():
    reuse={'01_method_flow':'Figure1_method','02_rotation_and_temperature':'Figure2_FVM',
           '03_structure_ablation':'Figure3_ablation','10_applicability_map':'Figure8_applicability',
           '05_learning_curve':'AppendixA_learning','11_numerical_refinement':'AppendixB_mesh',
           '04_descriptor_diagnostics':'AppendixD_importance'}
    for old,new in reuse.items():
        for ext in ['png','pdf']:shutil.copy2(PROJECT/f'results/phase3/figures/{old}.{ext}',FIG/f'{new}.{ext}')
    # Refresh the learning-curve layout only; the frozen numbers are unchanged.
    f,ax=plt.subplots(figsize=(9,5.6));f.subplots_adjust(bottom=.23,top=.93)
    for name,color in zip(MODEL_NAMES,COLORS):
        d=METRICS[(METRICS.protocol=='grouped_in_distribution')&(METRICS.model==name)].sort_values('fraction')
        ax.errorbar(100*d.fraction,d.MAE_mean,yerr=d.MAE_std,marker='o',capsize=3,color=color,label=MODEL_NAMES[name])
    ax.set(xlabel='Training pool used (%)',ylabel='MAE in dimensionless k/k_p',xticks=[25,50,75,100],ylim=(1,7.4))
    ax.legend(loc='upper center',ncol=2,fontsize=10,frameon=False)
    f.text(.125,.045,'36 / 72 / 108 / 144 training mothers; 36 test mothers per split; 10 splits',fontsize=10)
    for ext in ['png','pdf']:f.savefig(FIG/f'AppendixA_learning.{ext}',bbox_inches='tight')
    plt.close(f)
    regions=[('grouped_in_distribution','Figure4_in_distribution','In distribution: mother-geometry group split'),
             ('middle_phi_interpolation','Figure5_middle_phi','Unseen middle porosity: phi = 0.60'),
             ('high_phi_extrapolation','Figure6_high_phi','High-porosity extrapolation: phi = 0.90'),
             ('anisotropic_family_shift','Figure7_family','Unseen anisotropic structural family')]
    for region,name,title in regions:
        models=list(MODEL_NAMES);rows=[metric(region,x) for x in models]
        means=[r.MAE_mean for r in rows];sd=[r.MAE_std for r in rows]
        f,ax=plt.subplots(figsize=(9,5.2))
        ax.bar(range(5),means,yerr=sd,capsize=4,color=COLORS)
        ax.set_xticks(range(5),['Physics','Calibrated\nPhysics','Structure\nPhysics (3p)','Pure ML\n(RF)','Hybrid'])
        ax.set(ylabel='MAE in dimensionless k/k_p',title=title,ylim=(0,max(np.array(means)+np.array(sd))*1.23))
        for i,v in enumerate(means):ax.text(i,v+max(means)*.055,f'{v:.3f}',ha='center')
        note='Mean +/- SD over 10 group splits; overlapping tests' if region=='grouped_in_distribution' else 'Fixed train/test region; SD over 10 forest seeds only'
        f.text(.12,.015,note,fontsize=10);f.tight_layout(rect=(0,.03,1,1))
        for ext in ['png','pdf']:f.savefig(FIG/f'{name}.{ext}',bbox_inches='tight')
        plt.close(f)


if __name__ == "__main__":
    figures()
    print("Report figures rebuilt from generated CSV tables; no model training.")
