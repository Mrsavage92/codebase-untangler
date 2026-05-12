# Stack Reference: React Native

Patterns for React Native apps (Expo or bare RN). Mobile-specific concerns: platform splits,
navigation, native modules, build pipelines.

---

## Detection

- `react-native` in `package.json`
- `app.json` / `app.config.js` (Expo) or `ios/` + `android/` directories (bare)
- `metro.config.js`

---

## Canonical layout

```
src/
  app/                # or screens/, if not using expo-router
    (tabs)/
    (auth)/
  components/
    ui/               # presentational, platform-aware
    features/         # feature-specific composites
  hooks/
  services/           # business logic
  api/                # HTTP clients (typed)
  store/              # zustand / redux
  types/
  utils/
  constants/
assets/
  fonts/
  images/
```

---

## Common vibe-code symptoms

### 1. Platform-specific code inline everywhere

**Symptom**: `Platform.OS === 'ios' ? x : y` scattered through dozens of components.

**Fix**: when a component has substantial divergence, split into `Component.ios.tsx` and
`Component.android.tsx`. Metro picks the right one. For small style tweaks, keep inline
but isolate to style objects.

### 2. Navigation logic mixed with screens

**Symptom**: screens calling `navigation.navigate('Foo', { id: 1 })` deep in their render
trees, with magic string route names.

**Fix**: typed navigation (`@react-navigation/native` with TypeScript). One module exports
all route names as constants. Screens receive navigation as a prop or via hook only at
the top level.

### 3. Async storage / secure storage used directly everywhere

**Symptom**: `AsyncStorage.getItem(...)` and `SecureStore.getItemAsync(...)` calls peppered
through the codebase.

**Fix**: storage helpers in `services/storage.ts`. Typed get/set per key. Centralised
migration logic.

### 4. State management chaos

**Symptom**: useState, useContext, Redux, Zustand, React Query all in one app.

**Fix**: pick the right tool per concern:
- **Server state**: React Query / SWR / TanStack Query
- **Auth / global app state**: Zustand or one Context
- **Form state**: react-hook-form
- **Local UI state**: useState

Migrate one feature at a time, strangler-fig style.

### 5. Direct API calls from components

**Symptom**: `fetch(...)` or `axios.get(...)` inside component render.

**Fix**: extract to `api/<resource>.ts` typed functions. Components use React Query
hooks that call those functions.

### 6. Native module imports breaking web/Expo Go

**Symptom**: top-level imports of native-only modules cause crashes on Expo Go or web builds.

**Fix**: lazy require, or platform-specific files (`.native.tsx`).

### 7. Massive `App.tsx`

**Symptom**: 500-line `App.tsx` with providers, navigation setup, deeplinks, auth gating,
analytics init.

**Fix**: split into focused providers - each one in its own file, composed in App.tsx.

### 8. No environment separation

**Symptom**: same API URL in dev and prod.

**Fix**: `expo-constants` or `react-native-config`. One `config.ts` reads env, exports
typed constants.

---

## Lint rules (Phase 4)

```json
{
  "extends": ["@react-native", "plugin:@typescript-eslint/recommended"],
  "plugins": ["boundaries", "react-native"],
  "rules": {
    "react-native/no-inline-styles": "warn",
    "react-native/no-unused-styles": "error",
    "react-native/split-platform-components": "error",
    "boundaries/element-types": ["error", {
      "default": "disallow",
      "rules": [
        { "from": "screens", "allow": ["components", "hooks", "services", "api"] },
        { "from": "components", "allow": ["components", "hooks"] },
        { "from": "services", "allow": ["api", "services", "utils"] },
        { "from": "api", "allow": ["utils"] }
      ]
    }]
  }
}
```

---

## Safety net patterns

- **Component tests**: `@testing-library/react-native` + Jest
- **E2E**: Detox (bare RN) or Maestro (cross-platform, simpler)
- **Visual regression**: `react-native-storybook` + Chromatic, if budget allows
- **Smoke checklist**: manual run-through on iOS sim + Android emulator for critical flows

For Phase 2, Maestro flows are the highest ROI: one YAML file per critical user flow,
runs on real or simulated devices.

---

## Tooling

- `eslint` with `@react-native/eslint-config`
- `tsc --noEmit` - type check (run in CI)
- `npx expo-doctor` (Expo) - config sanity
- `npx react-native-clean-project` - nuclear option for cache issues
- `madge --circular src/` - circular deps
- `knip` - unused exports/files/deps
- Bundle analyzer: `npx react-native-bundle-visualizer`

---

## Phase 4 guard rails specific to RN

Add to CLAUDE.md:

```
- Native module imports must be guarded for web/Expo Go compatibility
- All API calls go through `api/<resource>.ts` typed functions
- Storage keys defined as constants in `services/storage.ts`
- Navigation route names defined in `app/routes.ts`, never as string literals
- Platform-specific code uses `.ios.tsx` / `.android.tsx` splits, not inline ternaries
```
