#!/usr/bin/env python3
"""
在結果頁加上「存成圖片」——產生 1080x1920 的 IG 限動尺寸結果圖。

先講清楚做得到與做不到的：
  網頁**無法**直接發佈到 IG 限動，Instagram 沒有開放這個能力給網站。
  圖片裡的文字也**不能點**，限動的可點連結必須由使用者自己加連結貼紙
  或 @提及貼紙。所以圖上的 @mrpin_xuan_siningbowl 是給人看的，
  不是超連結。

  在這個前提下能做到最好的是：
  - 手機：navigator.share 帶著圖片檔叫出系統分享選單，
          選 Instagram 就會直接進入限動編輯畫面（省掉截圖裁切）
  - 桌機：直接下載 PNG

配色直接取自測驗頁自己的 oklch 變數（已轉成 hex），確保同一個世界。

冪等：偵測到已加過就中止。

用法：
  python3 tools/add-story-image.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "index.html")

IG_HANDLE = "@mrpin_xuan_siningbowl"
QUIZ_URL = "https://ronwang82-singingbowl.github.io/bori-quiz/"

# 結果頁的按鈕（放在分享鈕下面）
STORY_BUTTON = (
    '\n          <button sc-camel-on-click="{{ saveImage }}" '
    'style="border:none; background:none; color:oklch(55% 0.04 55); '
    'font-size:13px; margin-top:2px; cursor:pointer; text-decoration:underline;">'
    '{{ saveLabel }}</button>'
)

ANCHOR = '{{ shareLabel }}</button>'

STORY_LOGIC = r"""
  // ── 產生 IG 限動尺寸（1080x1920）的結果圖 ──────────────────────
  // 配色取自本頁的 oklch 變數，轉成 hex 以便在 canvas 使用。
  buildStoryCanvas = async () => {
    const C = { bg:'#f9f5eb', deep:'#1f3a25', body:'#314a32',
                brown:'#704b36', gold:'#d1a84b', mute:'#856c5c',
                line:'#8fae94', card:'#eee7d9' };
    const W = 1080, H = 1920;
    const cv = document.createElement('canvas');
    cv.width = W; cv.height = H;
    const g = cv.getContext('2d');
    const SERIF = '"Noto Serif TC","Songti TC","PingFang TC",serif';

    g.fillStyle = C.bg; g.fillRect(0, 0, W, H);

    // 呼應官網 hero 的同心圓
    g.strokeStyle = C.card; g.lineWidth = 3;
    [430, 560].forEach(r => { g.beginPath(); g.arc(W/2, 980, r, 0, Math.PI*2); g.stroke(); });

    const centre = (t, y, font, color) => {
      g.font = font; g.fillStyle = color; g.textAlign = 'center';
      g.fillText(t, W/2, y);
    };

    const loadImg = src => new Promise(ok => {
      const im = new Image(); im.crossOrigin = 'anonymous';
      im.onload = () => ok(im); im.onerror = () => ok(null); im.src = src;
    });

    // 標頭
    const logo = await loadImg((window.__resources && window.__resources.logo) || '');
    if (logo) {
      g.save(); g.beginPath(); g.arc(W/2, 190, 62, 0, Math.PI*2); g.clip();
      g.drawImage(logo, W/2-62, 128, 124, 124); g.restore();
    }
    centre('缽日 BORI', 310, `600 40px ${SERIF}`, C.deep);
    centre('我 的 內 在 天 氣', 372, '300 26px sans-serif', C.brown);

    // 結果的三個角色
    const ids = this.pickResultChannels(this.state.answers);
    const chosen = getChannels().filter(c => ids.includes(c.id));
    const imgs = await Promise.all(chosen.map(c => loadImg(c.img)));

    const slot = W / chosen.length;
    const TOP = 520, box = 210;
    for (let i = 0; i < chosen.length; i++) {
      const cx = slot * (i + 0.5);
      const x0 = cx - box/2;
      // 插圖本身帶著淺灰底，所以裁成圓角方塊後用 cover 填滿——
      // 讓那層灰底直接變成卡片背景，不會露出一塊灰色方塊。
      g.save();
      g.beginPath();
      if (g.roundRect) g.roundRect(x0, TOP, box, box, 36);
      else g.rect(x0, TOP, box, box);
      g.clip();
      g.fillStyle = '#fff'; g.fillRect(x0, TOP, box, box);
      const im = imgs[i];
      if (im) {
        const s = Math.max(box/im.naturalWidth, box/im.naturalHeight);   // cover
        const w = im.naturalWidth*s, h = im.naturalHeight*s;
        g.drawImage(im, cx-w/2, TOP+box/2-h/2, w, h);
      }
      g.restore();
      g.font = `600 40px ${SERIF}`; g.fillStyle = C.deep; g.textAlign = 'center';
      g.fillText(chosen[i].name, cx, TOP + box + 62);
      g.font = '300 25px sans-serif'; g.fillStyle = C.mute;
      g.fillText(chosen[i].phrase, cx, TOP + box + 106);
    }

    // 自動換行
    const wrap = (text, maxW, font, color, startY, lh) => {
      g.font = font; g.fillStyle = color; g.textAlign = 'center';
      const lines = []; let cur = '';
      for (const ch of text) {
        if (g.measureText(cur + ch).width > maxW && cur) { lines.push(cur); cur = ch; }
        else cur += ch;
      }
      if (cur) lines.push(cur);
      lines.forEach((l, i) => g.fillText(l, W/2, startY + i*lh));
      return startY + lines.length*lh;
    };

    let y = wrap('這次比較有回應的線索是', 860, `600 46px ${SERIF}`, C.deep, 1010, 66);
    y = wrap(chosen.map(c => c.name).join('、'), 860, `600 62px ${SERIF}`, C.gold, y + 30, 82);
    y = wrap(chosen.map(c => c.phrase).join('、') + '——這幾天，我比較用這樣的方式在流動。',
             820, '300 30px sans-serif', C.body, y + 62, 54);
    wrap('這不是我的答案，是這次的天氣。三個月後，可能又換了一種樣子。',
         800, '300 26px sans-serif', C.mute, y + 60, 44);

    // 頁尾：IG 帳號 + 測驗網址。
    // 位置緊貼底部（限動上下兩端本來就會被 IG 的 UI 蓋住一點），
    // 這樣中段的留白才不會空得太突兀。
    g.strokeStyle = C.line; g.lineWidth = 2;
    g.beginPath(); g.moveTo(W/2-90, 1672); g.lineTo(W/2+90, 1672); g.stroke();
    centre('__IG_HANDLE__', 1748, '600 36px sans-serif', C.deep);
    centre('測測你的 → __QUIZ_URL__', 1802, '300 24px sans-serif', C.mute);

    return cv;
  };

  // 把圖顯示出來讓使用者自己存。
  // 為什麼不用 <a download>：LINE 與 IG 的內建瀏覽器會直接擋掉，
  // 跳出「不支援檔案下載功能，請透過其他瀏覽器再試一次」——
  // 而從 LINE 點進來的人正是這個測驗最大宗的流量來源。
  // 長按（或右鍵）存圖是唯一在所有環境都成立的做法。
  showImageOverlay = (url) => {
    const old = document.getElementById('bori-save-overlay');
    if (old) old.remove();
    const touch = window.matchMedia && window.matchMedia('(pointer:coarse)').matches;
    const box = document.createElement('div');
    box.id = 'bori-save-overlay';
    box.style.cssText = 'position:fixed; inset:0; z-index:99999; background:rgba(18,26,20,.94);'
      + 'display:flex; flex-direction:column; align-items:center; justify-content:center;'
      + 'gap:18px; padding:22px; overflow:auto;';

    const tip = document.createElement('div');
    tip.textContent = touch ? '長按圖片 → 儲存到相簿，就能貼到限動了'
                            : '在圖片上按右鍵 → 另存圖片';
    tip.style.cssText = 'color:#f9f5eb; font-size:15px; line-height:1.7; text-align:center;';

    const im = document.createElement('img');
    im.src = url;
    im.alt = '我的內在天氣';
    im.style.cssText = 'max-width:100%; max-height:66vh; border-radius:14px;'
      + 'box-shadow:0 10px 44px rgba(0,0,0,.45);';

    const close = document.createElement('button');
    close.textContent = '關閉';
    close.style.cssText = 'border:1px solid #8fae94; background:none; color:#f9f5eb;'
      + 'padding:11px 34px; border-radius:999px; font-size:14px; cursor:pointer;';
    close.onclick = () => { box.remove(); URL.revokeObjectURL(url); };

    box.append(tip, im, close);
    document.body.appendChild(box);
  };

  saveImage = async () => {
    this.setState({ saveLabel: '正在產生圖片…' });
    try {
      const cv = await this.buildStoryCanvas();
      const blob = await new Promise(r => cv.toBlob(r, 'image/png'));
      const file = new File([blob], '我的內在天氣.png', { type: 'image/png' });

      // 真正的 Safari / Chrome：叫出系統分享選單，選 Instagram 直接進限動編輯
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        try {
          await navigator.share({ files: [file], title: '我的內在天氣' });
        } catch (e) { /* 使用者取消，不用處理 */ }
        this.setState({ saveLabel: SAVE_LABEL_DEFAULT });
        return;
      }

      // 其餘一律顯示圖片讓使用者自己存（含 LINE / IG 內建瀏覽器）
      this.showImageOverlay(URL.createObjectURL(blob));
      this.setState({ saveLabel: SAVE_LABEL_DEFAULT });
    } catch (e) {
      this.setState({ saveLabel: '產生失敗，請重試' });
      setTimeout(() => this.setState({ saveLabel: SAVE_LABEL_DEFAULT }), 2600);
    }
  };
"""
# 不用 % 格式化：這段 JS 裡有 max-width:100% 之類的字面百分號，
# 用 % 會被當成格式指示字而炸掉。改用明確的字串替換。
STORY_LOGIC = (STORY_LOGIC
               .replace("__IG_HANDLE__", IG_HANDLE)
               .replace("__QUIZ_URL__", QUIZ_URL.replace("https://", "")))


def main():
    src = open(PATH, encoding="utf-8").read()
    m = re.search(r'<script[^>]*type="__bundler/template"[^>]*>', src)
    if not m:
        sys.exit("找不到 __bundler/template")
    start, end = m.end(), src.find("</script>", m.end())
    doc = json.loads(src[start:end].strip())

    if "saveImage" in doc:
        sys.exit("偵測到已經加過存圖功能了，不重複執行。")
    if "shareResult" not in doc:
        sys.exit("請先執行 add-share-button.py")

    before = len(doc)

    def once(old, new, what):
        if doc.count(old) != 1:
            sys.exit(f"{what} 錨點出現 {doc.count(old)} 次，預期 1 次")
        return doc.replace(old, new, 1)

    doc = once(ANCHOR, ANCHOR + STORY_BUTTON, "存圖按鈕")
    doc = once("const SHARE_LABEL_DEFAULT = '分享我的內在天氣';",
               "const SHARE_LABEL_DEFAULT = '分享我的內在天氣';\n"
               "const SAVE_LABEL_DEFAULT = '存成圖片，貼到 IG 限動';",
               "常數")
    doc = once("    shareLabel: SHARE_LABEL_DEFAULT,",
               "    shareLabel: SHARE_LABEL_DEFAULT,\n    saveLabel: SAVE_LABEL_DEFAULT,",
               "state")
    doc = once("  shareResult = async () => {",
               STORY_LOGIC + "\n  shareResult = async () => {",
               "邏輯")
    doc = once("      shareLabel: this.state.shareLabel,",
               "      shareLabel: this.state.shareLabel,\n"
               "      saveImage: this.saveImage,\n"
               "      saveLabel: this.state.saveLabel,",
               "匯出")
    for old in ("goQuiz = () => this.setState({ view: 'quiz', shareLabel: SHARE_LABEL_DEFAULT,",
                "resetQuiz = () => this.setState({ view: 'quiz', shareLabel: SHARE_LABEL_DEFAULT,"):
        doc = once(old, old + " saveLabel: SAVE_LABEL_DEFAULT,", "重置")

    new_raw = re.sub(r"</(?=script)", "<\\\\/",
                     json.dumps(doc, ensure_ascii=False), flags=re.I)
    open(PATH, "w", encoding="utf-8").write(src[:start] + new_raw + src[end:])
    print(f"✓ 已修改 {PATH}")
    print(f"  內層文件 {before} → {len(doc)} 字元（+{len(doc)-before}）")


if __name__ == "__main__":
    main()
