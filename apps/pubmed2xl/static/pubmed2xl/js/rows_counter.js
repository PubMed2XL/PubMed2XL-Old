var lines = document.querySelector("#id_pmids").value.split(/\r\n|\r|\n/);
$('#count').text(lines.length);
$(document).ready(function(){
  $("textarea").keyup(function(){
    var lines = $("textarea").val().split(/\r|\r\n|\n/);
    $('#count').text(lines.length);
  });
  $("textarea").keydown(function(){
    var lines = $("textarea").val().split(/\r|\r\n|\n/);
    $('#count').text(lines.length);
  }); 
});