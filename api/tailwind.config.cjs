const path = require('path');
module.exports = {
    content: [path.join(__dirname, 'app/templates/**/*.html'), path.join(__dirname, 'app/static/js/**/*.js')],
    theme: { extend: {} },
    plugins: []
};
