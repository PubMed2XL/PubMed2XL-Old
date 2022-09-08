const textarea = document.querySelector("#id_pmids")
const counter = document.getElementById('count');
textarea.addEventListener('input', () => {
  const text = textarea.value;
  const lines = text.split("\n");
  const count = lines.length;
  row = " rows"
  if (count <= 1){
    row = " row"
  }
  counter.innerHTML = count + row;
})