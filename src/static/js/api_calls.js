async function getData(url) {
    return fetch(url)
    .then(response => response.json())
    .catch(error => console.log(error));
  }
  
  async function apiTest(url) {
    let data = await Promise.all([getData(url)]);
    // console.log(data[0]); 
    document.querySelector("#demo").innerHTML = "";
    $('#demo').append($('<div/>').text("Classes:").html() + '<br>')
    for (i = 0; i < data[0].count; i++) {
      $('#demo').append('<br>' + $('<div/>').text(data[0].results[i].name).html())
    }
  }; 

async function testing() {
  var test = await Promise.all([getData("https://api.open5e.com/races/?format=json")]);
  var ret_test = [];
  for (i=0; i<9; i++) {
    console.log(test[0].results[i].name);
    ret_test.push(test[0].results[i].name)
  }
  return test
};

$(document).ready(function() {
    // When called this way, testing returns a promise. Instead, make testing call a function to populate the dropdowns
    let data = testing()
    console.log(data);
});