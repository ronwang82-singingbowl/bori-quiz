#!/usr/bin/env python3
"""
在「內在天氣」測驗的結果頁加上分享按鈕。

為什麼：
  這種心理測驗最主要的擴散動力就是「曬結果」。原本結果頁只有
  「缽日官網」和「重新測驗一次」兩個出口，測完的人想分享只能自己
  複製網址，實際上不會有人這樣做——擴散的路徑等於是斷的。

做法：
  index.html 裡的 <script type="__bundler/template"> 是一段 JSON 編碼的
  字串，裡面包著整份內層文件（樣板 + x-dc 邏輯）。這支程式解碼、改完、
  再編碼回去，不動外層任何東西。

  分享優先用 Web Share API（手機會叫出系統分享選單，可直接送進 LINE），
  桌機沒有這個 API 就退回複製到剪貼簿。

冪等：重複執行會偵測到已經改過而中止，不會改壞。

用法：
  python3 tools/add-share-button.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "index.html")

QUIZ_URL = "https://ronwang82-singingbowl.github.io/bori-quiz/"

# ── 1. 分享按鈕的樣板標記 ────────────────────────────────────────
# 放在「缽日官網」下面，用外框樣式當次要按鈕，不跟主要 CTA 搶。
SHARE_BUTTON = (
    '\n          <button sc-camel-on-click="{{ shareResult }}" '
    'style="border:1px solid oklch(72% 0.05 150); background:none; '
    'color:oklch(32% 0.05 150); padding:12px 28px; border-radius:999px; '
    'font-size:14px; font-weight:600; cursor:pointer;" '
    'style-hover="background:oklch(93% 0.02 85);">{{ shareLabel }}</button>'
)

ANCHOR = '>缽日官網</a>'

# ── 2. 分享邏輯 ─────────────────────────────────────────────────
SHARE_LOGIC = """
  shareResult = async () => {
    const selectedIds = this.pickResultChannels(this.state.answers);
    const chosen = getChannels().filter(c => selectedIds.includes(c.id));
    const names = chosen.map(c => c.name).join('、');
    const phrases = chosen.map(c => c.phrase).join('、');
    // ?s=1 讓 Ron 可以在 GA 分辨哪些流量是從分享進來的
    const url = '%(url)s?s=1';
    const text = '我這次的內在天氣是：' + names + '\\n'
      + phrases + '——這幾天，我比較用這樣的方式在流動。\\n\\n你的呢？';

    // 手機：叫出系統分享選單，可以直接送進 LINE
    if (navigator.share) {
      try {
        await navigator.share({ title: '屬於你現在的內在天氣', text: text, url: url });
      } catch (e) {
        // 使用者自己按取消，什麼都不用做（不要再退回複製，那樣很煩）
      }
      return;
    }

    // 桌機：複製到剪貼簿
    try {
      await navigator.clipboard.writeText(text + '\\n' + url);
      this.setState({ shareLabel: '已複製，貼上就能分享 ✓' });
      setTimeout(() => this.setState({ shareLabel: SHARE_LABEL_DEFAULT }), 2600);
    } catch (e) {
      this.setState({ shareLabel: '請手動複製網址' });
    }
  };
""" % {"url": QUIZ_URL}


def main():
    src = open(PATH, encoding="utf-8").read()

    m = re.search(r'<script[^>]*type="__bundler/template"[^>]*>', src)
    if not m:
        sys.exit("找不到 __bundler/template，檔案結構可能變了")
    start, end = m.end(), src.find("</script>", m.end())
    raw = src[start:end]
    doc = json.loads(raw.strip())

    if "shareResult" in doc:
        sys.exit("偵測到已經加過分享按鈕了，不重複執行。")

    before = len(doc)

    # (a) 樣板：在「缽日官網」按鈕後面插入分享按鈕
    if doc.count(ANCHOR) != 1:
        sys.exit(f"「缽日官網」錨點出現 {doc.count(ANCHOR)} 次，預期 1 次")
    doc = doc.replace(ANCHOR, ANCHOR + SHARE_BUTTON, 1)

    # (b) 狀態：加上按鈕文字
    old_state = "  state = {\n    view: 'gallery',"
    if doc.count(old_state) != 1:
        sys.exit("找不到唯一的 state 宣告")
    doc = doc.replace(
        old_state,
        "  state = {\n    view: 'gallery',\n    shareLabel: SHARE_LABEL_DEFAULT,",
        1,
    )

    # (c) 常數：放在 class 前面
    old_class = "class Component extends DCLogic {"
    if doc.count(old_class) != 1:
        sys.exit("找不到唯一的 class 宣告")
    doc = doc.replace(
        old_class,
        "const SHARE_LABEL_DEFAULT = '分享我的內在天氣';\n\n" + old_class,
        1,
    )

    # (d) 邏輯：插在 pickResultChannels 前面
    old_pick = "  pickResultChannels(answers) {"
    if doc.count(old_pick) != 1:
        sys.exit("找不到唯一的 pickResultChannels")
    doc = doc.replace(old_pick, SHARE_LOGIC + "\n" + old_pick, 1)

    # (e) 重測 / 重新開始時，把按鈕文字復原
    for old in ("goQuiz = () => this.setState({ view: 'quiz',",
                "resetQuiz = () => this.setState({ view: 'quiz',"):
        if doc.count(old) != 1:
            sys.exit(f"找不到唯一的 {old[:12]}")
        doc = doc.replace(old, old + " shareLabel: SHARE_LABEL_DEFAULT,", 1)

    # (f) 把 handler 與文字暴露給樣板
    old_ret = "      resetQuiz: this.resetQuiz,"
    if doc.count(old_ret) != 1:
        sys.exit("找不到唯一的 resetQuiz 匯出")
    doc = doc.replace(
        old_ret,
        old_ret + "\n      shareResult: this.shareResult,"
                  "\n      shareLabel: this.state.shareLabel,",
        1,
    )

    # ── 重新編碼塞回去，外層一個字都不動 ──────────────────────
    new_raw = json.dumps(doc, ensure_ascii=False)
    # 只轉義 </script —— 那才是唯一會提早關閉外層 script 標籤的序列。
    # bundler 自己也只轉義這 3 處，其餘 </div> 之類都原樣保留；
    # 跟著它的慣例可以讓 diff 維持最小。
    new_raw = re.sub(r"</(?=script)", "<\\\\/", new_raw, flags=re.I)
    out = src[:start] + new_raw + src[end:]

    open(PATH, "w", encoding="utf-8").write(out)
    print(f"✓ 已修改 {PATH}")
    print(f"  內層文件 {before} → {len(doc)} 字元（+{len(doc) - before}）")
    print(f"  外層總長 {len(src)} → {len(out)} 字元")


if __name__ == "__main__":
    main()
