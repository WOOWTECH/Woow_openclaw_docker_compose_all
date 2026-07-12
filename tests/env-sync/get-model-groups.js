// Playwright run-code script: extract model groups from the picker
// Returns JSON array of group names like ["MiniMax (4)", "OpenAI API (10)"]

async (page) => {
  // Find and click the model picker button (contains current model name)
  const modelBtn = page.locator('button').filter({ hasText: /Minimax|MiniMax|OpenAI|gpt|Select a model/i }).first();
  await modelBtn.click();
  await page.waitForTimeout(1500);

  // Extract all model group headers from the dropdown
  const snapshot = await page.accessibility.snapshot();

  // Alternative: use DOM query to find group labels
  const groups = await page.evaluate(() => {
    // Model groups appear as clickable items with "▶ GroupName (count)" pattern
    const elements = document.querySelectorAll('[class*="model"], [class*="selector"], [role="listbox"], [role="option"]');
    const texts = [];
    document.querySelectorAll('*').forEach(el => {
      const text = el.textContent?.trim();
      if (text && /^▶\s+\w+.*\(\d+\)$/.test(text) && !texts.includes(text)) {
        texts.push(text);
      }
    });
    return texts;
  });

  // Close the dropdown
  await page.keyboard.press('Escape');

  return JSON.stringify(groups);
};
