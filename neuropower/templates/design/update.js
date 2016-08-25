<script type='text/javascript' src="https://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.7.0/underscore-min.js"></script>
<script type='text/javascript'>

// margins

var margin = {top: 20, right: 20, bottom: 30, left: 50},
    width = 500 - margin.left - margin.right,
    height = 300 - margin.top - margin.bottom;

// axes

var yScale=d3.scale.linear()
  .domain([0,100])
  .range([height-margin.top,margin.bottom]);

var xScale = d3.scale.linear()
  .domain([0,{{runs}}])
  .range([margin.left,width-margin.right]);

var yAxis = d3.svg.axis()
  .orient("left")
  .scale(yScale);

var xAxis = d3.svg.axis()
  .orient("bottom")
  .scale(xScale);

// define frame

var svg = d3.select("#magic").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom);

// draw axes

svg.append("g")
  .attr("transform", "translate("+margin.left+",0)")
  .call(yAxis)
  .attr("stroke", "black")
  .attr("stroke-width", 1)
  .attr("fill", 'none');

svg.append("g")
  .attr("transform", "translate(0," + (height-margin.top) + ")")
  .call(xAxis)
  .attr("stroke", "black")
  .attr("stroke-width", 1)
  .attr("fill", 'none');

var numcycles = Number( {{ runs }} );

var lineData = JSON.parse('{{ text | escapejs }}');

// Fe optimisation
var lineFunc = d3.svg.line()
    .x(function(d) { return margin.left+d.Gen/numcycles*(width-margin.left-margin.right); })
    .y(function(d) { return height-margin.top-d.FeBest/1000*(height-margin.top-margin.bottom); })
    .interpolate("linear");

var lineGraph = svg.append("path")
                          .attr("d", lineFunc(lineData))
                          .attr("stroke", "green")
                          .attr("stroke-width", 1)
                          .attr("fill","none");

// Fd optimisation
var lineFunc = d3.svg.line()
    .x(function(d) { return margin.left+d.Gen/numcycles*(width-margin.left-margin.right); })
    .y(function(d) { return height-margin.top-d.FdBest/1000*(height-margin.top-margin.bottom); })
    .interpolate("linear");

var lineGraph = svg.append("path")
                          .attr("d", lineFunc(lineData))
                          .attr("stroke", "purple")
                          .attr("stroke-width", 1)
                          .attr("fill","none");

// Fc optimisation
var lineFunc = d3.svg.line()
    .x(function(d) { return margin.left+d.Gen/numcycles*(width-margin.left-margin.right); })
    .y(function(d) { return height-margin.top-d.FcBest/1000*(height-margin.top-margin.bottom); })
    .interpolate("linear");

                          var lineGraph = svg.append("path")
                                                    .attr("d", lineFunc(lineData))
                                                    .attr("stroke", "orange")
                                                    .attr("stroke-width", 1)
                                                    .attr("fill","none");

// Ff optimisation
var lineFunc = d3.svg.line()
    .x(function(d) { return margin.left+d.Gen/numcycles*(width-margin.left-margin.right); })
    .y(function(d) { return height-margin.top-d.FfBest/1000*(height-margin.top-margin.bottom); })
    .interpolate("linear");

var lineGraph = svg.append("path")
                          .attr("d", lineFunc(lineData))
                          .attr("stroke", "red")
                          .attr("stroke-width", 1)
                          .attr("fill","none");

// Main optimisation
var lineFunc = d3.svg.line()
    .x(function(d) { return margin.left+d.Gen/numcycles*(width-margin.left-margin.right); })
    .y(function(d) { return height-margin.top-d.FBest/1000*(height-margin.top-margin.bottom); })
    .interpolate("linear");

var lineGraph = svg.append("path")
                          .attr("d", lineFunc(lineData))
                          .attr("stroke", "steelblue")
                          .attr("stroke-width", 4)
                          .attr("fill","none");

//legend
// define frame

var svg = d3.select("#legend").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom);




</script>
