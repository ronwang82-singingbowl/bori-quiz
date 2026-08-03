#!/usr/bin/env python3
"""
文案批次三：修正兩個角色 phrase。

(1) 照心「先照見自己」→「從別人懂自己」
    oneLine 寫的是「你常常是先在別人身上，才看懂自己」——重點是
    「透過別人」。但 phrase 聽起來像「你直接看見自己」，把最關鍵的
    「別人」弄丟了。這是理解錯誤，不只是美感問題。
    順帶解掉一個衝突：空鏡的「鏡」和照心的「照見」都是鏡子隱喻，
    而水面倒影的圖其實被空鏡用走了。

(2) 空鏡「靜但醒著」→「靜著也醒著」
    八個 phrase 裡七個是五字，只有這個四字，在網格裡看得出來；
    結構也不同（其他是「器官／現象＋動作」，它是狀態描述）。

兩個都只在 getChannels() 出現一次，改一次就會連動到圖鑑頁、結果頁、
配對句與限動圖——那些地方都是讀同一個 phrase。

用法：
  python3 tools/clarify-copy-3.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "index.html")

EDITS = [
    ("phrase: '先照見自己'", "phrase: '從別人懂自己'", "照心 語意補回「別人」"),
    ("phrase: '靜但醒著'", "phrase: '靜著也醒著'", "空鏡 補成五字"),
]


def main():
    src = open(PATH, encoding="utf-8").read()
    m = re.search(r'<script[^>]*type="__bundler/template"[^>]*>', src)
    start, end = m.end(), src.find("</script>", m.end())
    doc = json.loads(src[start:end].strip())

    if "從別人懂自己" in doc:
        sys.exit("偵測到已經改過了，不重複執行。")

    for old, new, what in EDITS:
        if doc.count(old) != 1:
            sys.exit(f"「{what}」錨點出現 {doc.count(old)} 次，預期 1 次——已中止")
        doc = doc.replace(old, new, 1)
        print(f"  ✓ {what}")

    new_raw = re.sub(r"</(?=script)", "<\\\\/",
                     json.dumps(doc, ensure_ascii=False), flags=re.I)
    open(PATH, "w", encoding="utf-8").write(src[:start] + new_raw + src[end:])
    print(f"\n✓ 已修改 {PATH}")


if __name__ == "__main__":
    main()
