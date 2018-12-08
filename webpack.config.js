var path = require('path');
var BundleTracker = require('webpack-bundle-tracker');
var ExtractTextPlugin = require("extract-text-webpack-plugin");

module.exports = {
  context: __dirname,
  entry: './app/static/src/index.js',
  output: {
      path: path.resolve('./app/static/'),
      filename: "[name]-[hash].js"
  },
  plugins: [
    new ExtractTextPlugin('css/muspy.css'),
    new BundleTracker({filename: './webpack-stats.json'})
  ],
  module: {
    rules: [{
      test: /\.scss$/,
      use: ExtractTextPlugin.extract({
        fallback: 'style-loader',
        use: [
          'css-loader',
          'sass-loader'
        ]
      })
    }]
  },
};
