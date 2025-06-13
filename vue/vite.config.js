import path from 'path'
import { defineConfig, loadEnv } from 'vite'
import Icons from 'unplugin-icons/vite'
import IconsResolver from 'unplugin-icons/resolver'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import vueDevTools from 'vite-plugin-vue-devtools'
import { codeInspectorPlugin } from 'code-inspector-plugin';
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [
      vue(),
      vueDevTools(),
      Icons({
        autoInstall: true,
      }),
      AutoImport({
        resolvers: [
          ElementPlusResolver(),
          IconsResolver({
            prefix: 'Icon',
          }),
        ],
      }),
      Components({
        resolvers: [
          ElementPlusResolver(),
          IconsResolver({
            enabledCollections: ['ep'],
          }),
        ],
      }),
      codeInspectorPlugin({
        bundler: 'vite',
      }),
    ],
    base: env.VITE_BASE || './',
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      host: '0.0.0.0',
      proxy: {
        '/video': {
          target: 'http://localhost:8080',
          changeOrigin: true,
          // rewrite: (path) => path.replace(/^\/video/, ''), // 重写路径，去掉 /api 前缀
          configure: (proxy, options) => {
            proxy.on('proxyReq', (proxyReq, req, res) => {
              const realUrl = new URL(req.url, options.target).href;
              proxyReq.setHeader('x-real-url', realUrl);
              const updatedHeaders = proxyReq.getHeaders();
              console.log('[Proxy] Updated Headers:', updatedHeaders['x-real-url']);
            })
            proxy.on('proxyRes', (proxyRes, req, res) => {
              const realUrl = new URL(req.url, options.target).href;
              proxyRes.headers['x-real-url'] = realUrl;
              console.log('[Proxy] Response Headers:', proxyRes.headers['x-real-url']);
            })
          }
        },
      },
    },
  }
})
