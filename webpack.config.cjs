const path = require('path');

module.exports = {
  entry: './static/home.js', // Entry point of your application
  output: {
    filename: 'my_bundle.js',
    path: path.resolve(__dirname, 'static/js'), // Output directory for bundled files
  },
  resolve: {
    alias: {
      '@nlux/core': path.resolve(__dirname, 'node_modules/@nlux/core'),
    },
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env'],
          },
        },
      },
    ],
  },
};
