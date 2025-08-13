# TypeScript Configuration Guide

This document outlines the comprehensive TypeScript configuration for the Multi-Bot RAG Platform frontend.

## Configuration Overview

Our TypeScript setup uses strict mode with additional type checking rules to ensure maximum type safety and code quality.

### Key Features

- **Strict Mode**: All strict mode flags are enabled
- **Exact Optional Properties**: Prevents undefined from being assigned to optional properties
- **No Unchecked Indexed Access**: Requires explicit checks for array/object access
- **Path Mapping**: Convenient import aliases for better code organization
- **Comprehensive Type Definitions**: Centralized type system in `/src/types/`

## Configuration Files

### `tsconfig.json` (Main Configuration)

```json
{
  "compilerOptions": {
    // Strict Type Checking
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true,

    // Additional Checks
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "allowUnreachableCode": false,
    "allowUnusedLabels": false,

    // Path Mapping
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@/components/*": ["src/components/*"],
      "@/hooks/*": ["src/hooks/*"],
      "@/services/*": ["src/services/*"],
      "@/utils/*": ["src/utils/*"],
      "@/types/*": ["src/types/*"],
      "@/config/*": ["src/config/*"],
      "@/layouts/*": ["src/layouts/*"],
      "@/pages/*": ["src/pages/*"]
    }
  }
}
```

### `tsconfig.node.json` (Node Configuration)

Used for build tools and configuration files like Vite config.

## Type System Architecture

### Central Type Definitions (`/src/types/`)

Our type system is organized into logical modules:

- **`index.ts`** - Main export file with global utility types
- **`common.ts`** - Base interfaces and common types
- **`user.ts`** - User-related types
- **`auth.ts`** - Authentication types
- **`api.ts`** - API request/response types
- **`bot.ts`** - Bot configuration types
- **`chat.ts`** - Chat and messaging types
- **`document.ts`** - Document management types
- **`form.ts`** - Form validation types
- **`routing.ts`** - Navigation and routing types
- **`error.ts`** - Error handling types
- **`offline.ts`** - Offline functionality types

### Key Type Features

#### Brand Types for Type Safety
```typescript
export type Brand<T, B> = T & { __brand: B };
export type UserId = Brand<string, 'UserId'>;
export type BotId = Brand<string, 'BotId'>;
```

#### Utility Types
```typescript
export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;
export type Maybe<T> = T | null | undefined;
export type DeepPartial<T> = { [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P] };
```

#### Async State Management
```typescript
export interface UseAsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (...args: any[]) => Promise<void>;
  reset: () => void;
}
```

## Strict Mode Benefits

### 1. Exact Optional Properties (`exactOptionalPropertyTypes: true`)

Prevents assigning `undefined` to optional properties:

```typescript
// ❌ Error with exactOptionalPropertyTypes
interface User {
  name: string;
  email?: string;
}

const user: User = {
  name: "John",
  email: undefined // Error: undefined not assignable to string
};

// ✅ Correct approach
const user: User = {
  name: "John"
  // email is omitted, not set to undefined
};
```

### 2. No Unchecked Indexed Access (`noUncheckedIndexedAccess: true`)

Requires explicit checks for array/object access:

```typescript
// ❌ Error: Element implicitly has 'any' type
const items = ['a', 'b', 'c'];
const first = items[0]; // Type: string | undefined

// ✅ Correct approach
const first = items[0];
if (first) {
  // first is now type: string
  console.log(first.toUpperCase());
}
```

### 3. Strict Null Checks

All variables must be explicitly typed to handle null/undefined:

```typescript
// ❌ Error: Object is possibly 'null'
function processUser(user: User | null) {
  return user.name; // Error
}

// ✅ Correct approach
function processUser(user: User | null) {
  if (user) {
    return user.name; // Safe access
  }
  return null;
}
```

## Path Mapping Usage

Use convenient import aliases instead of relative paths:

```typescript
// ❌ Avoid relative imports
import { User } from '../../../types/user';
import { apiClient } from '../../../services/api';

// ✅ Use path mapping
import { User } from '@/types/user';
import { apiClient } from '@/services/api';
```

## Best Practices

### 1. Type Guards
```typescript
function isUser(obj: any): obj is User {
  return obj && typeof obj.id === 'string' && typeof obj.email === 'string';
}
```

### 2. Discriminated Unions
```typescript
type ApiResponse<T> = 
  | { success: true; data: T }
  | { success: false; error: string };
```

### 3. Generic Constraints
```typescript
interface Repository<T extends { id: string }> {
  findById(id: string): Promise<T | null>;
  save(entity: T): Promise<T>;
}
```

### 4. Conditional Types
```typescript
type NonNullable<T> = T extends null | undefined ? never : T;
```

## Error Handling with Strict Types

Our error handling system is fully typed:

```typescript
interface AppError {
  type: ErrorType;
  message: string;
  statusCode?: number;
  retryable: boolean;
  context?: ErrorContext;
}
```

## Form Validation Types

Type-safe form handling:

```typescript
interface FormState<T> {
  values: T;
  errors: Record<keyof T, string[]>;
  touched: Record<keyof T, boolean>;
  isValid: boolean;
}
```

## Migration Guide

When upgrading existing code to strict mode:

1. **Fix Optional Properties**: Remove explicit `undefined` assignments
2. **Add Null Checks**: Handle nullable values explicitly
3. **Type Array Access**: Check array bounds before access
4. **Use Type Guards**: Implement proper type checking
5. **Update Imports**: Use path mapping aliases

## IDE Integration

### VS Code Settings

Add to `.vscode/settings.json`:

```json
{
  "typescript.preferences.includePackageJsonAutoImports": "on",
  "typescript.suggest.autoImports": true,
  "typescript.preferences.importModuleSpecifier": "non-relative"
}
```

### ESLint Integration

Our TypeScript rules work with ESLint for comprehensive code quality.

## Performance Considerations

- **Incremental Compilation**: Project references for faster builds
- **Skip Lib Check**: Enabled for faster compilation
- **Isolated Modules**: Each file can be compiled independently

## Troubleshooting

### Common Issues

1. **"Object is possibly undefined"**
   - Add null checks or use optional chaining
   - Use type guards for complex objects

2. **"Property does not exist on type"**
   - Check your type definitions
   - Use type assertions carefully

3. **"Cannot assign undefined to optional property"**
   - Omit the property instead of setting to undefined
   - Use conditional assignment

### Debug Commands

```bash
# Type check without emitting
npx tsc --noEmit

# Show detailed type information
npx tsc --listFiles

# Generate declaration files
npx tsc --declaration --emitDeclarationOnly
```

## Conclusion

This strict TypeScript configuration provides:

- **Maximum Type Safety**: Catch errors at compile time
- **Better Developer Experience**: Excellent IDE support
- **Maintainable Code**: Clear contracts and interfaces
- **Performance**: Optimized compilation and runtime safety

The investment in strict typing pays dividends in code quality, maintainability, and developer productivity.