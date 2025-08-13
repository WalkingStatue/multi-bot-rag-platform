# Accessibility Guide

This document provides comprehensive guidance for implementing and maintaining accessibility features in the Multi-Bot RAG Platform frontend.

## Overview

Our accessibility implementation follows WCAG 2.1 AA guidelines and includes:

- **Semantic HTML** - Proper use of HTML elements for their intended purpose
- **ARIA Support** - Comprehensive ARIA attributes for screen readers
- **Keyboard Navigation** - Full keyboard accessibility for all interactive elements
- **Focus Management** - Proper focus handling and visual indicators
- **Color Contrast** - WCAG compliant color combinations
- **Responsive Design** - Accessible across all device sizes
- **Screen Reader Support** - Optimized for assistive technologies

## Implementation

### 1. Accessibility Utilities (`src/utils/accessibility.ts`)

Core utilities for accessibility features:

```typescript
import {
  announceToScreenReader,
  trapFocus,
  createFocusManager,
  generateId,
  KEYBOARD_KEYS,
  handleArrowKeyNavigation
} from '../utils/accessibility';

// Announce to screen readers
announceToScreenReader('Form submitted successfully', 'assertive');

// Trap focus in modal
const cleanup = trapFocus(modalElement);

// Manage focus restoration
const focusManager = createFocusManager();
focusManager.save();
// ... later
focusManager.restore();
```

### 2. Accessibility Hooks (`src/hooks/useAccessibility.ts`)

React hooks for common accessibility patterns:

```typescript
import {
  useId,
  useAnnouncer,
  useFocusTrap,
  useModal,
  useDisclosure,
  useKeyboardNavigation
} from '../hooks/useAccessibility';

// Generate unique IDs
const labelId = useId('form-label');

// Screen reader announcements
const { announce } = useAnnouncer();
announce('Data loaded successfully');

// Modal accessibility
const { modalRef, titleId, modalProps } = useModal(isOpen);

// Disclosure pattern (show/hide content)
const { isOpen, toggle, triggerProps, contentProps } = useDisclosure();
```

### 3. CSS Utilities (`src/styles/accessibility.css`)

Comprehensive CSS for accessibility:

- Screen reader only text (`.sr-only`)
- Focus indicators (`.focus-visible`)
- High contrast mode support
- Reduced motion support
- Skip links
- Keyboard navigation styles

## Component Examples

### Accessible Modal

```typescript
import { AccessibleModal } from '../components/common/AccessibleModal';

<AccessibleModal
  isOpen={isModalOpen}
  onClose={() => setIsModalOpen(false)}
  title="Confirm Action"
  description="This action cannot be undone"
>
  <p>Are you sure you want to delete this item?</p>
  <div className="flex gap-2">
    <button onClick={handleCancel}>Cancel</button>
    <button onClick={handleConfirm}>Delete</button>
  </div>
</AccessibleModal>
```

### Accessible Form

```typescript
const ContactForm = () => {
  const nameId = useId('name');
  const emailId = useId('email');
  const { announce } = useAnnouncer();

  const handleSubmit = (data) => {
    // Submit form
    announce('Form submitted successfully', 'assertive');
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor={nameId} className="form-label required">
          Name
        </label>
        <input
          id={nameId}
          type="text"
          className="form-input"
          required
          aria-describedby={`${nameId}-help`}
        />
        <div id={`${nameId}-help`} className="form-help">
          Enter your full name
        </div>
      </div>

      <div className="form-group">
        <label htmlFor={emailId} className="form-label required">
          Email
        </label>
        <input
          id={emailId}
          type="email"
          className="form-input"
          required
          aria-invalid={hasEmailError}
          aria-describedby={hasEmailError ? `${emailId}-error` : undefined}
        />
        {hasEmailError && (
          <div id={`${emailId}-error`} className="form-error" role="alert">
            Please enter a valid email address
          </div>
        )}
      </div>

      <button type="submit" className="btn btn-primary">
        Submit Form
      </button>
    </form>
  );
};
```

### Accessible Navigation

```typescript
const Navigation = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const navItems = ['Home', 'About', 'Services', 'Contact'];

  const handleKeyDown = (event: KeyboardEvent) => {
    const newIndex = handleArrowKeyNavigation(
      event,
      navElements,
      currentIndex,
      { orientation: 'horizontal' }
    );
    setCurrentIndex(newIndex);
  };

  return (
    <nav role="navigation" aria-label="Main navigation">
      <ul className="nav" onKeyDown={handleKeyDown}>
        {navItems.map((item, index) => (
          <li key={item} className="nav-item">
            <a
              href={`/${item.toLowerCase()}`}
              className="nav-link"
              aria-current={index === currentIndex ? 'page' : undefined}
              tabIndex={index === currentIndex ? 0 : -1}
            >
              {item}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
};
```

## ARIA Patterns

### 1. Button

```typescript
// Toggle button
<button
  type="button"
  aria-pressed={isPressed}
  onClick={handleToggle}
>
  {isPressed ? 'On' : 'Off'}
</button>

// Menu button
<button
  type="button"
  aria-expanded={isMenuOpen}
  aria-controls="menu-list"
  aria-haspopup="true"
  onClick={toggleMenu}
>
  Menu
</button>
```

### 2. Combobox/Autocomplete

```typescript
const { inputProps, listboxProps, filteredOptions } = useCombobox(options);

<div className="combobox">
  <input
    {...inputProps}
    placeholder="Search options..."
    className="form-input"
  />
  <ul {...listboxProps} className="dropdown-menu">
    {filteredOptions.map((option, index) => (
      <li
        key={option}
        id={`${listboxProps.id}-option-${index}`}
        role="option"
        aria-selected={index === selectedIndex}
        className="dropdown-item"
      >
        {option}
      </li>
    ))}
  </ul>
</div>
```

### 3. Tabs

```typescript
const TabPanel = ({ children, isActive, id, labelledBy }) => (
  <div
    id={id}
    role="tabpanel"
    aria-labelledby={labelledBy}
    hidden={!isActive}
    tabIndex={isActive ? 0 : -1}
  >
    {children}
  </div>
);

const Tabs = ({ tabs }) => {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <div>
      <div role="tablist" aria-label="Settings">
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            id={`tab-${index}`}
            role="tab"
            aria-selected={index === activeTab}
            aria-controls={`panel-${index}`}
            tabIndex={index === activeTab ? 0 : -1}
            onClick={() => setActiveTab(index)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      
      {tabs.map((tab, index) => (
        <TabPanel
          key={tab.id}
          id={`panel-${index}`}
          labelledBy={`tab-${index}`}
          isActive={index === activeTab}
        >
          {tab.content}
        </TabPanel>
      ))}
    </div>
  );
};
```

## Keyboard Navigation

### Standard Key Bindings

- **Tab/Shift+Tab**: Navigate between focusable elements
- **Enter/Space**: Activate buttons and links
- **Arrow Keys**: Navigate within components (menus, tabs, etc.)
- **Escape**: Close modals, dropdowns, and other overlays
- **Home/End**: Jump to first/last item in lists
- **Page Up/Page Down**: Scroll content areas

### Implementation Example

```typescript
const handleKeyDown = (event: KeyboardEvent) => {
  switch (event.key) {
    case KEYBOARD_KEYS.ENTER:
    case KEYBOARD_KEYS.SPACE:
      event.preventDefault();
      handleActivate();
      break;
    case KEYBOARD_KEYS.ESCAPE:
      event.preventDefault();
      handleClose();
      break;
    case KEYBOARD_KEYS.ARROW_DOWN:
      event.preventDefault();
      focusNext();
      break;
    case KEYBOARD_KEYS.ARROW_UP:
      event.preventDefault();
      focusPrevious();
      break;
  }
};
```

## Screen Reader Support

### Live Regions

```typescript
// Polite announcements (don't interrupt)
announceToScreenReader('Form saved', 'polite');

// Assertive announcements (interrupt current speech)
announceToScreenReader('Error occurred', 'assertive');

// Status updates
<div aria-live="polite" aria-atomic="true">
  {statusMessage}
</div>
```

### Descriptive Text

```typescript
// Screen reader only descriptions
<span className="sr-only">
  Opens in new window
</span>

// ARIA descriptions
<button aria-describedby="help-text">
  Submit
</button>
<div id="help-text" className="sr-only">
  This will submit your form data
</div>
```

## Color and Contrast

### WCAG Compliance

```typescript
import { meetsContrastRequirement } from '../utils/accessibility';

// Check color contrast
const isAccessible = meetsContrastRequirement(
  '#ffffff', // background
  '#0066cc', // foreground
  'AA',      // WCAG level
  'normal'   // text size
);
```

### CSS Variables for Theming

```css
:root {
  --color-primary: #0066cc;
  --color-primary-contrast: #ffffff;
  --color-error: #d32f2f;
  --color-error-contrast: #ffffff;
  --color-success: #28a745;
  --color-success-contrast: #ffffff;
}

/* High contrast mode */
@media (prefers-contrast: high) {
  :root {
    --color-primary: #0052a3;
    --color-border: #000000;
  }
}
```

## Testing Accessibility

### Automated Testing

```typescript
// Example accessibility test
import { renderWithProviders } from '../test/utils';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

test('should not have accessibility violations', async () => {
  const { container } = renderWithProviders(<MyComponent />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### Manual Testing Checklist

#### Keyboard Navigation
- [ ] All interactive elements are focusable
- [ ] Focus order is logical
- [ ] Focus indicators are visible
- [ ] No keyboard traps (except modals)
- [ ] Skip links work properly

#### Screen Reader Testing
- [ ] All content is announced properly
- [ ] Form labels are associated correctly
- [ ] Error messages are announced
- [ ] Status changes are announced
- [ ] Navigation landmarks are present

#### Visual Testing
- [ ] Text meets contrast requirements
- [ ] Focus indicators are visible
- [ ] Content is readable at 200% zoom
- [ ] No information conveyed by color alone
- [ ] Animations respect reduced motion preference

### Testing Tools

1. **Browser Extensions**
   - axe DevTools
   - WAVE Web Accessibility Evaluator
   - Lighthouse Accessibility Audit

2. **Screen Readers**
   - NVDA (Windows)
   - JAWS (Windows)
   - VoiceOver (macOS)
   - Orca (Linux)

3. **Keyboard Testing**
   - Test with Tab key only
   - Test with arrow keys
   - Test with screen reader shortcuts

## Best Practices

### 1. Semantic HTML First

```typescript
// ❌ Don't use divs for interactive elements
<div onClick={handleClick}>Click me</div>

// ✅ Use proper semantic elements
<button onClick={handleClick}>Click me</button>
```

### 2. Proper Labeling

```typescript
// ❌ Missing or inadequate labels
<input type="text" placeholder="Name" />

// ✅ Proper labeling
<label htmlFor="name">Full Name</label>
<input id="name" type="text" required />
```

### 3. Error Handling

```typescript
// ❌ Visual-only error indication
<input className="error" />

// ✅ Accessible error handling
<input
  aria-invalid={hasError}
  aria-describedby={hasError ? "error-msg" : undefined}
/>
{hasError && (
  <div id="error-msg" role="alert">
    Please enter a valid value
  </div>
)}
```

### 4. Loading States

```typescript
// ❌ Visual-only loading indicator
<div className="spinner" />

// ✅ Accessible loading state
<div>
  <span className="sr-only">Loading...</span>
  <div className="spinner" aria-hidden="true" />
</div>
```

## Performance Considerations

### Reduced Motion

```typescript
const { prefersReducedMotion } = useAccessibilityPreferences();

// Conditionally apply animations
const animationClass = prefersReducedMotion ? '' : 'animate-slide-in';
```

### Focus Management

```typescript
// Efficient focus trapping
useEffect(() => {
  if (isModalOpen) {
    const cleanup = trapFocus(modalRef.current);
    return cleanup;
  }
}, [isModalOpen]);
```

## Maintenance

### Regular Audits

1. Run automated accessibility tests in CI/CD
2. Perform manual testing with screen readers
3. Test keyboard navigation regularly
4. Validate color contrast ratios
5. Check for ARIA attribute correctness

### Documentation Updates

- Keep accessibility patterns documented
- Update examples when patterns change
- Maintain testing procedures
- Document known issues and workarounds

## Resources

### WCAG Guidelines
- [WCAG 2.1 AA Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)

### Testing Tools
- [axe-core](https://github.com/dequelabs/axe-core)
- [WAVE](https://wave.webaim.org/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)

### Screen Readers
- [NVDA](https://www.nvaccess.org/)
- [JAWS](https://www.freedomscientific.com/products/software/jaws/)
- [VoiceOver Guide](https://www.apple.com/accessibility/mac/vision/)

This comprehensive accessibility implementation ensures our application is usable by everyone, regardless of their abilities or the assistive technologies they use.