<script type='text/javascript' src="https://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.7.0/underscore-min.js"></script>
<script type='text/javascript' src="http://d3js.org/d3.v3.js"></script>
<script type="text/javascript">

var lineData = JSON.parse('{{ optim | escapejs }}');
var percentage = Object.keys(lineData).length / {{preruns}};

var chart = c3.generate({
  bindto:'#magic',
  size:{
    height:240,
    width:480
  },
  data: {
      columns: [
          ['show', percentage],
          ['dontshow', 1 - percentage],
      ],
      type: 'donut',
      order: null
  },
  color: {
      pattern: ['#8D181B', '#FFF']
  },
  legend: {
      show: false
  },
  donut: {
      label: {
          show: false
      },
      title: Math.round(percentage * 100),
      width: 15,
      expand: false
  },
  tooltip: {
      show: false
  }
});

// baseline text properly
d3
    .select(".c3-chart-arcs-title")
    .attr("dy", "0.3em")

// add percentage symbol
d3.select(".c3-chart-arcs")
    .append("text")
    .text("%")
    .attr("dy", "-0.5em")
    .attr("dx", "2em")

// black background for center text
d3.select(".c3-chart")
    .insert("circle", ":first-child")
    .attr("cx", chart.internal.width / 2)
    .attr("cy", chart.internal.height / 2 - chart.internal.margin.top)
    .attr("fill",'#6a6768')
    .attr("r", chart.internal.innerRadius)

//
//
//
// var margin = {top: 20, right: 20, bottom: 30, left: 50},
//     width = 500 - margin.left - margin.right,
//     height = 300 - margin.top - margin.bottom;
//
// var xScale = d3.scale.linear()
//   .domain([0,100])
//   .range([margin.left,width-margin.right]);
//
// var xAxis = d3.svg.axis()
//   .orient("bottom")
//   .scale(xScale);
//
// var svg = d3.select("#magic").append("svg")
//     .attr("width", width + margin.left + margin.right)
//     .attr("height", height + margin.top + margin.bottom);
//
// // where x-axis starts
// svg.append("g")
//   .attr("transform", "translate(0," + (height-margin.top) + ")")
//   .call(xAxis);
//
// var lineData = JSON.parse('{{ optim | escapejs }}');
// console.log(lineData)
// var lineFunc = d3.svg.line()
//     .x(function(d) { return margin.left+d.Gen/{{preruns}}*(width-margin.left-margin.right); })
//     .y(function(d) { return (height-margin.top-margin.bottom)/5*4; })
//     .interpolate("linear");
//
// var lineGraph = svg.append("path")
//                           .attr("d", lineFunc(lineData))
//                           .attr("stroke", "steelblue")
//                           .attr("stroke-width", 40)
//                           .attr("fill","none");
//
// var text = svg.append("text")
//   .attr("x",20)
//   .attr("y",50)
//   .attr("dy",".35em")
//   .text("Percentage done...");
</script>
