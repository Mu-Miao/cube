import type { App } from 'vue'
import { ElButton } from 'element-plus/es/components/button/index.mjs'
import { ElDialog } from 'element-plus/es/components/dialog/index.mjs'
import { ElForm, ElFormItem } from 'element-plus/es/components/form/index.mjs'
import { ElIcon } from 'element-plus/es/components/icon/index.mjs'
import { ElInput } from 'element-plus/es/components/input/index.mjs'
import { ElLoading } from 'element-plus/es/components/loading/index.mjs'
import { ElOption, ElSelect } from 'element-plus/es/components/select/index.mjs'
import { ElSlider } from 'element-plus/es/components/slider/index.mjs'
import { ElSwitch } from 'element-plus/es/components/switch/index.mjs'
import { ElTabPane, ElTabs } from 'element-plus/es/components/tabs/index.mjs'
import { ElTable, ElTableColumn } from 'element-plus/es/components/table/index.mjs'
import { ElTag } from 'element-plus/es/components/tag/index.mjs'

let installed = false
let styleLoadPromise: Promise<unknown[]> | null = null

function loadElementStyles() {
  styleLoadPromise ??= Promise.all([
    import('element-plus/theme-chalk/base.css'),
    import('element-plus/theme-chalk/el-button.css'),
    import('element-plus/theme-chalk/el-dialog.css'),
    import('element-plus/theme-chalk/el-form.css'),
    import('element-plus/theme-chalk/el-form-item.css'),
    import('element-plus/theme-chalk/el-icon.css'),
    import('element-plus/theme-chalk/el-input.css'),
    import('element-plus/theme-chalk/el-loading.css'),
    import('element-plus/theme-chalk/el-message.css'),
    import('element-plus/theme-chalk/el-message-box.css'),
    import('element-plus/theme-chalk/el-notification.css'),
    import('element-plus/theme-chalk/el-option.css'),
    import('element-plus/theme-chalk/el-overlay.css'),
    import('element-plus/theme-chalk/el-select.css'),
    import('element-plus/theme-chalk/el-slider.css'),
    import('element-plus/theme-chalk/el-switch.css'),
    import('element-plus/theme-chalk/el-tab-pane.css'),
    import('element-plus/theme-chalk/el-table.css'),
    import('element-plus/theme-chalk/el-table-column.css'),
    import('element-plus/theme-chalk/el-tabs.css'),
    import('element-plus/theme-chalk/el-tag.css'),
  ])
  return styleLoadPromise
}

export async function installElementPlus(app: App) {
  if (installed) return
  await loadElementStyles()

  const elementComponents = [
    ElButton,
    ElDialog,
    ElForm,
    ElFormItem,
    ElIcon,
    ElInput,
    ElOption,
    ElSelect,
    ElSlider,
    ElSwitch,
    ElTabPane,
    ElTable,
    ElTableColumn,
    ElTabs,
    ElTag,
  ]

  elementComponents.forEach((component) => {
    app.use(component)
  })
  app.use(ElLoading)
  installed = true
}
