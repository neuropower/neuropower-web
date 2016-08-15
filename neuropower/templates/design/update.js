<script type="text/javascript">

var figSel = d3.select("#magic");

var identityScale = d3.scale.linear()
  .range([0,1000]);

//The data for our line
var lineData = [ { "x": 1,   "y": 5},  { "x": 20,  "y": 20},
                 { "x": 40,  "y": 10}, { "x": 600,  "y": 40},
                 { "x": 200,  "y": 5},  { "x": 100, "y": 600}];

var svgSel = figSel.append("svg")
 .attr("width",200)
 .attr("height",200);

//This is the accessor function we talked about above
var lineFunc = d3.svg.line()
    .x(function(d) { return d.x; })
    .y(function(d) { return d.y; })
    .interpolate("linear");

var lineGraph = svgSel.append("path")
                            .attr("d", lineFunc(lineData))
                            .attr("stroke", "blue")
                            .attr("stroke-width", 2)
                            .attr("fill", "none");

</script>
