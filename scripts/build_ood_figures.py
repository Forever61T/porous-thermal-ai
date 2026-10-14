"""Plot saved OOD diagnostics; no model fitting or score selection."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import _bootstrap
from src.common import ROOT

m=pd.read_csv(ROOT/'results/ood/metrics_summary.csv')
regions=['grouped_in_distribution','middle_phi_interpolation','high_phi_extrapolation','anisotropic_family_shift']
labels=['IID','Middle phi gap','High phi OOD','Unseen family']
fig,axes=plt.subplots(1,2,figsize=(11,4.3));colors=['#2478A7','#777777','#C65539']
for j,(model,method,label) in enumerate([('RF','nn_distance','Feature distance'),('RF','tree_std','RF tree SD'),('Hybrid','tree_std','Residual tree SD')]):
    d=m[(m.model==model)&(m.method==method)].set_index('protocol').loc[regions]
    axes[0].bar(np.arange(4)+(j-1)*.24,100*d.test_alert_rate_mean,.24,yerr=100*d.test_alert_rate_std,color=colors[j],label=label,capsize=2)
axes[0].set(ylabel='Mother-group alert rate (%)',ylim=(0,112));axes[0].legend(frameon=False,fontsize=8)
for j,(model,color) in enumerate([('RF','#2478A7'),('Hybrid','#C65539')]):
    d=m[(m.model==model)&(m.method=='nn_distance')].set_index('protocol').loc[regions]
    axes[1].bar(np.arange(4)+(j-.5)*.3,d.test_MAPE_pct_mean,.3,yerr=d.test_MAPE_pct_std,color=color,label=model,capsize=2)
axes[1].set(ylabel='Mean absolute relative error (%)');axes[1].legend(frameon=False)
for ax in axes:
    ax.set_xticks(np.arange(4),labels,rotation=15);ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
fig.suptitle('Exploratory fit/calibration/test models; not the full-fit Phase 3 scores',fontsize=11)
fig.tight_layout();dest=ROOT/'results/ood/figures';dest.mkdir(exist_ok=True)
for ext in ['png','pdf']:fig.savefig(dest/('ood_warning_diagnostics.'+ext),dpi=220,bbox_inches='tight')
plt.close(fig)
print('OOD figures built from saved CSV.')
