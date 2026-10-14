# 浙江大学课程汇报 Beamer

正文20页，参考文献2页。主实验科学结果对应porous-thermal-ai v1.0.0；v1.1.0候选新增轻量OOD诊断，仅同步讨论与复现页，CNN未执行。`main.tex`、`references.bib`与原创科学图件是本项目内容；模板主体`zju_beamer.sty`未修改。

## 在Mac上编译

需要XeLaTeX与BibTeX。本机已使用TeX Live2026/XeTeX0.999998编译成功。安装TeX发行版不属于Python requirements，也不需要GPU。

在终端进入这个`slides`文件夹。如果从GitHub或源文件压缩包取得，先取固定版本的主题文件：

```bash
python3 fetch_theme.py
sh build.sh
```

本地工作目录已有主题文件，可以直接`sh build.sh`。最终打开`main.pdf`。源包没有重新分发上游品牌图形；下载器从原始仓库获取4个固定文件、校验SHA256，不覆盖内容不同的已有文件。需要联网的步骤只有`fetch_theme.py`。

没有使用上游`make init`或`make clean`，因为它们包含删除图片/PDF的操作。本项目build脚本只调用XeLaTeX、BibTeX和两次XeLaTeX，不删除图件。

## 编辑位置

题目、汇报人、学院、日期在`main.tex`开头，姓名留空。正文使用冻结表中的数字；请不要手工改数以改善模型排名。科学图件在`figures/`；图表从冻结CSV生成，代码在`build_figures.py`（公开仓库对应`scripts/build_beamer_figures.py`）。该脚本不训练模型。源包独立使用时，在已运行过run_all的科学仓库旁执行：

```bash
python3 build_figures.py --project-root /path/to/porous-thermal-ai --output-dir figures
```

## 来源与许可

采用[qychen2001/ZJU-Beamer-Template](https://github.com/qychen2001/ZJU-Beamer-Template)，固定commit `a276635341cee0e5b31c5ac004a1999fb3c9785b`。根目录未发现LICENSE，但`zju_beamer.sty`文件头有LPPL1.3c-or-later/GPL3-or-later双许可与原作者署名，不能据根目录缺失就断言主题完全无许可。品牌素材没有单独许可证明，不将它们归入本项目MIT或CC BY4.0；公开源包使用来源下载方式。完整判断见上层`BEAMER_TEMPLATE_AUDIT.md`。

原创课程内容、数据图：CC BY4.0；原创构建脚本：MIT。最终带校徽PDF供课程汇报使用；其机构标识不因本文许可而获得额外授权。
