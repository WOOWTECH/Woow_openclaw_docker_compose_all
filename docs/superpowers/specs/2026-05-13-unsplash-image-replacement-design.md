# Mark Studio — Unsplash 圖片替換設計規格

## 目標
將馬克健身網站全站 10 張圖片替換為 Unsplash 高品質運動按摩/伸展主題圖片。

## 設計決策

| 項目 | 決定 |
|------|------|
| 風格 | 專業運動風 — 運動員伸展、治療師按壓肌肉 |
| 構圖 | 不露臉 — 聚焦手部按壓、肌肉線條、身體局部特寫 |
| 色調 | CSS `filter: grayscale(1)` 統一黑白處理 |
| 託管 | 下載到 `static/src/img/`，自託管（方案 B） |
| 標註 | Footer 加 Unsplash credit |

## 圖片替換清單

### 1. Hero 背景 — `hero-bg.jpg`
- **搜尋**：sports massage, muscle therapy, back massage
- **構圖**：寬幅橫構圖，手按壓背部/肩膀特寫，暗色調
- **尺寸**：1920x1080 以上（全屏背景）
- **CSS**：`filter: grayscale(1) brightness(0.5)`

### 2. 服務 01 — `svc-01-massage.jpg`
- **搜尋**：deep tissue massage hands
- **構圖**：治療師雙手按壓肌肉特寫
- **尺寸**：800x600
- **同時用於**：預約卡片（Booking CTA section）

### 3. 服務 02 — `svc-02-stretch.jpg`
- **搜尋**：assisted stretching, passive stretch
- **構圖**：被動伸展動作，聚焦腿部/手臂
- **尺寸**：800x600

### 4. 服務 03 — `svc-03-personal.jpg`
- **搜尋**：personal training stretch, one on one therapy
- **構圖**：一對一場景，不露臉，聚焦動作
- **尺寸**：800x600

### 5. 技術左 — `tech-left.jpg`
- **搜尋**：massage technique close up, thumb pressure
- **構圖**：指關節/掌壓手法特寫
- **尺寸**：600x400

### 6. 技術右 — `tech-right.jpg`
- **搜尋**：core stretching, hip flexor stretch
- **構圖**：軀幹/髖部伸展動作
- **尺寸**：600x400

### 7. 體驗 01 — `exp-01-consult.jpg`
- **搜尋**：physical assessment, body palpation
- **構圖**：觸診/身體檢查局部
- **尺寸**：400x300

### 8. 體驗 02 — `exp-02-measure.jpg`
- **搜尋**：flexibility test, range of motion
- **構圖**：柔軟度測量，角度/拉伸動作
- **尺寸**：400x300

### 9. 體驗 03 — `exp-03-stretch.jpg`
- **搜尋**：stretching therapy session
- **構圖**：伸展進行中，手部輔助動作
- **尺寸**：400x300

### 10. 體驗 04 — `exp-04-advice.jpg`
- **搜尋**：therapist notes, clipboard consultation
- **構圖**：紀錄板/筆記特寫（暗示專業建議）
- **尺寸**：400x300

## CSS 變更

在 `markstudio.css` 中新增全站灰階濾鏡：

```css
/* 全站圖片灰階處理 — Retrodandy 單色美學 */
.mk-hero-bg {
    filter: grayscale(1) brightness(0.5);
}

.mk-svc-img img,
.mk-step-img img,
.mk-booking-card-img img {
    filter: grayscale(1) brightness(0.85);
}
```

## Unsplash 標註

在 Footer 加上：
```
Photos by Unsplash
```

## 檔案異動

| 檔案 | 變更 |
|------|------|
| `static/src/img/*.jpg` | 替換 10 張圖片 |
| `static/src/css/markstudio.css` | 新增 grayscale 濾鏡（~10 行） |
| `views/homepage_templates.xml` | 不需改（檔名不變） |

## 圖片下載流程

1. 用 Unsplash API 搜尋每張圖的關鍵字
2. 從搜尋結果中挑選符合構圖需求的圖片
3. 使用 `urls.regular`（1080w）下載
4. 儲存為對應檔名到 `static/src/img/`
5. 觸發 Unsplash download endpoint（API 要求）

## 限制

- Unsplash 開發模式限 50 次/小時
- 10 張圖搜尋約需 10-20 次 API 呼叫（含篩選）
- 需在限額內完成
