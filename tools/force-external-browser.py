#!/usr/bin/env python3
"""
兩件事：
(1) 所有對外分享的測驗連結都帶 openExternalBrowser=1，
    從 LINE 點進來的人會直接落在預設瀏覽器，而不是 LINE 內建瀏覽器。
(2) 從網址還原結果時，自動捲到結論那一段。

為什麼要 (1)：
  LINE 內建瀏覽器不給下載、不給長按存圖。與其在裡面補救，不如一開始
  就別讓人落在那裡。openExternalBrowser=1 是 LINE 官方支援的參數，
  在非 LINE 環境只是一個被忽略的 query string，完全無害。

為什麼要 (2)：
  Ron 實測：跳出去之後畫面上滿滿都是八個插圖，看不到任何文字，
  以為頁面壞了。其實文字都在，只是被插圖擠到螢幕外。手機愈寬愈嚴重。

用法：
  python3 tools/force-external-browser.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "index.html")

SCROLL = """
// 從網址還原結果時，捲到結論那一段。
// 不然一進來滿螢幕都是插圖，看不到「這次比較有回應的線索是」，
// 會以為頁面壞掉（Ron 在 Android Chrome 上實際遇到）。
// 注意：不能掛 window 'load'——這支腳本是 bundler 在頁面載入之後才注入的，
// load 早就發生過了，掛上去永遠不會被呼叫（實測 scrollY 一直是 0）。
if (!window.__boriResultScroll) {
  window.__boriResultScroll = true;
  (function () {
    if (!answersFromURL()) return;
    setTimeout(function () {
      // 結論句是 <h1 class="serif">，裡面還包一層 <span class="sc-interp">，
      // 所以不能用「沒有子元素的 div」去找。
      var el = Array.prototype.slice.call(document.querySelectorAll('h1'))
        .filter(function (e) {
          return /這次比較有回應的線索是/.test(e.textContent);
        })[0];
      // 不用 behavior:'smooth'——一進來就該直接看到結論，
      // 而且平滑捲動在部分環境會被當成 no-op。
      if (el) el.scrollIntoView({ block: 'center' });
    }, 900);
  })();
}

"""


def main():
    src = open(PATH, encoding="utf-8").read()
    m = re.search(r'<script[^>]*type="__bundler/template"[^>]*>', src)
    start, end = m.end(), src.find("</script>", m.end())
    doc = json.loads(src[start:end].strip())

    if "__boriResultScroll" in doc:
        sys.exit("偵測到已經執行過了，不重複執行。")
    if "answersFromURL" not in doc:
        sys.exit("請先執行 add-result-url.py")

    def once(old, new, what):
        if doc.count(old) != 1:
            sys.exit(f"{what} 錨點出現 {doc.count(old)} 次，預期 1 次")
        return doc.replace(old, new, 1)

    # (1) 分享出去的連結帶 openExternalBrowser=1
    doc = once("const url = 'https://ronwang82-singingbowl.github.io/bori-quiz/?s=1';",
               "// 帶 openExternalBrowser=1：朋友從 LINE 點進來會直接落在預設瀏覽器，\n"
               "    // 不會卡在 LINE 內建瀏覽器（那裡不能下載也不能長按存圖）。\n"
               "    // 非 LINE 環境只是一個被忽略的參數，無害。\n"
               "    const url = 'https://ronwang82-singingbowl.github.io/bori-quiz/"
               "?s=1&openExternalBrowser=1';",
               "分享連結")

    # (2) 還原結果時捲到結論
    doc = once("const SHARE_LABEL_DEFAULT", SCROLL + "const SHARE_LABEL_DEFAULT", "捲動")

    new_raw = re.sub(r"</(?=script)", "<\\\\/",
                     json.dumps(doc, ensure_ascii=False), flags=re.I)
    open(PATH, "w", encoding="utf-8").write(src[:start] + new_raw + src[end:])
    print(f"✓ 已修改 {PATH}")


if __name__ == "__main__":
    main()
