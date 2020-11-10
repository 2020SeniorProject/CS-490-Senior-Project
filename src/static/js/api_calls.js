var subclasses = [];
var subraces = [];

// Gets API data or throws an error (handles error too)
async function getData(url) {
    return fetch(url)
    .then(response => response.json())
    .catch(error => console.log(error));
  }

// Populates the select options for the "race" tab
async function populate_races() {
  var data = await Promise.all([getData("/api/races")]);

  let races = data[0].races;
  races.sort();

  for (i=0; i<races.length; i++) {
    $('#racename').append(`<option value="${races[i]}">${races[i]}</option>`);
  }

  subraces = data[0].subraces;
};

// Populates the select options for the "class" tab
async function populate_class() {
  var data = await Promise.all([getData("/api/classes")]);

  let classes = data[0].classes;
  classes.sort();

  for (i=0; i<classes.length; i++) {
    $('#classname').append(`<option value="${classes[i]}">${classes[i]}</option>`);
  }
  subclasses = data[0].subclasses;
};

// Using the store objects from API (essentially dictionaries), gets the options that match the selected property
function get_option_html(property_name, objectt) {
  var html_code = "";
  for (i=0; i<objectt[property_name].length; i++) {
    html_code += `<option>${objectt[property][i]}</option>`;
  }
  return html_code;
}

// Calls the populate functions when the document loads
$(document).ready(function() {
    populate_races();
    populate_class();
});

// Updates the subraces when the selection in the "race" tab changes
$(document).on('change', '#racename', function(){
  let racename = $(this).val();
  let html_code = "";

  if (racename == "") {
    html_code = "<option>Choose a Race!</object>";
  }
  else {
    html_code += get_option_html(racename, subraces)
  }

  $('#subrace').html(html_code);
});

// Updates the subclasses when the selection in the "subclass" tab changes
$(document).on('change', '#classname', function(){
  let classname = $(this).val();
  let html_code = "";

  if (classname == "") {
    html_code = "<option>Choose a Class!</object>";
  }
  else {
    html_code += get_option_html(classname, subclasses)
  }

  $('#subclass').html(html_code);
});