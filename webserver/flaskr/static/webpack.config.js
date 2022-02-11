const webpack = require('webpack')

const config = {
    mode: "development",
    entry: __dirname + '/script.js',
    output: {
        path: __dirname + '/dist',
        filename: 'bundle.js',
    },
    resolve: {
        extensions: ['.js', '.jsx', '.css']
    },
    devtool: 'inline-source-map',
};

module.exports = config;