const path = require('path');
const BundleTracker = require('webpack-bundle-tracker');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = {
  mode: "development",
  entry: path.resolve(__dirname, 'app/static/src/index.js'),
  output: {
      path: path.resolve(__dirname, 'app/static/dist/'),
      filename: "[name].js"
  },
  plugins: [
    new MiniCssExtractPlugin({filename: '[name].css'}),
    new BundleTracker({filename: './tmp/webpack-stats.json'})
  ],
  module: {
    rules: [{
      test: /\.scss$/,
      use: [
        MiniCssExtractPlugin.loader,
        'css-loader',
        'sass-loader'
      ]
    }]
  },
};
