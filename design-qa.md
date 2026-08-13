# Design QA

- source visual truth path: `C:\Users\WZB\.codex\generated_images\019ffa18-cbc2-7480-872e-2d1013c63f76\exec-ee491944-bac5-44a3-9227-22ba78f456e5.png`
- implementation screenshots: `.codex-qa/desktop.png`, `.codex-qa/mobile.png`
- combined comparison: `.codex-qa/comparison.png`
- viewport: desktop `1280 x 720`; mobile `390 x 844`
- pixels and density: source `1536 x 1024`; desktop implementation `1280 x 720`; mobile implementation `390 x 844`; browser density `1x`
- state: Chinese default and English alternate profile READMEs, light GitHub reading surface, external badges loaded

## Findings

- No actionable P0, P1, or P2 visual findings remain.
- Typography keeps the source's compact console hierarchy while using GitHub-safe text for body copy. The final WZB wordmark uses an actual deepslate texture mask instead of a flat approximation.
- Layout preserves the source's obsidian/blackstone frame, redstone circuit, emerald core, and dark system-console hierarchy while translating the dense dashboard into a readable GitHub README.
- Colors stay within the source palette: near-black panels, white text, emerald status accents, and redstone action accents.
- Images use lossless PNG output and nearest-neighbor scaling for the Minecraft textures. Desktop and mobile use dedicated aspect ratios rather than stretched crops.
- Chinese and English copy are separate complete documents with equivalent information architecture.
- At `390px`, the browser selected `banner-cn-mobile.png` and `mcacs-cn-mobile.png`; measured document `scrollWidth` equals the `390px` viewport, so no horizontal overflow remains.
- The English document independently selected `banner-en-mobile.png` and `mcacs-en-mobile.png` at `390px`; it also had no horizontal overflow or broken images.
- All rendered images except the removed third-party statistics card had non-zero natural dimensions. The contribution snake and project badges loaded, and the browser console contained no errors or warnings.

## Comparison history

1. The initial full-view comparison found a P2 fidelity issue: the WZB wordmark was flat white, while the source used a stone-textured block treatment. Fixed by masking the actual deepslate texture through the wordmark and recaptured both responsive views.
2. Runtime inspection found a P2 reliability issue: the third-party GitHub statistics image returned `0 x 0`. Removed the unreliable card and retained the working contribution snake.
3. Post-fix comparison confirmed the source's texture, palette, hierarchy, and circuit motif are present without introducing mobile overflow or clipped content.

## Focused-region evidence

The hero and flagship images were inspected at their native `1280px` width, plus the mobile hero at `760 x 460`. Text, borders, block textures, and redstone/emerald alignment remained sharp and unclipped. No additional focused crop was needed because the native assets were large enough to judge directly.

## Primary interactions tested

- Chinese/English navigation targets exist and resolve to the corresponding README files.
- Responsive `<picture>` sources switch at the `600px` breakpoint.
- Chinese and English responsive routes were both rendered at desktop and mobile widths.
- Repository, documentation, CI, release, container, license, and selected-project links were checked independently.

final result: passed
