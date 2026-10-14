# 气凝胶启发的二维多孔介质导热预测

## 摘要

多孔绝热材料的导热预测常以孔隙率作为主要输入，但相同孔隙率下的骨架连通和方向差异仍可能改变传热路径。本工作生成360幅二维二值结构，以有限体积法计算稳态有效导热率，比较Bruggeman有效介质模型、校准及三参数结构物理模型、随机森林和物理模型加残差学习的混合模型。10次母结构分组留出中，加入结构描述符后，随机森林的平均绝对误差由4.817降至1.657；混合模型为1.684，未显示稳定的小数据优势。留出中间孔隙率φ=0.60时，混合模型误差为1.417，低于随机森林的2.888；在φ=0.90外推中，原有效介质模型误差为0.125，低于随机森林和混合模型。未见各向异性结构族时，三参数结构物理模型误差为3.175，优于两种森林模型。结构信息的预测收益主要来自贯通和方向关系，各模型的相对误差随预测区域变化。上述结果适用于固定两相导热率的理想二维问题，真实气凝胶数据库的有限趋势不能构成严格外部验证。

关键词：多孔介质；有限体积法；有效介质理论；随机森林；残差学习；模型适用域

## Abstract

Porosity alone does not specify the conduction paths in porous insulating materials. This study generates 360 binary two-dimensional structures and calculates their steady effective conductivity using the finite volume method. Bruggeman effective-medium predictions, calibrated and three-parameter structural physics models, random forests, and an additive physics-plus-residual model are compared under group-based evaluation. Across ten mother-structure splits, incorporating structural descriptors reduces the random-forest mean absolute error from 4.817 to 1.657. The residual hybrid gives 1.684 and shows no consistent small-data advantage. When the intermediate porosity of 0.60 is withheld, the hybrid error is 1.417, compared with 2.888 for the direct forest. For extrapolation to porosity 0.90, the uncalibrated effective-medium model gives an error of 0.125, lower than both forest models. On the unseen anisotropic family, the three-parameter structural physics model gives the lowest error among these models, at 3.175. All errors are dimensionless in conductivity normalized by the pore-phase conductivity. Spanning paths and orientation provide information that porosity omits, but their predictive benefit depends on the target domain. The benchmark represents an idealized two-dimensional conduction problem; the limited experimental aerogel trends do not establish simulation-to-experiment transfer.

Keywords: porous media; finite volume method; effective medium theory; random forest; residual learning; applicability domain
