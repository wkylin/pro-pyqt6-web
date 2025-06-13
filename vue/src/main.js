import { createApp } from 'vue'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import './style.css'

import App from './App.vue'

const root = createApp(App)
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  root.component(key, component)
}

root.mount('#app')
