var subclasses = []

async function getData(url) {
    return fetch(url)
    .then(response => response.json())
    .catch(error => console.log(error));
  }

async function populate_races() {
  var data = await Promise.all([getData("/api/races")]);

  let races = data[0].races;
  races.sort();

  for (i=0; i<races.length; i++) {
    $('#racename').append(`<option value="${races[i]}">${races[i]}</option>`);
  }

  let subraces = data[0].subraces;
  console.log(subraces);
};

async function populate_class() {
  var data = await Promise.all([getData("/api/classes")]);

  let classes = data[0].classes;
  classes.sort();

  for (i=0; i<classes.length; i++) {
    $('#classname').append(`<option value="${classes[i]}">${classes[i]}</option>`);
  }
  subclasses = data[0].subclasses;
  console.log(subclasses);
};

$(document).ready(function() {
    populate_races();
    populate_class();
});

$(document).on('change', '#racename', function(){
  console.log("Race changed");
});

$(document).on('change', '#classname', function(){
  console.log("Class changed");
  console.log(subclasses);

  let classname = $(this).val();
  let subclasses_names = subclasses.Barbarian;
  console.log(subclasses[0]);
  console.log(subclasses_names);
  console.log(classname);
});