const WebpackMerge = require('webpack-merge');
const dev = require('./webpack.dev.config.js');

const BundleTracker = require('webpack-bundle-tracker');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = WebpackMerge(dev, {
  mode: "production",
  output: {
    filename: "[name].[hash].js"
  },
  plugins: [
    new MiniCssExtractPlugin({filename: '[name].[hash].css'}),
    new BundleTracker({filename: './tmp/webpack-stats-prod.json'})
  ],
});
