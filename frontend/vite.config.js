import { defineConfig } from 'vite'
import { djangoVitePlugin } from 'django-vite-plugin'

export default defineConfig({
    plugins: [
        djangoVitePlugin([
            'home/js/app.js',
            'home/css/style.css',
        ])
    ],
});