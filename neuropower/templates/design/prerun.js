<script type='text/javascript' src="https://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.7.0/underscore-min.js"></script>
<script type='text/javascript' src="http://d3js.org/d3.v3.js"></script>
<script type="text/javascript">

var lineData = JSON.parse('{{ optim | escapejs }}');
var percentage = Object.keys(lineData.Gen).length / {{preruns}};
console.log(percentage);

var chart = c3.generate({
  bindto:'#prerun',
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


</script>
