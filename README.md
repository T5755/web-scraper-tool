# 🌐 网页爬虫 + 数据导出工具

> 一个带图形界面的网页数据采集工具：输入网址 → 自动解析表格 / 链接 / 正文 → 一键导出 CSV / Excel / JSON。
> 纯本地运行，0 成本，适合作为作品集项目，也能直接拿去接"帮我把网站数据扒下来"类的活。

## 功能

- ✅ 提取页面所有表格（自动转 DataFrame，支持多表格）
- ✅ 提取所有链接（文本 + href）
- ✅ 按 CSS 选择器精准提取（如 `.price`、`#list li`）
- ✅ 提取正文纯文本
- ✅ **浏览器渲染模式**：勾选后用无头浏览器抓取，支持 JS 动态页面（电商/平台站）
- ✅ **自动翻页**：设置翻页数，自动识别"下一页"并逐页采集
- ✅ 导出 CSV / Excel / JSON（带 BOM，Excel 中文不乱码）
- ✅ 内置示例页面，**无网络也能演示**

## 开启 JS 渲染（可选）

```bash
pip install playwright
playwright install chromium
```
界面勾选「🌐 浏览器渲染」即可抓取动态页面。
> ⚠️ 首次使用前必须装一次 chromium（`playwright install chromium`），否则勾选后会报 "未安装 playwright / 找不到浏览器"。

## 使用技巧

- **静态页面（表格/新闻/维基百科）**：不要勾 JS 渲染，速度更快更稳。
- **电商 / 平台站（数据靠 JS 异步加载）**：勾选「浏览器渲染」再抓。
- **多页列表（商品/帖子）**：把「自动翻页数」设成目标页数（如 10），工具会自动识别「下一页」逐页采集；若识别不准，在「下一页选择器」里填如 `.next a` 或 `a:contains('下一页')`。
- 抓完所有页的数据会自动聚合进同一张表再导出。

## 运行方式

```bash
pip install -r requirements.txt
streamlit run app.py
```

浏览器打开终端给出的地址（默认 http://localhost:8501）即可使用。
留空网址或输入 `demo` 即可用内置示例页面体验。

## 截图说明
<img width="1277" height="682" alt="屏幕截图 2026-07-08 130335" src="https://github.com/user-attachments/assets/a68f2e21-a267-4aae-87da-7170f777f730" />
<img width="1264" height="623" alt="屏幕截图 2026-07-08 130413" src="https://github.com/user-attachments/assets/2a4739aa-e96f-4962-9119-2ba872b07654" />
<img width="719" height="620" alt="屏幕截图 2026-07-08 130509" src="https://github.com/user-attachments/assets/ef7d503d-f0db-4926-9d25-8d2a38044352" />

1. 主界面：输入网址 + 选择抓取模式
2. 提取表格后：表格预览 + 三个下载按钮
3. 导出 Excel 打开效果

## 技术栈

Python · requests · BeautifulSoup4 · pandas · Streamlit

## 怎么用这个项目接单

客户常说："帮我把某某网站的数据弄下来给我。"
你当场演示这个工具，告诉他：

> "你给我网址，我帮你把数据自动抓成 Excel，干净、可筛选、能直接分析。"

报价参考：单页数据抓取 ¥100~300；多页/带反爬 ¥300~800。
**切记**：只抓允许抓取的公开数据，遵守目标站 robots.txt，不碰需登录的隐私数据。
