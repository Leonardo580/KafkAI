/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
      './templates/**/*.html',
      './node_modules/flowbite/**/*.js',
      'node_modules/preline/dist/*.js'
  ],
  theme: {
    extend: {},
  },
  plugins: [
      require('flowbite/plugin'),
      require('preline/plugin')
  ],

    "animation": {
            shimmer: "shimmer 2s linear infinite"
          },
          "keyframes": {
            shimmer: {
              from: {
                "backgroundPosition": "0 0"
              },
              to: {
                "backgroundPosition": "-200% 0"
              }
            }
          }
}