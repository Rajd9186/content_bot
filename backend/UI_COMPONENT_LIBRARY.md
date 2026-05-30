# Professional UI Component Library & Design Patterns

## Part 1: Design Token System

### Color System
```css
/* Sophisticated, Professional Palette */
:root {
  /* Primary Brand Colors */
  --color-primary-dark: #0f172a;    /* Deep navy */
  --color-primary: #1e40af;          /* Professional blue */
  --color-primary-light: #dbeafe;    /* Light blue */
  
  /* Secondary/Accent */
  --color-accent: #dc2626;           /* Energetic red */
  --color-accent-light: #fee2e2;     /* Light red */
  
  /* Neutral Scale (8 levels for sophistication) */
  --color-neutral-50: #fafafa;
  --color-neutral-100: #f4f4f5;
  --color-neutral-200: #e4e4e7;
  --color-neutral-300: #d4d4d8;
  --color-neutral-400: #a1a1a6;
  --color-neutral-500: #71717a;
  --color-neutral-600: #52525b;
  --color-neutral-700: #3f3f46;
  --color-neutral-800: #27272a;
  --color-neutral-900: #18181b;
  
  /* Semantic Colors */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;
  
  /* Backgrounds */
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f9fafb;
  --color-bg-tertiary: #f3f4f6;
  
  /* Text */
  --color-text-primary: #111827;
  --color-text-secondary: #6b7280;
  --color-text-tertiary: #9ca3af;
  
  /* Borders */
  --color-border: #e5e7eb;
  --color-border-light: #f0f0f0;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  --shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg-primary: #1a1a1a;
    --color-bg-secondary: #2d2d2d;
    --color-bg-tertiary: #3d3d3d;
    --color-text-primary: #ffffff;
    --color-text-secondary: #d0d0d0;
    --color-border: #404040;
  }
}
```

### Typography System
```css
:root {
  /* Font Families */
  --font-display: 'Crimson Text', serif;        /* Elegant headings */
  --font-body: 'Inter', -apple-system, sans-serif; /* Clean body text */
  --font-mono: 'Fira Code', monospace;           /* Code/data */
  
  /* Font Sizing (Modular scale 1.125) */
  --fs-xs: 0.75rem;     /* 12px */
  --fs-sm: 0.875rem;    /* 14px */
  --fs-base: 1rem;      /* 16px */
  --fs-lg: 1.125rem;    /* 18px */
  --fs-xl: 1.25rem;     /* 20px */
  --fs-2xl: 1.5rem;     /* 24px */
  --fs-3xl: 1.875rem;   /* 30px */
  --fs-4xl: 2.25rem;    /* 36px */
  --fs-5xl: 3rem;       /* 48px */
  
  /* Font Weights */
  --fw-light: 300;
  --fw-normal: 400;
  --fw-medium: 500;
  --fw-semibold: 600;
  --fw-bold: 700;
  
  /* Line Heights */
  --lh-tight: 1.25;
  --lh-normal: 1.5;
  --lh-relaxed: 1.75;
}

/* Responsive Typography with clamp() */
h1 {
  font-family: var(--font-display);
  font-size: clamp(2rem, 8vw, 3.5rem);
  font-weight: var(--fw-light);
  line-height: var(--lh-tight);
  letter-spacing: -0.02em;
}

h2 {
  font-family: var(--font-display);
  font-size: clamp(1.5rem, 5vw, 2.5rem);
  font-weight: var(--fw-normal);
  line-height: var(--lh-tight);
}

p {
  font-family: var(--font-body);
  font-size: var(--fs-base);
  line-height: var(--lh-relaxed);
}
```

### Spacing System
```css
:root {
  /* Spacing Scale (8px base) */
  --space-0: 0;
  --space-1: 0.25rem;    /* 4px */
  --space-2: 0.5rem;     /* 8px */
  --space-3: 0.75rem;    /* 12px */
  --space-4: 1rem;       /* 16px */
  --space-6: 1.5rem;     /* 24px */
  --space-8: 2rem;       /* 32px */
  --space-12: 3rem;      /* 48px */
  --space-16: 4rem;      /* 64px */
  --space-24: 6rem;      /* 96px */
}
```

---

## Part 2: Component Library

### Button Component (React Example)
```jsx
// Button.jsx
import PropTypes from 'prop-types';
import './Button.css';

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  fullWidth = false,
  onClick,
  ...props
}) {
  return (
    <button
      className={`btn btn--${variant} btn--${size} ${fullWidth ? 'btn--full' : ''}`}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
}

Button.propTypes = {
  children: PropTypes.node.isRequired,
  variant: PropTypes.oneOf(['primary', 'secondary', 'outline', 'ghost', 'danger']),
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  disabled: PropTypes.bool,
  fullWidth: PropTypes.bool,
  onClick: PropTypes.func,
};

// Button.css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-body);
  font-weight: var(--fw-semibold);
  border-radius: 0.5rem;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  user-select: none;
}

/* Primary Button */
.btn--primary {
  background-color: var(--color-primary);
  color: white;
  box-shadow: var(--shadow-md);
}

.btn--primary:hover:not(:disabled) {
  background-color: #1d3a8a;
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.btn--primary:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: var(--shadow-md);
}

/* Secondary Button */
.btn--secondary {
  background-color: var(--color-neutral-200);
  color: var(--color-text-primary);
}

.btn--secondary:hover:not(:disabled) {
  background-color: var(--color-neutral-300);
}

/* Outline Button */
.btn--outline {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: transparent;
}

.btn--outline:hover:not(:disabled) {
  background-color: var(--color-primary-light);
}

/* Ghost Button */
.btn--ghost {
  color: var(--color-primary);
  background: transparent;
}

.btn--ghost:hover:not(:disabled) {
  background-color: var(--color-neutral-100);
}

/* Sizes */
.btn--sm {
  padding: var(--space-2) var(--space-3);
  font-size: var(--fs-sm);
}

.btn--md {
  padding: var(--space-3) var(--space-4);
  font-size: var(--fs-base);
}

.btn--lg {
  padding: var(--space-4) var(--space-6);
  font-size: var(--fs-lg);
}

/* Full Width */
.btn--full {
  width: 100%;
}

/* Disabled State */
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

### Input Component (React)
```jsx
// Input.jsx
import { forwardRef } from 'react';
import './Input.css';

export const Input = forwardRef(({
  type = 'text',
  placeholder = '',
  label = '',
  error = '',
  helpText = '',
  disabled = false,
  ...props
}, ref) => {
  return (
    <div className="input-group">
      {label && (
        <label className="input-label">{label}</label>
      )}
      <div className="input-wrapper">
        <input
          ref={ref}
          type={type}
          placeholder={placeholder}
          className={`input ${error ? 'input--error' : ''} ${disabled ? 'input--disabled' : ''}`}
          disabled={disabled}
          {...props}
        />
      </div>
      {error && (
        <span className="input-error">{error}</span>
      )}
      {helpText && !error && (
        <span className="input-help">{helpText}</span>
      )}
    </div>
  );
});

Input.displayName = 'Input';

// Input.css
.input-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.input-label {
  font-size: var(--fs-sm);
  font-weight: var(--fw-semibold);
  color: var(--color-text-primary);
}

.input-wrapper {
  position: relative;
}

.input {
  width: 100%;
  padding: var(--space-3);
  font-family: var(--font-body);
  font-size: var(--fs-base);
  border: 2px solid var(--color-border);
  border-radius: 0.5rem;
  background-color: var(--color-bg-primary);
  color: var(--color-text-primary);
  transition: all 0.2s;
}

.input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1);
}

.input:hover:not(.input--disabled):not(:focus) {
  border-color: var(--color-neutral-300);
}

.input--error {
  border-color: var(--color-error);
}

.input--error:focus {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.input--disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: var(--color-neutral-100);
}

.input-error {
  font-size: var(--fs-sm);
  color: var(--color-error);
  font-weight: var(--fw-medium);
}

.input-help {
  font-size: var(--fs-sm);
  color: var(--color-text-secondary);
}
```

### Card Component
```jsx
// Card.jsx
export function Card({ children, className = '', ...props }) {
  return (
    <div className={`card ${className}`} {...props}>
      {children}
    </div>
  );
}

// Card.css
.card {
  background-color: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
}

.card:hover {
  border-color: var(--color-primary-light);
  box-shadow: var(--shadow-md);
}

@media (max-width: 768px) {
  .card {
    padding: var(--space-4);
  }
}
```

### Loading State Component
```jsx
// Loading.jsx
export function Loading({ size = 'md', message = 'Loading...' }) {
  return (
    <div className={`loading loading--${size}`}>
      <div className="loading-spinner"></div>
      {message && <p className="loading-text">{message}</p>}
    </div>
  );
}

// Loading.css
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: var(--space-8);
}

.loading-spinner {
  border: 3px solid var(--color-neutral-200);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading--sm .loading-spinner {
  width: 24px;
  height: 24px;
  border-width: 2px;
}

.loading--md .loading-spinner {
  width: 40px;
  height: 40px;
  border-width: 3px;
}

.loading--lg .loading-spinner {
  width: 60px;
  height: 60px;
  border-width: 4px;
}

.loading-text {
  color: var(--color-text-secondary);
  font-size: var(--fs-sm);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

### Modal Component
```jsx
// Modal.jsx
import { useEffect } from 'react';

export function Modal({ isOpen, onClose, title, children }) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <>
      <div className="modal-overlay" onClick={onClose} />
      <div className="modal" role="dialog" aria-modal="true">
        <div className="modal-header">
          <h2 className="modal-title">{title}</h2>
          <button
            className="modal-close"
            onClick={onClose}
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>
        <div className="modal-body">
          {children}
        </div>
      </div>
    </>
  );
}

// Modal.css
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 999;
  animation: fadeIn 0.2s ease;
}

.modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: var(--color-bg-primary);
  border-radius: 0.75rem;
  box-shadow: var(--shadow-2xl);
  z-index: 1000;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
  animation: slideUp 0.3s ease;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-6);
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-size: var(--fs-2xl);
  font-weight: var(--fw-semibold);
}

.modal-close {
  background: none;
  border: none;
  font-size: var(--fs-xl);
  cursor: pointer;
  color: var(--color-text-secondary);
}

.modal-body {
  padding: var(--space-6);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translate(-50%, -40%);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%);
  }
}

/* Mobile responsive */
@media (max-width: 768px) {
  .modal {
    max-width: 95vw;
    max-height: 95vh;
  }
  
  .modal-header,
  .modal-body {
    padding: var(--space-4);
  }
}
```

---

## Part 3: Layout Patterns

### Responsive Grid Layout
```jsx
// ProductGrid.jsx
export function ProductGrid({ products }) {
  return (
    <div className="grid-container">
      <div className="product-grid">
        {products.map(product => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </div>
  );
}

// Styles
.grid-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--space-6);
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-6);
  
  @media (min-width: 768px) {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
  
  @media (min-width: 1024px) {
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  }
}
```

### Responsive Navigation
```jsx
// Navigation.jsx
import { useState } from 'react';

export function Navigation() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="navbar">
      <div className="nav-container">
        <div className="nav-logo">MyApp</div>
        
        <button
          className="nav-toggle"
          onClick={() => setIsOpen(!isOpen)}
          aria-expanded={isOpen}
        >
          <span></span>
          <span></span>
          <span></span>
        </button>
        
        <ul className={`nav-menu ${isOpen ? 'nav-menu--active' : ''}`}>
          <li><a href="/">Home</a></li>
          <li><a href="/features">Features</a></li>
          <li><a href="/pricing">Pricing</a></li>
          <li><a href="/contact">Contact</a></li>
        </ul>
      </div>
    </nav>
  );
}

// Navigation.css
.navbar {
  background-color: var(--color-bg-primary);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: var(--space-4);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-logo {
  font-size: var(--fs-xl);
  font-weight: var(--fw-bold);
  color: var(--color-primary);
}

.nav-menu {
  display: flex;
  list-style: none;
  gap: var(--space-6);
  margin: 0;
  padding: 0;
}

.nav-menu a {
  text-decoration: none;
  color: var(--color-text-primary);
  font-weight: var(--fw-medium);
  transition: color 0.2s;
}

.nav-menu a:hover {
  color: var(--color-primary);
}

.nav-toggle {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  flex-direction: column;
  gap: 6px;
}

.nav-toggle span {
  width: 25px;
  height: 3px;
  background-color: var(--color-text-primary);
  border-radius: 2px;
  transition: all 0.3s;
}

/* Mobile Menu */
@media (max-width: 768px) {
  .nav-toggle {
    display: flex;
  }
  
  .nav-menu {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    flex-direction: column;
    gap: 0;
    background-color: var(--color-bg-secondary);
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
  }
  
  .nav-menu--active {
    max-height: 500px;
  }
  
  .nav-menu li {
    border-bottom: 1px solid var(--color-border);
  }
  
  .nav-menu a {
    display: block;
    padding: var(--space-4);
  }
}
```

---

## Part 4: Interaction Patterns

### Form Validation Pattern
```jsx
// useForm Hook
import { useState } from 'react';

export function useForm(initialValues, onSubmit) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setValues(prev => ({ ...prev, [name]: value }));
  };

  const handleBlur = (e) => {
    const { name } = e.target;
    setTouched(prev => ({ ...prev, [name]: true }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const newErrors = await onSubmit(values);
    if (newErrors) {
      setErrors(newErrors);
    }
  };

  return {
    values,
    errors,
    touched,
    handleChange,
    handleBlur,
    handleSubmit,
  };
}

// Usage
function LoginForm() {
  const { values, errors, touched, handleChange, handleBlur, handleSubmit } =
    useForm(
      { email: '', password: '' },
      async (values) => {
        // Validate and submit
      }
    );

  return (
    <form onSubmit={handleSubmit}>
      <Input
        name="email"
        type="email"
        value={values.email}
        onChange={handleChange}
        onBlur={handleBlur}
        error={touched.email && errors.email}
      />
      <Input
        name="password"
        type="password"
        value={values.password}
        onChange={handleChange}
        onBlur={handleBlur}
        error={touched.password && errors.password}
      />
      <Button type="submit" fullWidth>Sign In</Button>
    </form>
  );
}
```

### Error Boundary Pattern
```jsx
// ErrorBoundary.jsx
import { Component } from 'react';

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <Button onClick={() => window.location.reload()}>
            Reload Page
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

---

## Part 5: Accessibility Checklist

- [ ] Semantic HTML: `<button>`, `<nav>`, `<main>`, `<section>`
- [ ] ARIA labels: `aria-label`, `aria-describedby` on complex elements
- [ ] Keyboard navigation: All interactive elements focusable
- [ ] Focus indicators: Visible focus states on all interactive elements
- [ ] Color contrast: 4.5:1 for normal text, 3:1 for large text
- [ ] Alt text: Meaningful alt text for all images
- [ ] Form labels: Associated `<label>` elements for all inputs
- [ ] Error messages: Linked to form fields with `aria-describedby`
- [ ] Skip links: Navigation skip to main content
- [ ] Screen reader testing: Test with NVDA or JAWS
- [ ] Mobile accessibility: Touch targets ≥ 44x44px
- [ ] Reduced motion: Respect `prefers-reduced-motion`

```css
/* Accessibility improvements */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Focus indicators */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

button:focus-visible,
a:focus-visible,
input:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

---

## Summary

This component library provides:
1. **Consistent Design Tokens** across colors, typography, and spacing
2. **Reusable Components** following best practices
3. **Responsive Patterns** for desktop and mobile
4. **Interaction Patterns** for common use cases
5. **Accessibility** built-in from the start
6. **Performance** with minimal CSS and JS

Start with these components and customize based on your brand identity and project needs.
