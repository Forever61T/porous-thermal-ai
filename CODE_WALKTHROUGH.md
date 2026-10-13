# 从哪开始读代码

先看 `README.md` 的四区域结果，再运行 `python scripts/run_all.py`。不要从随机一个作者 Notebook 开始。

| 顺序 | 文件 | 输入 → 输出 | 你要理解的事 |
|---|---|---|---|
| 1 | `configs/no1.json` | seed、φ、结构族、相导热率 → 数据生成规则 | 360图来自我们自己的生成器 |
| 2 | `scripts/audit_data.py` / `src/data/generate_no1.py` | 高斯随机场 → 二值图、9特征、FVM标签 | Bruggeman从未用于生成label |
| 3 | `src/features/build_features.py` | 二值图 → 孔隙率/贯通/方向/截面特征 | 特征没有读取温度、热流或标签 |
| 4 | `src/physics/thermal_models.py` | 图像 → 稀疏FVM；φ与形状参数 → EMT预测 | 有解析串并联和相极限测试 |
| 5 | `src/phase3/experiments.py:make_plans` | sample/group ID → 70计划 | 旋转对不能跨训练测试；固定区域不是10独立OOD |
| 6 | `src/phase3/experiments.py:fit_core` | 训练集 → Mean/Physics/校准/3p/Ridge/RF/Hybrid | 物理参数和残差仅用训练标签拟合 |
| 7 | `src/phase3/experiments.py:run` | 冻结协议 → 逐样本预测、消融/学习曲线/mean±SD | 不搜索超参数，不挑最漂亮的seed |
| 8 | `src/phase3/figures.py` | 数值CSV → PNG/PDF | 数据变动会反映到图里 |
| 9 | `scripts/evaluate.py` | 新结果 vs 冻结参考 → PASS或明确错误 | 49指标行/70划分全查，不只验一个R² |
| 10 | `tests/` | 数学极限/分组/标签隔离 → 9测试 | 正确性与是否高分是不同问题 |

## 哪些是作者代码，哪些是我们的

本仓库不包含第三方作者源代码。几何、特征、FVM、模型组织和验证代码都是课程项目独立实现，由Codex辅助完成。库内部的RF/Ridge由scikit-learn提供，通过pip安装，不把其实现称作原创。

外部工作借鉴的是：分组思路、物理形状参数思路、来源记录及清洗的审慎性。具体对应见 `docs/external_sources.md`；不是把下载仓库复制进来改名字。

## 结果文件怎么读

`metrics_by_run.csv`：一次模型/协议/seed的分数；`metrics_summary.csv`：同类运行mean/std/count。
`predictions.csv`：每个测试样本真值和预测；`splits.json`：确切训练/测试ID。
`ablation_summary.csv`：输入信息消融；`residual_diagnostics.csv`：残差可学性。
`parameters.json`：每个训练集拟合的1p/3p参数；`mesh_audit_30_cases.csv`：数值细化误差。
负R²、负预测和物理界限越界都保留，不因结果难看而删行。

## 最终文稿与图件的来源

`python scripts/build_report.py` 从模板和CSV重建报告Markdown，`python scripts/build_report_figures.py` 重建报告用图。它们不训练新模型。最终PDF是审阅后的版本文件；模型流程不依赖Chrome/PDF排版工具。模板和参考文献源在`reports/templates/`。
