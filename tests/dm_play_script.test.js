/**
 * @jest-environment jsdom
 */

 const fs = require('fs');
 const path = require('path');

 jest.mock('../static/js/api_calls.js');
 jest.mock('../static/js/bootstrap.bundle.min.js');
 jest.mock('../static/js/map_image.js');
 jest.mock('../static/js/navbar.js');
 jest.mock('../static/js/page_resize.js');
 jest.mock('../static/js/script.js');

 jest
    .dontMock('fs');

// console.log(__dirname);
const html = fs.readFileSync(path.resolve(__dirname, '../templates/play.html'), 'utf8');
// console.log(html);
const $ = require('jquery');
// console.log($);
const dm_play_script = require('../tests/dm_play_script.js');
// console.log(dm_play_script);

test('use jsdom in this test file', () => {
    const element = document.createElement('div');
    expect(element).not.toBeNull();
  });

// test('Use the /combat namespace', () => {
//     expect(namespace).toMatch('/combat');
// });