function newFunction() {
    document.getElementById("demo").innerHTML = "Hallok";
}

function Cint() {
    const Car = {
      name:"Fiat",
      cost:500,
      cutesy:"Yes",
      cutesyAndName: function() {return this.name+this.cutesy}
    };
    document.getElementById("demo").innerHTML = Car.cutesyAndName;
}