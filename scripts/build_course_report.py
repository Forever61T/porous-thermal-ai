from pathlib import Path
import pandas as pd,json,re,hashlib
import _bootstrap
from src.common import ROOT
P=ROOT;S=P/'reports/course_sections';T=P/'results/phase3/tables';M=pd.read_csv(T/'metrics_summary.csv');A=pd.read_csv(T/'ablation_summary.csv').set_index('ablation')
def row(region,model,f=1):return M[(M.protocol==region)&(M.model==model)&(M.fraction==f)].iloc[0]
def table(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rows)
g='grouped_in_distribution';names={'Physics':'原Physics','CalibratedPhysics':'1p校准','PhysicsStructure3p':'3p结构','RF':'RF','Hybrid':'Hybrid'}
tables={
'ablation_table':table(['输入','RF MAE mean ± SD'],[[label,f"{A.loc[k,'MAE_mean']:.3f} ± {A.loc[k,'MAE_std']:.3f}"] for k,label in [('A0_porosity','A0 孔隙率'),('A1_basic_geometry','A1 尺度与界面'),('A2_full_structure','A2 全结构')]]),
'iid_table':table(['模型','MAE','RMSE','R²'],[[names[k]]+[f'{row(g,k)[v+"_mean"]:.3f} ± {row(g,k)[v+"_std"]:.3f}' for v in ['MAE','RMSE','R2']] for k in names]),
'learning_table':table(['训练池','RF MAE','Hybrid MAE'],[[f'{int(f*100)}%']+[f'{row(g,k,f).MAE_mean:.3f} ± {row(g,k,f).MAE_std:.3f}' for k in ['RF','Hybrid']] for f in [.25,.5,.75,1]]),
'region_table':table(['区域','原Physics','3p结构','RF','Hybrid'],[[label]+[f'{row(r,k).MAE_mean:.3f}' for k in ['Physics','PhysicsStructure3p','RF','Hybrid']] for r,label in [('grouped_in_distribution','同分布'),('middle_phi_interpolation','φ=0.60缺口'),('high_phi_extrapolation','φ=0.90外推'),('anisotropic_family_shift','未见结构族')]])}
text='\n\n'.join(f.read_text().strip() for f in sorted(S.glob('[0-9][0-9]_*.md')))
for k,v in tables.items():text=text.replace('{{'+k+'}}',v.strip())

# Exploratory numerical claims are assembled from their separate saved CSV.
Q=pd.read_csv(P/'results/ood/metrics_summary.csv')
def ood(region,method='nn_distance'):
 return Q[(Q.protocol==region)&(Q.model=='RF')&(Q.method==method)].iloc[0]
regions=['grouped_in_distribution','middle_phi_interpolation','high_phi_extrapolation','anisotropic_family_shift']
values={
 'ood_nn_rates':'、'.join(f'{100*ood(r).test_alert_rate_mean:.1f}%' for r in regions[:-1])+'和'+f'{100*ood(regions[-1]).test_alert_rate_mean:.0f}%',
 'ood_nn_aucs':'、'.join(f'{ood(r).region_AUROC_mean:.3f}' for r in regions[:-1])+'和'+f'{ood(regions[-1]).region_AUROC_mean:.3f}',
 'ood_nn_rhos':f"{ood(regions[2]).error_spearman_mean:.3f}和{ood(regions[3]).error_spearman_mean:.3f}",
 'ood_nn_missed':f'{100*(1-ood(regions[2]).test_alert_rate_mean):.1f}',
 'ood_tree_high_auc':f"{ood(regions[2],'tree_std').region_AUROC_mean:.3f}",
 'ood_rf_high_mae':f'{ood(regions[2]).test_MAE_mean:.3f}',
 'ood_rf_iid_mae':f'{ood(regions[0]).test_MAE_mean:.3f}',
 'ood_rf_high_mape':f'{ood(regions[2]).test_MAPE_pct_mean:.1f}',
 'ood_rf_iid_mape':f'{ood(regions[0]).test_MAPE_pct_mean:.1f}'
}
for key,value in values.items():text=text.replace('{{'+key+'}}',value)

assert '{{' not in text
refs=(S/'references.md').read_text().strip();text+='\n\n# 参考文献\n\n'+refs
text+='''\n\n# 附录 复现与补充结果

正式平台为MacBook Air M4、macOS27.0、Python3.12.14、CPU。固定NumPy2.3.5、pandas2.2.3、SciPy1.16.2、scikit-learn1.7.2和Matplotlib3.10.7等8个直接依赖。运行python scripts/run_all.py可重建FVM标签、冻结模型、统计表和科学图件；49行主实验汇总、70个划分计划均与参考一致；原v1.0.0有9项测试，本轮新增2项隔离检查，共11项通过。GitHub新clone重算约38.6秒，依赖安装不计入耗时。

代码与合成数据公开于https://github.com/Forever61T/porous-thermal-ai。科学结果对应v1.0.0，commit cf9ab4bf12532dbe9890f39974dcaa968c7d4243；本轮文稿、Beamer和轻量OOD诊断准备为v1.1.0候选，尚未发布Release。实验作者数据及其逐行衍生结果按来源许可处理，公开版本不重新分发。代码和文稿由Codex辅助实现与整理，提交者应核对并按课程要求披露工具使用。

![图A.1 数据量实验](figures/AppendixA_learning.png)

**图A.1 训练母结构36、72、108和144；误差棒为划分标准差。**

![图A.2 网格细化](figures/AppendixB_mesh.png)

**图A.2 相同像素几何的128与256格差异，30个预选结构。**

![图A.3 描述符诊断](figures/AppendixD_importance.png)

**图A.3 相关特征的置乱和移除诊断，不代表独立因果贡献。**
'''
text+='\n\n![图A.4 可信域诊断](figures/AppendixE_ood.png)\n\n**图A.4 独立训练/校准/测试诊断模型的告警与相对误差；主实验指标不替换。固定偏移区域的误差棒仅为森林种子波动。**\n'
(P/'reports/Final_Course_Report.md').write_text(text)
# Keep original prose and new section sources independent, with a revision ledger.
meta={'sections_edited_sequentially':[f.name for f in sorted(S.glob('[0-9][0-9]_*.md'))],'metrics_sha256':hashlib.sha256((T/'metrics_summary.csv').read_bytes()).hexdigest(),'scientific_config_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [P/'configs/no1.json',P/'configs/phase3.json']},'old_report_preserved':True,'template_confirmation':'User confirmed course-report migration on 2026-10-14','chinese_characters':len(re.findall(r'[\u4e00-\u9fff]',text)),'new_experiments':'light OOD diagnostic only; canonical Phase 3 unchanged'}
(P/'docs/evidence/course_report_build.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print('Assembled edited sections:',meta['chinese_characters'],'Chinese characters; frozen tables used.')
