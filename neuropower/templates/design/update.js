<script type='text/javascript' src="https://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.7.0/underscore-min.js"></script>
<script type='text/javascript'>

// function refresh() {
//     $.ajax({
//         url: '{% url "DRunGA" %}',
//         success: function(data) {
//             $('#magic').html(data);
//         }
//     });
//     setInterval("refresh()", 10000000);
// }
//
// $(function(){
//     refresh();
// });

var margin = {top: 20, right: 20, bottom: 30, left: 50},
    width = 500 - margin.left - margin.right,
    height = 300 - margin.top - margin.bottom;

var yScale=d3.scale.linear()
  .domain([0,100])
  .range([height-margin.top,margin.bottom]);

var xScale = d3.scale.linear()
  .domain([0,100])
  .range([margin.left,width-margin.right]);

var yAxis = d3.svg.axis()
  .orient("left")
  .scale(yScale);

var xAxis = d3.svg.axis()
  .orient("bottom")
  .scale(xScale);

var svg = d3.select("#magic").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom);

// where y-axis starts
svg.append("g")
  .attr("transform", "translate("+margin.left+",0)")
  .call(yAxis);

// where x-axis starts
svg.append("g")
  .attr("transform", "translate(0," + (height-margin.top) + ")")
  .call(xAxis);

var numcycles = Number( {{ runs }} );

console.log(numcycles);

var lineData = JSON.parse('{{ text | escapejs }}');
console.log(lineData)
var lineFunc = d3.svg.line()
    .x(function(d) { return margin.left+d.Gen/numcycles*(width-margin.left-margin.right); })
    .y(function(d) { return height-margin.top-d.Best/1000*(height-margin.top-margin.bottom); })
    .interpolate("linear");

var lineGraph = svg.append("path")
                          .attr("d", lineFunc(lineData))
                          .attr("stroke", "blue")
                          .attr("stroke-width", 4)
                          .attr("fill", "red");


</script>
