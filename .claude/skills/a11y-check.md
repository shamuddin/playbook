---
name: a11y-check
description: Run WCAG 2.1 AA accessibility audits on the React frontend
---

Run an automated and manual accessibility audit across all PLAYBOOK frontend pages. Validate keyboard navigation, semantic markup, and color independence.

1. **Automated scan**: If `axe-core` CLI or `@axe-core/cli` is available, run it against the running frontend (`http://localhost:5173`). Otherwise, use Lighthouse accessibility audit (`npx lighthouse --only-categories=accessibility`).
2. **Keyboard navigation**: Tab through each page (Login, Dashboard, Incidents, Judge, Compliance, PolicyBuilder, Playground). Verify every interactive element is reachable and focus is visible.
3. **Semantic HTML**: Check that `frontend/src/components/Layout.tsx` and pages use `<main>`, `<nav>`, `<header>`, and heading hierarchy (`h1` → `h2` → `h3`) without skips.
4. **ARIA audit**: Verify dynamic lists (incidents, timeline, judge decisions) have `role="list"` / `role="listitem"` or equivalent. Recharts charts must have `role="img"` and `aria-label`.
5. **Color contrast**: Use a contrast checker on Tailwind color pairs (especially severity badges: red, amber, green). Verify 4.5:1 for normal text and 3:1 for large text/UI borders.
6. **Report**: Summarize violations by WCAG principle (Perceivable, Operable, Understandable, Robust). Provide exact component paths and remediation code snippets.
