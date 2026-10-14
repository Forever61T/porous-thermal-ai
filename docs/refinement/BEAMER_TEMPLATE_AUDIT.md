# 浙江大学Beamer模板审计

核验日期2026-10-14。来源[qychen2001/ZJU-Beamer-Template](https://github.com/qychen2001/ZJU-Beamer-Template)，本次读取仓库README、Makefile、主题源码与提交记录，固定commit `a276635341cee0e5b31c5ac004a1999fb3c9785b`（2026-05-09，xcolor修复）。本轮不修改原PowerPoint。

| 项目 | 实际观察 | 本项目处理 |
|---|---|---|
| README | 提供XeLaTeX→BibTeX→XeLaTeX×2；记录Mac/TeX Live2025等兼容性 | 在实际M4/TeX Live2026编译，不仅引用作者声称 |
| 根LICENSE/API licenseInfo | 根文件缺失、API为null | 继续查文件级许可，不把null当最终判断 |
| zju_beamer.sty | Pim Vullers2009、光头哥2023、PhilFan2025署名；明确LPPL1.3c-or-later或GPL3-or-later | 原样使用；SHA256 `a87fab7468c9380d54cf0895b3afcafb223e8e6329b1be5e46d4a844c38bca3d`；不改成我们的MIT |
| 校徽/题字/background | 未核实独立再分发许可 | 保留本地来源记录；公开源包不重上传，提供固定来源下载器；不对标志授予CC BY |
| Makefile | init/clean含删除图件/PDF规则 | 没有调用；自行写只编译的build.sh |
| 视觉 | 浙江大学蓝色、页眉页脚、封面品牌和结构块 | 保留模板主体，仅替换课程内容、图和引用 |
| 实际结果 | XeTeX0.999998、TeX Live2026；22页 | 20正文+2文献；最终日志无undefined citation、Missing character或Overfull；渲染逐页检查 |

许可证全文与解释可查[LaTeX Project LPPL1.3c](https://www.latex-project.org/lppl/lppl-1-3c/)。该链接只支持主题文件许可，不证明所有品牌素材都可以任意再分发。

## 复用范围

复用了主题排版、色彩、页眉页脚、标题页和引用入口；科学图件由本项目冻结CSV重新排成汇报尺寸，未复制模板示例科研内容。原创源文件通过`fetch_theme.py`取固定上游文件，SHA256见`theme_manifest.json`；已有文件不同即停止，不悄悄替换。

带机构标识的Word/PDF及Beamer PDF留在课程交付目录；公开仓库同步原创文章Markdown、科学图件、TeX、BibTeX、脚本、来源说明和审计。未重新上传用户毕业模板、第三方论文全文、真实数据库逐行数据或上游品牌资产。v1.0.0保持不变，本轮准备含轻量OOD的v1.1.0候选，没有新Release；22页仅同步现有讨论和复现页。
