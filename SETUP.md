## 安装指南

### 软件版本
* python：Anaconda2-4.1.1-Windows-x86_64
* traits (4.5.0)
* traitsui (4.5.1)
* chaco (4.5.0)

### 软件安装
1. 安装python
2. 安装chaco
```bash
conda install chaco==4.5.0
```
3. 安装kiwisolver
```bash
conda install kiwisolver
```
4. 修复traitsui中ListEditor标签无法显示中文bug
```
# 文件位置: ${Anaconda_install_path}/Lib/site-packages/traitsui/qt4/list_editor.py
# 修复方法：
756: name = str( name ) or '???'
更改为
756: name = unicode(name) or '???'

```