<script type="text/javascript">

var margin = {top: 20, right: 20, bottom: 30, left: 50},
    width = 960 - margin.left - margin.right,
    height = 500 - margin.top - margin.bottom;

var svg = d3.select("#magic").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var x = d3.time.scale()
    .range([0, width]);

var y = d3.scale.linear()
    .range([height, 0]);

var xAxis = d3.svg.axis()
    .scale(x)
    .orient("bottom");

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left");

var lineData = JSON.parse("/Users/Joke/Documents/Onderzoek/ProjectsOngoing/ly29baxbc93w5pc1a7u2jc5gqe73tla9.json");
//
// var lineFunc = d3.svg.line()
//     .x(function(d) { return d.Gen; })
//     .y(function(d) { return d.Best; })
//     .interpolate("linear");
//
// var lineGraph = svgSel.append("path")
//                             .attr("d", lineFunc(lineData))
//                             .attr("stroke", "blue")
//                             .attr("stroke-width", 2)
//                             .attr("fill", "none");

    var lines = svg.append("circle")
      .attr("cx",10)
      .attr("cy",10)
      .attr("r",20)
      .attr("fill","red");

</script>
