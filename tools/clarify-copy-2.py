#!/usr/bin/env python3
"""
文案批次二：修掉會讓人停頓的題目用字。

以「第一次來、沒接觸過」的角度重讀後，這些是會造成誤解或作答偏誤的
地方。都是題目內容，屬於創作範圍，Ron 逐條確認過才改。

一個連動點要注意：
  結果頁標題「這次比較有回應的線索是」在四個地方出現——結果頁本身、
  限動圖的繪製、自動捲動的搜尋字串、還有一段註解。改一個就得全改，
  否則限動圖會印舊字、自動捲動會找不到目標而失效。

用法：
  python3 tools/clarify-copy-2.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "index.html")

# (舊字串, 新字串, 說明, 預期出現次數)
EDITS = [
    # 第 4 題選項 8：長度是其他選項的三倍，句式也不同（其他是動作，這個是
    # 經歷），會造成選擇偏誤——有人自動跳過異常長的選項，有人反而覺得
    # 「講這麼詳細應該是我」。
    ("回想起或聽見別人的故事而被打動，才看懂自己",
     "聽別人的故事，才看懂自己", "第4題選項8 縮短", 1),

    # 第 3 題選項 8：其他七個都是「我察覺到 X」，只有這個是迴避。題目問
    # 「你怎麼發現的」，而這個答案是「我沒發現」，照心型的人反而不會選。
    ("開始不太想看自己",
     "看別人的事有感覺，才發現是自己", "第3題選項8 改成察覺", 1),

    # 第 2 題選項 8：「對著自己看一會兒」字面像照鏡子，實際是內省。
    ("對著自己看一會兒",
     "安靜地看看自己現在怎麼了", "第2題選項8 去歧義", 1),

    # 第 1 題選項 8：和選項 5「閉上眼睛時反而看見畫面」都用「看見」，
    # 難以分辨。照心的意思是「先在別人身上看懂自己」，原本完全沒帶到。
    ("先看見了自己的樣子",
     "像在看另一個人一樣看著自己", "第1題選項8 去混淆", 1),

    # 題幹用字
    ("慢慢把自己攤開", "慢慢把自己打開", "第4題題幹 攤開→打開", 1),
    ("被惹毛", "被踩到", "第1題題幹 語氣一致", 1),

    # 結果頁標題：「線索」暗示在解謎，但使用者不知道自己在找什麼。
    # 四處都要改（結果頁、限動圖、自動捲動選字、註解）。
    ("這次比較有回應的線索是", "這次比較有回應的是", "結果頁標題（含限動圖與捲動）", 4),
]


def main():
    src = open(PATH, encoding="utf-8").read()
    m = re.search(r'<script[^>]*type="__bundler/template"[^>]*>', src)
    start, end = m.end(), src.find("</script>", m.end())
    doc = json.loads(src[start:end].strip())

    if "聽別人的故事，才看懂自己" in doc:
        sys.exit("偵測到已經改過了，不重複執行。")

    for old, new, what, expect in EDITS:
        n = doc.count(old)
        if n != expect:
            sys.exit(f"「{what}」錨點出現 {n} 次，預期 {expect} 次——已中止，檔案未變動")
        doc = doc.replace(old, new)
        print(f"  ✓ {what}（{n} 處）")

    new_raw = re.sub(r"</(?=script)", "<\\\\/",
                     json.dumps(doc, ensure_ascii=False), flags=re.I)
    open(PATH, "w", encoding="utf-8").write(src[:start] + new_raw + src[end:])
    print(f"\n✓ 已修改 {PATH}")


if __name__ == "__main__":
    main()
