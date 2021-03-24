/**
 * @jest-environment jsdom
 */


const $ = require('jquery');
const dm_play_script = require('../static/js/dm_play_script');

test('use jsdom in this test file', () => {
    const element = document.createElement('div');
    expect(element).not.toBeNull();
  });