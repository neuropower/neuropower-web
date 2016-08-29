<script type='text/javascript' src="https://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.7.0/underscore-min.js"></script>
<script type='text/javascript' src="http://d3js.org/d3.v3.js"></script>
<script type='text/javascript'>

var lineData = JSON.parse('{{ text | escapejs }}');
var designData = JSON.parse('{{ design | escapejs }}');

var Gen = lineData.Gen;
var FBest = lineData.FBest;
var FeBest = lineData.FeBest;
var FcBest = lineData.FcBest;
var FdBest = lineData.FdBest;
var FfBest = lineData.FfBest;

var nopt = {{ runs }}/50
var list =[];
for (var i = 1; i != nopt; ++i) list.push(i * 50);

var chart = c3.generate({
  bindto:'#magic',
  size:{
    height:240,
    width:480
  },
  data :{
    x: 'x',
    columns: [
      ['x'].concat(Gen),
      ['Overall Fit'].concat(FBest),
      ['Fe'].concat(FeBest),
      ['Ff'].concat(FfBest),
      ['Fd'].concat(FdBest),
      ['Fc'].concat(FcBest)
    ]
  },
  point:{
    show:false
  },
  axis:{
    x:{
      tick:{
        values:list
      },
      max:{{ runs }}
    }
  },
  color:{
    pattern:['#790808','#afd2ec','#afe3ec','#afecd4','#afbcec']
  }

})



</script>
