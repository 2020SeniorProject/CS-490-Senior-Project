// Called when the document fully loads
$('document').ready(function() {
    var previousSource = $(this).data('previousSource', $("#initial_image").val());
    console.log("connected");
});

// called when the input in the map_url html id is chnaged.
// Updates the displayed image.
$('#map_url').on('input', function() {
    console.log("sd'");
    var src = jQuery(this).val();
    var previews = $(".previewImage");
    var drawPreview = true;
    var PreviousSource = $(this).data('previousSource');
  
    if(!src.match("^https?://(?:[a-zA-Z0-9\-]+\.)+[a-z]{2,6}(?:/[^/#?]+)+\.(?:jpg|gif|png|jpeg|webp)$") && src != "") {
      $("#warning").html("Must be an image");
      return false;  
    } else {
      $("#warning").html("");
    }
  
    $.each(previews , function(index, value) { 
      if (src == "" && PreviousSource == $(value).attr('src')) {
        $(value).remove();
        drawPreview = false;
        return false; 
      }
      if($(value).attr('src') == src) {
        drawPreview = false;
        return false;
      }
    });

    if ($("#initial_image").length == 0) {
        $('#prev').append("<img class='previewImage' id=initial_image width=50%>");
    }
  
    if(drawPreview) {
      $('#initial_image').attr("src", src);   
    }
    
    var previousSource = $(this).data('previousSource', src);
  });