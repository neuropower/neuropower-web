<script type="text/javascript">

var margin = {top: 20, right: 20, bottom: 30, left: 50},
    width = 500 - margin.left - margin.right,
    height = 300 - margin.top - margin.bottom;

var xScale = d3.scale.linear()
  .domain([0,100])
  .range([margin.left,width-margin.right]);

var xAxis = d3.svg.axis()
  .orient("bottom")
  .scale(xScale);

var svg = d3.select("#magic").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom);

// where x-axis starts
svg.append("g")
  .attr("transform", "translate(0," + (height-margin.top) + ")")
  .call(xAxis);

var lineData = JSON.parse('{{ text | escapejs }}');
console.log(lineData)
var lineFunc = d3.svg.line()
    .x(function(d) { return margin.left+d.Gen/500*(width-margin.left-margin.right); })
    .y(function(d) { return (height-margin.top-margin.bottom)/5*4; })
    .interpolate("linear");

var lineGraph = svg.append("path")
                          .attr("d", lineFunc(lineData))
                          .attr("stroke", "blue")
                          .attr("stroke-width", 10)
                          .attr("fill", "red");

var text = svg.append("text")
  .attr("x",20)
  .attr("y",50)
  .attr("dy",".35em")
  .text("Percentage done...");
</script>
