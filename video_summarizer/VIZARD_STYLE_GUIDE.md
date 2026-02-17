# Vizard.ai Style Subtitles & Fixes

## ✅ New "Vizard" Subtitle Style

### **What is it?**
High-engagement "Karaoke" style subtitles, similar to Vizard.ai or TikTok/Reels captions.

### **How it looks:**
Instead of a crowded block of text, you see **3 words** at a time:
1.  **Previous Word** (White)
2.  **Current Spoken Word** (💛 **Yellow Highlight**)
3.  **Next Word** (White)

### **Example:**
When the speaker says "video":

```
awesome <video> content
(White)  (Yellow)  (White)
```

The highlight moves as they speak! 

---

## ✅ Clip Editor Fix (No more re-asking URL)

### **Issue:**
"Edit Clip Timing" kept asking for the "Original video path", which was annoying.

### **Fix:**
- We now **auto-save user metadata** (`metadata.json`) with every short.
- This file remembers where the original video is.
- When you click "Regenerate", it **automatically finds the file**.
- No more typing paths! 🚀

---

## 📋 How to Use

### **For New Shorts:**
1.  Just generate previews as normal.
2.  The metadata is saved automatically.
3.  Vizard-style is now the default!

### **For Existing Shorts:**
1.  **To fix subtitles:** Go to "Add Subtitles to Selected" -> It will regenerate with Vizard style.
2.  **To fix Clip Editor:** You might need to enter the path *one last time* for old shorts, but new ones will work automatically.

---

## 🔧 Technical Details

**Subtitle Logic:**
- **Flattened Word List:** We process every single word timestamp.
- **Dynamic Context:** For word `i`, we grab `i-1`, `i`, and `i+1`.
- **HTML Highlighting:** We use `<font color="#FFEE00"><b>word</b></font>` for the active word.
- **Precision Timing:** Subtitle duration matches the spoken word exactly (min 0.1s).

**Result:** Fast-paced, engaging, professional look! 

---

**Version: 2.5 (Vizard Style + Metadata Fix)**
