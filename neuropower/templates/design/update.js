<script type="text/javascript">
// var figSel = d3.select("#magic");
//
// var svgSel = figSel.append("svg")
//   .attr("width",50)
//   .attr("height",50);
//
// var circleSel = svgSel.append("circle")
//   .attr("cx",25)
//   .attr("cy",25)
//   .attr("r",25)
//   .style("fill","purple");
//
var figSel = d3.select("#magic");

var circleRadii = [40,20,10];

var svgSel = figSel.append("svg")
  .attr("width",600)
  .attr("height",100);

var circles = svgSel.selectAll("circle")
  .data(circleRadii)
  .enter()
  .append("circle");

var circleAttributes = circles
  .attr("cx",50)
  .attr("cy",50)
  .attr("r", function(d){return d;})
  //  .style("fill","red");
    .style("fill",function(d){
      var returnColor;
        if (d == 40) {returnColor="green";
        } else if (d==20) {returnColor="purple";
        } else if (d==10) {returnColor="red"; }
    return returnColor;
    });

</script>
