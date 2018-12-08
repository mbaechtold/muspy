var path = require('path');
var BundleTracker = require('webpack-bundle-tracker');

module.exports = {
  context: __dirname,
  entry: './app/static/src/index.js',
  output: {
      path: path.resolve('./static/muspy/js'),
      filename: "[name]-[hash].js"
  },
  plugins: [
    new BundleTracker({filename: './tmp/webpack-stats-production.json'})
  ],
};
