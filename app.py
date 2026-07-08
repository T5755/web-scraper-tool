"""网页爬虫 + 数据导出工具（支持 JS 渲染 & 自动翻页）· Streamlit 界面
运行：streamlit run app.py
"""
import io
import os

import pandas as pd
import streamlit as st

from scraper import (
    fetch_html,
    crawl_pages,
    parse_tables,
    parse_links,
    parse_selector,
    parse_text,
    _concat_tables,
    _concat_df,
    to_csv_bytes,
    to_excel_bytes,
    to_json_bytes,
)

SAMPLE = os.path.join(os.path.dirname(__file__), "sample.html")

st.set_page_config(page_title="网页爬虫工具", layout="wide")
st.title("🌐 网页爬虫 + 数据导出工具")
st.caption("输入网址即可抓取表格 / 链接 / 正文，支持 JS 动态页面与自动翻页，一键导出 CSV / Excel / JSON")

with st.sidebar:
    st.header("抓取设置")
    use_js = st.checkbox("🌐 浏览器渲染（JS 动态页面）", help="勾选后用无头浏览器渲染，适合电商/平台站；需先装 playwright")
    max_pages = st.number_input("自动翻页数（1=不翻页）", min_value=1, max_value=20, value=1)
    next_hint = st.text_input("下一页选择器（留空自动识别）", "", placeholder="如 .next a / a:contains('下一页')")

url = st.text_input("目标网址（留空 / 输入 demo 体验示例 / 输入 demo2 一键抓图书5页）", "")
mode = st.selectbox("抓取模式", ["提取表格", "提取链接", "按 CSS 选择器提取", "提取正文文本"])
selector = ""
if mode == "按 CSS 选择器提取":
    selector = st.text_input("CSS 选择器（如 .price, #list li, table td）", "")


def offer_download(name: str, df: pd.DataFrame):
    if df.empty:
        st.warning(f"{name}：未提取到数据")
        return
    st.dataframe(df)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(f"下载 {name} (CSV)", to_csv_bytes(df), f"{name}.csv", "text/csv")
    with col2:
        st.download_button(
            f"下载 {name} (Excel)", to_excel_bytes(df), f"{name}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with col3:
        st.download_button(f"下载 {name} (JSON)", to_json_bytes(df), f"{name}.json", "application/json")


if st.button("开始抓取", type="primary"):
    try:
        raw = url.strip().lower()
        with st.spinner("抓取中..."):
            if raw == "demo2":
                # 一键演示：自动抓 books.toscrape.com 前 5 页图书（书名+价格）
                pages = crawl_pages("http://books.toscrape.com/", max_pages=5)
                st.success(f"共抓取 {len(pages)} 页（books.toscrape.com 电商演示）")
                rows = []
                for _u, h in pages:
                    titles = parse_selector(h, ".product_pod h3 a")[".product_pod h3 a"].tolist()
                    prices = parse_selector(h, ".price_color")[".price_color"].tolist()
                    for t, p in zip(titles, prices):
                        rows.append({"书名": t, "价格": p})
                df = pd.DataFrame(rows)
                st.subheader("📚 图书清单（前 5 页 · 书名 + 价格）")
                offer_download("图书清单", df)
            else:
                if raw in ("", "demo"):
                    html = open(SAMPLE, encoding="utf-8").read()
                    pages = [("demo", html)]
                    st.info("使用内置示例页面演示（无网络也能跑）")
                else:
                    pages = crawl_pages(url, max_pages=int(max_pages), next_hint=next_hint, use_js=use_js)
                    st.success(f"共抓取 {len(pages)} 页")

                if mode == "提取表格":
                    all_tables = [(u, parse_tables(h)) for u, h in pages]
                    tables = _concat_tables(all_tables)
                    if not tables:
                        st.warning("未找到 <table> 表格")
                    for name, df in tables:
                        st.subheader(name)
                        offer_download(name, df)
                elif mode == "提取链接":
                    df = _concat_df(parse_links, pages)
                    st.subheader("提取链接")
                    offer_download("链接", df)
                elif mode == "按 CSS 选择器提取":
                    if not selector.strip():
                        st.error("请填写 CSS 选择器")
                    else:
                        df = _concat_df(lambda h: parse_selector(h, selector), pages)
                        st.subheader(f"选择器：{selector}")
                        offer_download("结果", df)
                else:
                    df = _concat_df(parse_text, pages)
                    st.subheader("正文文本")
                    offer_download("正文", df)

    except Exception as e:  # noqa: BLE001
        st.error(f"抓取失败：{e}")

st.divider()
st.caption("提示：抓取前请确认目标网站允许抓取（参考其 robots.txt），仅用于合法合规的数据获取。")
