import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import {djangoVitePlugin} from "django-vite-plugin";

// https://vitejs.dev/config/
export default defineConfig({

  server: {
    hmr: false
  },
  plugins: [react(),
      djangoVitePlugin([
            'dist/src/App.jsx',
            'dist/src/App.css',
        ])
  ],

})
