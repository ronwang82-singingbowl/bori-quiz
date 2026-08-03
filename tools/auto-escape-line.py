#!/usr/bin/env python3
"""
在 LINE 內建瀏覽器開啟時，自動轉到系統預設瀏覽器。

為什麼要自動：
  上一版是「分享出去的連結帶 openExternalBrowser=1」，但那要求每個
  貼連結的人都記得加參數——Ron 自己貼、別人轉貼、從 IG 簡介點進來，
  只要有一個環節漏掉就又卡回 LINE 內建瀏覽器。
  改成頁面自己判斷，任何入口都有效。

為什麼放在外層 <head> 最前面：
  這支腳本要在那包 157 KB 的 app 開始解析之前就執行，使用者才只會
  看到一瞬間的空白就跳走。放在 bundler 注入的 x-dc 裡太晚了。
  也刻意排在 GA 之前，避免同一次造訪被記成兩次瀏覽。

不會無限迴圈：
  轉出去的網址已經帶 openExternalBrowser=1，條件不成立就不會再轉。
  萬一 LINE 哪天不再理會這個參數、webview 自己載入了帶參數的網址，
  一樣因為條件不成立而停下來，最多就是停在 LINE 裡（跟現在一樣），
  不會反覆跳轉。

用法：
  python3 tools/auto-escape-line.py
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "index.html")

SNIPPET = """
<!-- ── 從 LINE 內建瀏覽器自動跳到預設瀏覽器 ──────────────────────
     LINE 的 webview 不給下載檔案、也不給長按存圖，測驗結果圖在裡面
     完全存不下來。與其在裡面補救，不如一進來就轉出去。
     openExternalBrowser=1 是 LINE 官方支援的參數。
     必須排在所有腳本之前，才能在 app 載入前就跳走。 -->
<script>
(function () {
  try {
    if (!/Line\\//i.test(navigator.userAgent)) return;      // 不在 LINE 就什麼都不做
    var u = new URL(location.href);
    if (u.searchParams.get('openExternalBrowser') === '1') return;  // 已經試過，別再轉
    u.searchParams.set('openExternalBrowser', '1');
    location.replace(u.toString());                          // replace：不留下上一頁
  } catch (e) { /* 舊瀏覽器沒有 URL 物件之類的，直接放過 */ }
})();
</script>
"""

ANCHOR = '<meta charset="utf-8">'


def main():
    src = open(PATH, encoding="utf-8").read()

    if "從 LINE 內建瀏覽器自動跳到預設瀏覽器" in src:
        sys.exit("偵測到已經加過了，不重複執行。")

    head_end = src.find("</head>")
    if src.count(ANCHOR) < 1 or src.find(ANCHOR) > head_end:
        sys.exit("找不到外層 <head> 裡的 charset 宣告")

    # 只動第一個（外層）——內層 bundler 樣板裡也有一個同樣的字串
    i = src.find(ANCHOR) + len(ANCHOR)
    new = src[:i] + SNIPPET + src[i:]

    # 確認插在 GA 之前
    ga = new.find("googletagmanager")
    mine = new.find("openExternalBrowser")
    assert mine < ga, "應該排在 GA 之前"

    open(PATH, "w", encoding="utf-8").write(new)
    print(f"✓ 已修改 {PATH}")
    print(f"  插入位置：外層 <head> 第 {src[:i].count(chr(10)) + 1} 行之後，GA 之前")


if __name__ == "__main__":
    main()
