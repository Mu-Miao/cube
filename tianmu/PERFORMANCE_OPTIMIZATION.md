# Tianmu Frontend Performance Optimization Notes

Date: 2026-07-22

This note documents the Vue/Vite first-load optimization work done in `tianmu`.
It focuses on what changed, why it changed, and how the result was verified.

## Goal

The frontend was slow on first open because the initial page could pull too much shared code and styling before the user actually needed it.

The main goal was to reduce first-load cost without changing product behavior:

- Keep existing route behavior and page UI intact.
- Move heavy libraries out of the startup path.
- Keep `/public` lightweight, because it is now the default entry route.
- Keep `/teen` dashboard features available when the user enters the authenticated console.

## What Changed

### 1. Element Plus is no longer registered at app startup

Before, `src/main.ts` imported and installed all of Element Plus:

```ts
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

app.use(ElementPlus)
```

That made the app pay the Element Plus cost immediately, even on routes that do not use it.

Now `src/main.ts` only loads Element Plus when navigating into `/teen`:

```ts
router.beforeEach(async (to) => {
  if (to.path.startsWith('/teen')) {
    const { installElementPlus } = await import('@/plugins/elementPlus')
    await installElementPlus(app)
  }
})
```

The actual component registration lives in `src/plugins/elementPlus.ts`.

Why: `/public` is the default first page and does not need Element Plus. Deferring Element Plus keeps the public first-load path smaller.

### 2. Element Plus components are registered by actual usage

`src/plugins/elementPlus.ts` registers only the components currently used by the app, such as:

- `ElButton`
- `ElDialog`
- `ElForm`
- `ElInput`
- `ElSelect`
- `ElSlider`
- `ElSwitch`
- `ElTable`
- `ElTabs`
- `ElTag`
- `ElLoading`

Element Plus service imports such as `ElMessage`, `ElMessageBox`, and `ElNotification` were also changed from the package root to component-level entries.

Why: package-root imports make it easier for the bundler to include more of the UI library than needed.

### 3. ECharts is loaded only when charts are initialized

`src/views/Dashboard.vue` and `src/views/AiAnalysis.vue` previously imported ECharts statically:

```ts
import * as echarts from 'echarts'
```

Now both pages load it with dynamic import when the chart DOM is ready:

```ts
const echarts = await loadEcharts()
chart = echarts.init(chartRef.value)
```

Why: ECharts is the largest frontend dependency in this build. It should not be part of the generic startup path.

### 4. The 3.2 MB boot GIF is no longer bundled into Dashboard

`src/components/brand/MascotCompanion.vue` used to import the boot GIF from `src/assets`:

```ts
import bootSleep from '@/assets/mascot/boot_sleep.gif'
```

Now the boot state references the public asset path:

```ts
image: '/boot_sleep.gif'
```

Why: importing the GIF from `src/assets` made Vite include it in the build graph. The GIF is large and should not be pulled into a route chunk just because the component exists.

### 5. Vite now has explicit manual chunks

`vite.config.ts` now separates major dependency groups:

- `vue`
- `api-client`
- `element-plus`
- `echarts`
- `three`
- `vendor`

Why: stable chunk boundaries make the build easier to inspect and improve browser caching after deployment.

## Build Result

Verified with:

```bash
npm run build
```

The build and type-check passed.

Important size changes observed from the Vite build output:

| Asset area | Before | After |
| --- | ---: | ---: |
| Main entry JS | about 911 KB | about 7.2 KB |
| Main CSS | about 367 KB | about 16.6 KB |
| ECharts | about 1.11 MB | still separate, loaded by chart pages |
| `boot_sleep.gif` in build assets | about 3.3 MB | no longer emitted from `src/assets` |

Note: Element Plus still exists as its own chunk because `/teen` routes need it. The important improvement is that the app entry no longer directly installs the whole library.

## Runtime Verification

After building, the production preview server was started with:

```bash
npm run preview -- --host 127.0.0.1 --port 4173
```

The following routes returned `200 OK`:

- `/`
- `/public`
- `/teen/dashboard`

That confirmed the built SPA still serves both the default public route and the teen dashboard route.

## Remaining Opportunities

The largest remaining chunk is ECharts. It is already isolated, but it is still large when chart pages load. Future work could reduce it further by importing only the specific ECharts charts/components used by the app.

Element Plus CSS is still emitted as a separate stylesheet. It is much smaller than the original full CSS import, but if `/public` first paint needs to be extremely lean, the next step is to verify whether Vite can avoid injecting that stylesheet into `index.html` for the default route or whether the deployment layer should defer it.

Image optimization is also still worth doing:

- `public/mzh5(1).glb` is about 8.9 MB.
- `public/smart-cube-transparent.png` is about 161 KB after compression.
- `public/cube-logo.png` and `src/assets/brand/cube-logo.png` are about 199 KB each.

Those are not all necessarily first-load blockers, but they are good next targets once network traces confirm when each asset is requested.
