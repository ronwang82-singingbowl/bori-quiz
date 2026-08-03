#!/usr/bin/env python3
"""
文案批次一：讓第一次來的人看得懂。

改兩處，都不動題目本身：

(1) 著陸頁的副標
    原本：「平時的樣子，等權重並排，沒有哪一個特別被放大。」
    「等權重並排」「被放大」是設計者的語言——你知道它在說「這是還沒
    測的預設狀態」，第一次來的人只看到八個沒見過的詞配一句聽不懂的話。
    而且沒交代要花多久、有幾題，心理測驗的轉換率很吃這個。

(2) 結果頁補一句「為什麼是好幾個」
    結果會給 2-3 個角色，但從頭到尾沒解釋為什麼不是一個。
    一般人做過的測驗都是「你是 XX 型」，突然給三個會困惑。

刻意沒有動的：
    角色名（地脈、空鏡…）雖然是自創詞，但每個下面都配了白話的
    phrase，陌生感反而是記憶點。「這不是你的答案，是這次的天氣」
    也留著——它很美，而且真的有解釋功能。

用法：
  python3 tools/clarify-copy.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "index.html")

OLD_SUB = "平時的樣子，等權重並排，沒有哪一個特別被放大。"
NEW_SUB = ("8 種內在天氣，看你這陣子是哪一種。<br>"
           "4 個問題，大約 1 分鐘。沒有對錯，也不用留任何資料。")

# 結果頁：在配對句與「這次的天氣」之間，補一句解釋為什麼是好幾個
OLD_P = ('<p style="font-size:14px; line-height:1.9; color:oklch(55% 0.04 55); '
         'margin:0;">{{ weatherSentence }}</p>')
NEW_P = ('<p style="font-size:14px; line-height:1.9; color:oklch(45% 0.06 50); '
         'margin:0;">通常不會只有一種——這是這次比較明顯的幾個。</p>\n'
         '        <p style="font-size:14px; line-height:1.9; '
         'color:oklch(55% 0.04 55); margin:0;">{{ weatherSentence }}</p>')


def main():
    src = open(PATH, encoding="utf-8").read()
    m = re.search(r'<script[^>]*type="__bundler/template"[^>]*>', src)
    start, end = m.end(), src.find("</script>", m.end())
    doc = json.loads(src[start:end].strip())

    if "通常不會只有一種" in doc:
        sys.exit("偵測到已經改過了，不重複執行。")

    def once(old, new, what):
        if doc.count(old) != 1:
            sys.exit(f"{what} 錨點出現 {doc.count(old)} 次，預期 1 次")
        return doc.replace(old, new, 1)

    doc = once(OLD_SUB, NEW_SUB, "著陸頁副標")
    doc = once(OLD_P, NEW_P, "結果頁補充句")

    new_raw = re.sub(r"</(?=script)", "<\\\\/",
                     json.dumps(doc, ensure_ascii=False), flags=re.I)
    open(PATH, "w", encoding="utf-8").write(src[:start] + new_raw + src[end:])
    print(f"✓ 已修改 {PATH}")


if __name__ == "__main__":
    main()
