# Mac 初学者复现说明

正式验证：MacBook Air M4 / Apple Silicon / macOS / CPU，Python 3.12.14。
不需要CUDA、Windows、MPS、Metal、PyTorch、XGBoost或SHAP。

## 1. 安装 Python 3.12

已有Python3.12可以先检查。若没有，使用 [Python官方macOS universal2安装包](https://www.python.org/downloads/release/python-31210/)。3.12.10是可取得的公开安装包；实际完整验证使用3.12.14，不冒称每个补丁版本都已测试。

打开“终端”，运行：

```bash
python3.12 --version
python3.12 -c "import platform; print(platform.machine())"
```

版本应是3.12.x，Apple Silicon原生环境应显示`arm64`。

## 2. 取得项目

安装Git后运行下面命令，或在GitHub点击Code → Download ZIP并解压：

```bash
git clone https://github.com/Forever61T/porous-thermal-ai.git
cd porous-thermal-ai
```

后续命令都在包含`README.md`和`requirements.txt`的项目根目录执行。

## 3. 创建与激活环境

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python --version
```

`.venv`隔离本项目的库。关闭终端后需要再次`cd`进入项目并激活环境。

## 4. 安装固定依赖

```bash
python -m pip install -r requirements.txt
python -m pip check
```

8个直接依赖：NumPy、pandas、SciPy、scikit-learn、Matplotlib、joblib、pytest、openpyxl。
openpyxl仅用于可选外部Excel审计；保留它是为了同一小环境支持该步骤。
25个完整依赖版本见`requirements-lock.txt`。没有GPU依赖。

## 5. 一次跑完

```bash
python scripts/run_all.py
```

默认重新生成360图/FVM标签，运行全部冻结No.1实验、30例网格检查、图件、9测试和49指标/70划分核对。
先前缓存会备份到`data/interim/reproduction_backups/`。不要修改`references/frozen_phase3/`。

No.1不需要外部数据下载。真实气凝胶数据库由于许可不明未随仓库分发；默认跳过这项附加检查。可选步骤见`docs/external_sources.md`。

## 6. 预期输出与成功标准

| 文件/提示 | 应看到什么 |
|---|---|
| `data/processed/no1_samples.csv` | 360行、180母结构；无量纲k/k_p |
| `data/interim/no1_images.npz` | 360幅二值图像的本地缓存 |
| `results/phase3/tables/metrics_summary.csv` | 49行，MAE/RMSE/R² mean/std/count |
| `results/phase3/tables/splits.json` | 70计划，母结构交叠为0 |
| `results/phase3/figures/` | 自动生成PNG/PDF；无可选现实图时有10类图 |
| 终端 | `9 passed`，最后`FULL_REPRODUCTION_PASS` |
| `results/reproduction/<UTC时间>/machine_record.json` | status=FULL_REPRODUCTION_PASS及实际耗时/版本 |

| 区域 | RF MAE | Hybrid MAE | 原Physics MAE | 3p Physics MAE |
|---|---:|---:|---:|---:|
| 同分布10次分组留出 | 1.656923 | 1.683911 | 5.130651 | 2.632313 |
| 未见中间φ=0.60 | 2.888052 | 1.416837 | 3.228 | 2.642 |
| 高φ=0.90外推 | 0.897441 | 0.391320 | 0.125473 | 0.123444 |
| 未见各向异性族 | 4.511952 | 4.937401 | 8.254209 | 3.174961 |

三位数表述用于阅读，完整参考CSV用于判定。容差atol=1e-6、rtol=1e-7；不强求所有机器逐字节一致。
原完整本地流程（含Excel审计）43.4秒；公开版排除了默认外部审计，首次独立重算实测38.5秒，证据见`docs/evidence/public_no1_replay.json`。耗时不含安装，也不是对其他机器的速度保证。

## 7. 如何分步调试

```bash
python scripts/audit_data.py
python scripts/run_phase3.py
python scripts/evaluate.py
python -m pytest -q
```

完整顺序中run_phase3已训练Physics/RF/Hybrid并绘图。`evaluate.py`只核对已有结果，单独PASS不表示从零重跑。
再次快速执行可用`python scripts/run_all.py --reuse-no1`，但首次展示建议默认重算FVM。

## 8. 出错时

先确认激活了`.venv`并在根目录。查看对应`console.log`和机器记录；保留报错，不改参考分数、不扩大容差。
CI只检验数值解析极限和泄漏测试，不宣称Ubuntu与M4所有模型分数逐位相同。
# 当前v1.1.0候选附加说明

正式平台仍为MacBook Air M4 CPU。主实验49行指标和70划分不变；原v1.0.0测试9项，本轮新增2项隔离检查，共11项。
需要连同轻量OOD扩展复现时，在已按下文建立的环境中执行：

```bash
python scripts/run_all.py --with-ood
python scripts/build_course_report.py
```

`results/ood/`应有16行汇总、40个fit/calibration/test计划、评分CSV及图。默认`run_all.py`继续只执行主科学流程；报告Markdown和Word/PDF排版为独立作者流程。没有CNN或GPU环境。

