var subclasses = [];
var subraces = [];

async function getData(url) {
  /* The getData function. This function gets
  JSON information from the API 
  
  :param url:
    the URL of the API */
    return fetch(url)
    .then(response => response.json())
    .catch(error => console.log(error));
  }

async function populate_races() {
  /* The populate_races function.n THis function
  populates the race select options */
  var data = await Promise.all([getData("/api/races")]);

  let races = data[0].races;
  races.sort();

  for (i=0; i<races.length; i++) {
    $('#racename').append(`<option value="${races[i]}">${races[i]}</option>`);
  }

  subraces = data[0].subraces;
  
  var old_racename = document.getElementById('old_race').value;
  var old_subrace = document.getElementById('old_subrace').value;
  document.getElementById('racename').value=`${old_racename}`;
  change_race();
  document.getElementById('subrace').value=`${old_subrace}`;
};

async function populate_class() {
  /* The populate_class function. This function
  populates the class select options. */
  var data = await Promise.all([getData("/api/classes")]);

  let classes = data[0].classes;
  classes.sort();

  for (i=0; i<classes.length; i++) {
    $('#classname').append(`<option value="${classes[i]}">${classes[i]}</option>`);
  }
  subclasses = data[0].subclasses;

  var old_class = document.getElementById('old_class').value;
  var old_subclass = document.getElementById('old_subclass').value;
  document.getElementById('classname').value=`${old_class}`;
  change_class();
  document.getElementById('subclass').value=`${old_subclass}`;
};

function get_option_html(property_name, objectt) {
  /* The get_option_html function. This
  function creates the options for the "sub" selects. 
  
  :param property_name:
    The name of the property being used: class or Race
  :param objectt:
    the mapping of classes to subclasses or races to subraces */
  var html_code = "";

  for (i=0; i<objectt[property_name].length; i++) {
    html_code += `<option>${objectt[property_name][i]}</option>`;
  }
  
  return html_code;
}

$(document).ready(function() {
  /* The document.ready function. This
  function runs when the page is fully loaded. */
    populate_races();
    populate_class();
});

// Updates the subraces when the selection in the "race" tab changes
$(document).on('change', '#racename', change_race);

function change_race() {
  /* The change_race function. This function
  is called when the race select is changed,
  updating the subrace select. */ 
  let racename = $('#racename').val();
  let html_code = "";

  if (racename == "") {
    html_code = "<option>Choose a Race!</object>";
  }
  else {
    html_code += get_option_html(racename, subraces)
  }

  $('#subrace').html(html_code);
}

// Updates the subclasses when the selection in the "subclass" tab changes
$(document).on('change', '#classname', change_class);

function change_class() {
  /* The change_class function. This function
  is called when the class select is changed,
  updating the subclass select. */
  let classname = $('#classname').val();
  let html_code = "";

  if (classname == "") {
    html_code = "<option>Choose a Class!</object>";
  }
  else {
    html_code += get_option_html(classname, subclasses)
  }

  $('#subclass').html(html_code);
}