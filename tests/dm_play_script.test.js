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
const all = require('./dm_play_script.js');
// console.log(dm_play_script);
const io = require('socket.io-client');
const http = require('http');
const ioBack = require('socket.io');

let socket;
let httpServer;
let httpServerAddr;
let ioServer;

test('use jsdom in this test file', () => {
  const $ = require('jquery');
  window.$ = $;
  const element = document.createElement('div');
  expect(element).not.toBeNull();
});

test('Test constants are as expected', () => {
  const $ = require('jquery');
  const callback = jest.fn();
  all(callback);
  expect(initiatives).toMatchObject([]);
  expect(turn_index).toBeNull();
  const username_content = $('#username').text();
  expect(username).toMatch(username_content);
  const room_id_content = $('#room_id').text();
  expect(room_id).toMatch(room_id_content);
  expect(checklist).toMatch(`<ul id=checklist class="list-group list-group-flush">
                      <li class="list-group-item">
                        <div class="custom-control custom-checkbox">
                          <input type="checkbox" class="custom-control-input" id=movement_checklist>
                          <label class="custom-control-label" for=movement_checklist>Movement</label>
                        </div>
                      </li>
                      <li class="list-group-item">
                      <div class="custom-control custom-checkbox">
                          <input type="checkbox" class="custom-control-input" id=action_checklist>
                          <label class="custom-control-label" for=action_checklist>Action</label>
                        </div>
                      </li>
                      <li class="list-group-item">
                      <div class="custom-control custom-checkbox">
                          <input type="checkbox" class="custom-control-input" id=bonus_action_checklist>
                          <label class="custom-control-label" for=bonus_action_checklist>Bonus Action</label>
                        </div>
                      </li>
                    </ul>`)
  expect(namespace).toMatch('/combat');
  // const io_namespace = io(namespace)
  // expect(socket).toMatch(io_namespace);
});

test('Set Initiative', () => {
  document.body.innerHTML = html;
  const set_initiative = document.getElementById('set_initiative');
  set_initiative.submit();
  expect(document.getElementById('initiative_roll').value).toBe("");
});