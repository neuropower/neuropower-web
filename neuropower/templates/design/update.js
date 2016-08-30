<script type='text/javascript' src="https://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.7.0/underscore-min.js"></script>
<script type='text/javascript' src="http://d3js.org/d3.v3.js"></script>
<script type='text/javascript'>

var lineData = JSON.parse('{{ optim | escapejs }}');
var designData = JSON.parse('{{ design | escapejs }}');

// Figure of optimisation
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
});


// figure of best design
var Tps = designData.tps;

console.log(designData);

var names = ['Stimulus_0','Stimulus_1','Stimulus_2','Stimulus_3','Stimulus_4','Stimulus_5','Stimulus_6','Stimulus_7','Stimulus_8','Stimulus_9'];

var outer=[]
var inner=[]

for (var i = 0; i != {{ stim }}+1; ++i){
  innerzero = ['x'].concat(Tps)
  if(i==0){
    outer[i] = innerzero
  } else {
    inner = [names[i]].concat(designData[names[i-1]])
    outer[i] = inner
  }
  // console.log(["Stimulus_".join(i)]);
  // list.push("Stimulus_".join(var).concat(Stim))
};
 console.log(outer);



var chart = c3.generate({
  bindto:'#legend',
  size:{
    height:240,
    width:580
  },
  data :{
    x: 'x',
    columns: outer
  },
  point:{
    show:false
  },
  color:{
    pattern:['#790808','#afd2ec','#afe3ec','#afecd4','#afbcec']
  }
})

</script>
