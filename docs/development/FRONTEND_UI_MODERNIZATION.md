### Frontend UI Modernization Guide

This guide outlines the repo-specific plan to modernize the frontend with a cohesive color palette, responsive layouts, accessible components, and optional dark mode.

---

### Objectives
- **Consistency**: Shared design tokens for colors, spacing, radii, and shadows.
- **Responsiveness**: Mobile-first layouts with progressive enhancements.
- **Accessibility**: Visible focus states, keyboard navigation, and contrast.
- **Maintainability**: Centralized components and patterns.

---

### Tech Stack Assumptions
- React 18, Vite, TypeScript
- Tailwind CSS 3.x (with forms/typography plugins)
- Headless UI and Heroicons/Lucide for primitives/icons

---

### Design Tokens and Palette
- **Primary (Indigo)**: 600 `#4F46E5`, 500 `#6366F1`, 100 `#E0E7FF`
- **Accent (Purple)**: 600 `#7C3AED`, 500 `#8B5CF6`, 100 `#EDE9FE`
- **Success (Emerald)**: 600 `#059669`, 100 `#D1FAE5`
- **Warning (Amber)**: 600 `#D97706`, 100 `#FEF3C7`
- **Danger (Rose)**: 600 `#E11D48`, 100 `#FFE4E6`
- **Neutral (Slate)**: 900 `#0F172A`, 700 `#334155`, 500 `#64748B`, 100 `#F1F5F9`
- **Surface**: `#FFFFFF` (light), `#0B1220` (dark surface-950)

Tailwind theme extension (proposal):

```js
// tailwind.config.js (excerpt)
export default {
  darkMode: 'class',
  content: ['./index.html','./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {50:'#EEF2FF',100:'#E0E7FF',200:'#C7D2FE',300:'#A5B4FC',400:'#818CF8',500:'#6366F1',600:'#4F46E5',700:'#4338CA',800:'#3730A3',900:'#312E81'},
        accent:  {50:'#F5F3FF',100:'#EDE9FE',200:'#DDD6FE',300:'#C4B5FD',400:'#A78BFA',500:'#8B5CF6',600:'#7C3AED',700:'#6D28D9',800:'#5B21B6',900:'#4C1D95'},
        success: {100:'#D1FAE5',600:'#059669'},
        warning: {100:'#FEF3C7',600:'#D97706'},
        danger:  {100:'#FFE4E6',600:'#E11D48'},
        neutral: {50:'#F8FAFC',100:'#F1F5F9',200:'#E2E8F0',300:'#CBD5E1',400:'#94A3B8',500:'#64748B',600:'#475569',700:'#334155',800:'#1E293B',900:'#0F172A'}
      },
      boxShadow: { card: '0 1px 2px 0 rgb(0 0 0 / 0.06), 0 1px 3px 1px rgb(0 0 0 / 0.04)' },
      borderRadius: { xl: '1rem' }
    }
  },
  plugins: [require('@tailwindcss/forms'), require('@tailwindcss/typography')],
}
```

Global styles (proposal):

```css
/* src/index.css (excerpt) */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
@tailwind base; @tailwind components; @tailwind utilities;

:root { --bg: #F8FAFC; --surface: #FFFFFF; }
.dark { --bg: #0B1220; --surface: #0F172A; }

html, body { @apply bg-[var(--bg)] text-neutral-900 dark:text-neutral-100 antialiased; font-family: Inter, system-ui, sans-serif; }
::selection { @apply bg-primary-200 text-neutral-900; }
```

---

### Core Component Standards
Implement and standardize the following in `src/components/common`:

- **Button**: `variant = primary | secondary | outline | ghost | danger`, `size = sm | md | lg`, `isLoading`, optional `leftIcon/rightIcon`.
- **Input/Select/Textarea**: unified focus rings `focus:ring-primary-500`, compact/error states, helper text.
- **Badge**: `default | success | warning | danger | info`.
- **Card**: container for boxed sections; default `rounded-lg shadow-card bg-white dark:bg-neutral-900`.
- **Modal/Drawer**: based on Headless UI `Dialog`, focus-trap, ESC/overlay close.
- **EmptyState**: icon, title, description, actions.
- **Skeleton**: shimmering placeholders.
- **PageHeader**: title, subtitle, breadcrumb/actions area.
- **Layout**: wraps pages with `Navigation`, container, and theme support.

Usage samples:

```tsx
// Button
<Button variant="primary" size="md">Save</Button>
<Button variant="outline" size="sm" isLoading>Loading</Button>

// Badge
<Badge variant="success">Owner</Badge>

// Card
<Card><Card.Header title="Quick Actions" /><Card.Body>...</Card.Body></Card>
```

---

### Navigation and Layout
- Sticky top navbar with subtle blur and shadow.
- Active item: `text-primary-700 bg-primary-50` (dark: `text-primary-300 bg-primary-950/40`).
- Mobile drawer nav using Headless UI `Dialog`.
- Add theme toggle to persist `.dark` via `localStorage`.

---

### Page Guidelines
- **Auth**: Two-column (form + brand). Glass effect cards: `bg-white/80 backdrop-blur`. Use `Alert` for errors.
- **Dashboard**: KPI cards, `Quick Actions` as lift-on-hover cards, recent bots with provider avatars, role `Badge`s.
- **Bots**: Filters as chips/pills on desktop, stack on mobile; row actions collapse to kebab on small screens.
- **Chat**: Two-pane on md+ (sessions sidebar + messages). Message bubbles, code block styling via typography plugin, sticky input bar.
- **Documents**: Drag-and-drop uploader, progress bars, file-type badges, grid/list toggle, filters.
- **Collaboration**: Roles table with color badges; invite modal; inline role editing with `Select`.
- **Profile**: Carded sections for account/security/notifications; standardized toggles/inputs.
- **API Keys**: Provider cards with masked values, copy/reveal, scopes.

---

### Responsiveness Patterns
- Tables → stacked cards on small screens.
- Filters collapse into dropdown/sheet on mobile.
- Sticky actions and headers where helpful.
- Chat sidebar hidden under `sm`, accessible via button.

---

### Motion and Accessibility
- Subtle transitions: `transition-all duration-150 ease-out`.
- Hover rings: `ring-1 ring-primary-200`.
- Respect reduced motion (`prefers-reduced-motion`).
- Keyboard focus: `focus-visible:ring-2 focus-visible:ring-primary-500`.
- Contrast: use 600 foregrounds on 50/100 backgrounds.

---

### Implementation Roadmap (PR Breakdown)
1. Base setup
   - Tailwind tokens, dark mode, plugins; global CSS and font.
   - Introduce `Layout.tsx` and `PageHeader.tsx`.
2. Core components
   - Create/standardize `Button`, `Input`, `Badge`, `Card`, `Modal`, `EmptyState`, `Skeleton`.
   - Migrate usages: replace ad-hoc classes with tokens/components.
3. Navigation
   - Sticky/blur nav, mobile drawer, theme toggle; integrate `NotificationSystem`.
4. Pages
   - Auth → new layout/cards.
   - Dashboard → KPI, quick actions, recent bots.
   - Bots → filters, list, actions.
   - Chat → shell, bubbles, input.
   - Documents → uploader/list UI.
   - Collaboration/Profile/API Keys → standardized settings.
5. Polish
   - a11y pass, dark mode QA, responsive audit.
6. Cleanup
   - Remove unused styles and unify icons.

---

### Migration Guide (Search/Replace)
Replace hardcoded color utilities with tokens:

- `bg-blue-600` → `bg-primary-600`
- `hover:bg-blue-700` → `hover:bg-primary-700`
- `text-blue-600` → `text-primary-600`
- `bg-green-100 text-green-800` → `bg-success-100 text-success-600`
- `bg-yellow-100 text-yellow-800` → `bg-warning-100 text-warning-600`
- `bg-red-600 hover:bg-red-700` → `bg-danger-600 hover:bg-danger-700`
- `text-gray-*` → `text-neutral-*` (match nearest value)
- Replace `bg-white shadow rounded-lg` wrappers with `Card`.
- Replace inline badges with `Badge` component.

Lint suggestion: prohibit direct `bg-blue-*`, `text-blue-*`, `bg-green-*`, `bg-red-*` in `src/**` except for the theme.

---

### Dark Mode
- Class-based `.dark` on `html` or `body`.
- Theme toggle persists to `localStorage` and syncs on load.
- Audit pages for contrast and state colors.

---

### Acceptance Criteria and QA Checklist
- Palette tokens used across components and pages; no stray hardcoded colors.
- Fully responsive layouts; no horizontal scroll on mobile.
- Accessible focus states; keyboard nav works; contrast AA.
- Dark mode toggle with persisted preference and correct surfaces/foregrounds.
- Existing tests remain green; visual smoke-test on key pages (Auth, Dashboard, Bots, Chat, Documents).

---

### Contribution Notes
- New UI should use shared components and tokens.
- Prefer Headless UI for complex interactions (Dialog, Listbox, Menu, Transition).
- Keep code readable (clear names, early returns, minimal nesting).



