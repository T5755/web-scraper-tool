"""网页爬虫核心逻辑：抓取 + 解析 + 导出 + JS渲染 + 自动翻页
支持四种模式：表格 / 链接 / CSS 选择器 / 正文文本
依赖：requests, beautifulsoup4, pandas
可选：playwright（开启"浏览器渲染"时需 pip install playwright && playwright install chromium）
"""

import io
import re
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


# ---------- 抓取 ----------

def fetch_html(url: str, timeout: int = 15) -> str:
    """普通抓取（静态页面，快）。"""
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.encoding = resp.apparent_encoding or "utf-8"
    resp.raise_for_status()
    return resp.text


def fetch_html_js(url: str, timeout: int = 20) -> str:
    """用无头浏览器抓取（支持 JS 动态渲染页面）。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "未安装 playwright。请执行：pip install playwright && playwright install chromium"
        )
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)  # 等 JS 把数据渲染出来
        html = page.content()
        browser.close()
    return html


# ---------- 自动翻页 ----------

_NEXT_KEYWORDS = ["下一页", "next", "›", ">", ">>"]


def find_next_url(html: str, base_url: str, hint: str = "") -> str | None:
    """在页面里找"下一页"链接，返回绝对地址；找不到返回 None。"""
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    if hint:
        for el in soup.select(hint):
            if el.get("href"):
                candidates.append(el["href"])
    else:
        for a in soup.find_all("a"):
            href = a.get("href")
            if not href:
                continue
            rel = a.get("rel")
            if rel and "next" in rel:
                candidates.append(href)
                continue
            txt = a.get_text(strip=True).lower()
            if any(k in txt for k in _NEXT_KEYWORDS):
                candidates.append(href)
    if not candidates:
        return None
    return urljoin(base_url, candidates[0])


def crawl_pages(start_url: str, max_pages: int = 1, next_hint: str = "",
                use_js: bool = False, timeout: int = 20):
    """从起始页开始，按 max_pages 自动翻页，返回 [(url, html), ...]。"""
    pages = []
    seen = set()
    url = start_url
    for _ in range(max(1, max_pages)):
        if url in seen:
            break
        seen.add(url)
        html = fetch_html_js(url, timeout) if use_js else fetch_html(url, timeout)
        pages.append((url, html))
        if len(pages) >= max(1, max_pages):
            break
        nxt = find_next_url(html, url, next_hint)
        if not nxt or nxt == url:
            break
        url = nxt
    return pages


# ---------- 解析 ----------

def parse_tables(html: str):
    """解析页面中所有 <table>，返回 [(名称, DataFrame), ...]。"""
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    result = []
    for i, table in enumerate(tables):
        rows = []
        for tr in table.find_all("tr"):
            cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
            if cells:
                rows.append(cells)
        if not rows:
            continue
        max_cols = max(len(r) for r in rows)
        rows = [r + [""] * (max_cols - len(r)) for r in rows]
        df = pd.DataFrame(rows[1:], columns=rows[0]) if len(rows) > 1 else pd.DataFrame(rows)
        result.append((f"表格{i + 1}", df))
    return result


def parse_links(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")
    data = []
    for a in soup.find_all("a"):
        text = a.get_text(strip=True)
        href = a.get("href")
        if href:
            data.append({"文本": text, "链接": href})
    return pd.DataFrame(data, columns=["文本", "链接"])


def parse_selector(html: str, selector: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")
    items = [el.get_text(strip=True) for el in soup.select(selector)]
    return pd.DataFrame({selector: items}, columns=[selector])


def parse_text(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text()).strip()
    return pd.DataFrame({"正文": [text]}, columns=["正文"])


# ---------- 多页聚合 ----------

def _concat_tables(all_tables):
    out, idx = [], 0
    for _, tables in all_tables:
        for _name, df in tables:
            idx += 1
            out.append((f"表格{idx}", df))
    return out


def _concat_df(get_df, pages):
    frames = []
    for _url, html in pages:
        df = get_df(html)
        if not df.empty:
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ---------- 导出 ----------

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


def to_json_bytes(df: pd.DataFrame) -> bytes:
    return df.to_json(force_ascii=False, orient="records").encode("utf-8")
