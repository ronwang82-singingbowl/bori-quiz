#!/usr/bin/env python3
"""
把測驗結果編進網址，讓結果可以被還原。

起因：
  LINE 內建瀏覽器不給下載也不給長按存圖，所以上一版做了「用外部瀏覽器
  開啟」的引導。但 Ron 實測發現跳出去之後測驗從頭開始——結果沒了，
  等於白做工，比不能下載更糟。

解法：
  跳轉時把四題的答案帶在網址上（?a=1,4,6,6），載入時如果讀得到就
  直接進結果頁。順帶也讓結果本身變成可分享的網址。

  答案只是 1–8 的頻道編號，不含任何個人資料。

LINE 裡的優先順序也一併調整：
  截圖其實是最沒有摩擦的做法（圖本來就是 9:16 滿版，截出來就能用），
  所以把「直接截圖」講在前面，「用外部瀏覽器開啟」當作想要原始檔的人
  的備案。

必須在 add-share-button.py 與 add-story-image.py 之後執行。

用法：
  python3 tools/add-result-url.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "index.html")

HELPER = """
// 從網址讀回測驗結果。只有 1-8 的頻道編號，不含任何個人資料。
function answersFromURL() {
  try {
    const raw = new URLSearchParams(location.search).get('a');
    if (!raw) return null;
    const ids = raw.split(',').map(n => parseInt(n, 10))
                   .filter(n => Number.isInteger(n) && n >= 1 && n <= 8);
    return ids.length === getQuestions().length ? ids : null;
  } catch (e) { return null; }
}

"""


def main():
    src = open(PATH, encoding="utf-8").read()
    m = re.search(r'<script[^>]*type="__bundler/template"[^>]*>', src)
    start, end = m.end(), src.find("</script>", m.end())
    doc = json.loads(src[start:end].strip())

    if "answersFromURL" in doc:
        sys.exit("偵測到已經加過網址還原了，不重複執行。")
    if "saveImage" not in doc:
        sys.exit("請先執行 add-share-button.py 與 add-story-image.py")

    def once(old, new, what):
        if doc.count(old) != 1:
            sys.exit(f"{what} 錨點出現 {doc.count(old)} 次，預期 1 次")
        return doc.replace(old, new, 1)

    # 1) helper
    doc = once("const SHARE_LABEL_DEFAULT", HELPER + "const SHARE_LABEL_DEFAULT", "helper")

    # 2) 初始狀態改成看得懂網址
    doc = once("  state = {\n    view: 'gallery',",
               "  state = {\n    view: answersFromURL() ? 'result' : 'gallery',",
               "初始 view")
    doc = once("    qIndex: 0,\n    answers: [],\n    optionOrders: [],",
               "    qIndex: 0,\n    answers: answersFromURL() || [],\n    optionOrders: [],",
               "初始 answers")

    # 3) 跳外部瀏覽器時把答案一起帶過去，才不會要重測
    doc = once("        const u = new URL(location.href);\n"
               "        u.searchParams.set('openExternalBrowser', '1');",
               "        const u = new URL(location.href);\n"
               "        u.searchParams.set('a', this.state.answers.join(','));\n"
               "        u.searchParams.set('openExternalBrowser', '1');",
               "跳轉帶答案")

    # 4) LINE 的提示改成「截圖最快」，外部瀏覽器當備案
    doc = once("tip.textContent = inLine ? 'LINE 的瀏覽器不能存圖，請用外部瀏覽器開啟（或直接截圖也可以）'",
               "tip.textContent = inLine ? '這張圖就是限動尺寸——直接截圖最快。'\n"
               "                           + '想要原始檔的話，用下面的外部瀏覽器開啟（結果會保留）'",
               "LINE 提示")
    doc = once("main.textContent = inLine ? '用外部瀏覽器開啟' : '下載圖片';",
               "main.textContent = inLine ? '用外部瀏覽器開啟（可下載）' : '下載圖片';",
               "按鈕文字")

    new_raw = re.sub(r"</(?=script)", "<\\\\/",
                     json.dumps(doc, ensure_ascii=False), flags=re.I)
    open(PATH, "w", encoding="utf-8").write(src[:start] + new_raw + src[end:])
    print(f"✓ 已修改 {PATH}")


if __name__ == "__main__":
    main()
