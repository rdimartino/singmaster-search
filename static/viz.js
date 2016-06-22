function cleanData(d) {
    return {x: d.center, y:(d.centerSearchTime>0?d.centerSearchTime:0.0001), m:d.matchCount};
}

function lineChart() {
	var margin = {
    top: 20,
    right: 20,
    bottom: 30,
    left: 45
  },
  width = 600 - margin.left - margin.right,
  height = 400 - margin.top - margin.bottom,
	x = d3.scale.linear().domain([0, 2000]).range([0, width]),
	y = d3.scale.log().base(10).domain([0.0001, 1]).range([height, 0]),
	xAxis = d3.svg.axis().scale(x).orient("bottom").tickSize(-height),
	yAxis = d3.svg.axis().scale(y).orient("left").ticks(5).tickSize(-width);
   var line = d3.svg.line()
  	.x(function(d) {return x(d.x);})
  	.y(function(d) {return y(d.y);})
  	.interpolate("basis");
  
  var zoom = d3.behavior.zoom()
    .x(x)
    .y(y)
    .scaleExtent([0, 50])
    .on("zoom", zoomed);
  
  //Set-up chart body
  var chart = d3.select("#viz01 > .chart").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
    .call(zoom);
    
  var clipMask = chart.append("defs").append("svg:clipPath")
    .attr("id", "clip1")
    .append("svg:rect")
    .attr("id", "clip-rect1")
    .attr("x", "0")
    .attr("y", "0")
    .attr("width", width)
    .attr("height", height);

  var chartAxes = chart.append("g");

  var chartBody = chart.append("g")
    .attr("clip-path", "url(#clip1)");

  chartAxes.append("rect")
    .attr("width", width)
    .attr("height", height)
    .on("click", unclick);
  
  //X axis
  chartAxes.append("g")
    .attr("class", "x axis")
    .attr("transform", "translate(0," + height + ")")
    .call(xAxis);

  chartAxes.append("text")
    .attr("text-anchor", "middle")
    .attr("transform", "translate("+ (width/2) +","+(height+(3*margin.bottom)/4)+")")
    .text("n-th Center");
	
  //Y axis
  chartAxes.append("g")
    .attr("class", "y axis")
    .call(yAxis)
    .selectAll(".tick text")
      .text(null)
    .filter(powerOfTen)
      .text(10)
    .append("tspan")
      .attr("dy", "-.7em")
      .text(function(d) { return Math.round(Math.log(d) / Math.LN10); });

   chartAxes.append("text")
     .attr("text-anchor", "middle")
     .attr("transform", "translate("+ (-2*margin.left/3) +","+(height/2)+")rotate(-90)")
     .text("Seconds");
     
  //Plots
  var spline = chartBody.append("path");
  
  function zoomed() {
    unclick();
    
    var translation = zoom.translate();
    var scalar = zoom.scale();
		
    zoom.translate([
      translation[0] > 0 ? 0 : translation[0],
      translation[1] < height * (1.0 - scalar) ?
      height * (1.0 - scalar) : translation[1]
    ]);

    chartAxes.select(".x.axis").call(xAxis);
    chartAxes.select(".y.axis").call(yAxis)
    .selectAll(".tick text")
      .text(null)
    .filter(powerOfTen)
      .text(10)
    .append("tspan")
      .attr("dy", "-.7em")
      .text(function(d) { return Math.round(Math.log(d) / Math.LN10); });

    update();
  }

  function update() {
  	var pathSet = function() {
      var subset = viz_data.filter(function(d) { return d.x%10==0});
      subset.unshift(viz_data[0]);
      subset.push(viz_data[viz_data.length-1]);
      return subset;
    };
    
    spline.attr("d", line(pathSet()));

    var circSet = function() {
      var subset=viz_data.filter(function(d) {return (d.x>=x.domain()[0] && d.x<=x.domain()[1] && d.y>=y.domain()[0] && d.y<=y.domain()[1] );});
      if (zoom.scale()<25) {
        subset = subset.filter(function(d) {return d.m!=1;});
      } 
      return subset;
    };
  	
    var scatter=chartBody.selectAll("circle")
      .data(circSet(), function(d) {return d.x;});

    scatter.enter()
      .append("circle")
      .attr("r", 5)
      .attr("fill", function(d) {
        var color;
        if (d.m < 1) {
          color = "red";
        } else if (d.m > 1) {
          color = "green";
        } else {
          color = "blue";
        }
        return color;
      })
      .attr("title", function(d) {return "Center: "+d.x.toString();})
      .attr("data-content",function(d) {return "Time: "+d.y.toFixed(5).toString()+
      "</br>Matches: "+d.m.toString();})
      .attr("data-toggle","popover")
      .on("click", function (d) {
        unclick();
        d3.select(this).attr("class","viz-active");
        $("svg circle.viz-active").popover({
         'trigger':'manual'
         ,'container': 'body'
         ,'placement': 'top'
         ,'white-space': 'nowrap'
         ,'html':'true'
        });
        $("svg circle.viz-active").popover("show");
      });

    scatter.attr("cx", function(d, i) {
        return x(d.x);
      })
      .attr("cy", function(d) {
        return y(d.y);
      });

    scatter.exit().remove();
  }
  //Support functions
  function unclick() {
    $(".viz-active").removeClass("viz-active");
    $(".popover").popover("hide");
  }
   
  return {update: update, unclick: unclick};
}

var viz1 = lineChart();

function barChart() {
	var margin = {
    top: 20,
    right: 20,
    bottom: 30,
    left: 45
  },
  width = 600 - margin.left - margin.right,
  height = 400 - margin.top - margin.bottom,
	x = d3.scale.ordinal().rangeRoundBands([0, width],0.05),
	y = d3.scale.log().base(10).clamp(true).domain([0.1, 1000]).range([height, 0]),
	xAxis = d3.svg.axis().scale(x).orient("bottom").tickSize(-height),
	yAxis = d3.svg.axis().scale(y).orient("left").ticks(5).tickSize(-width).tickFormat(d3.format("n"));
  
  var chart = d3.select("#viz02 > .chart").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    
  var clipMask = chart.append("defs").append("svg:clipPath")
  .attr("id", "clip2")
  .append("svg:rect")
  .attr("id", "clip-rect2")
  .attr("x", "0")
  .attr("y", "0")
  .attr("width", width)
  .attr("height", height);

  var chartAxes = chart.append("g");

  var chartBody = chart.append("g")
    .attr("clip-path", "url(#clip2)");

  chartAxes.append("rect")
    .attr("width", width)
    .attr("height", height);
  
  //X axis
  chartAxes.append("g")
    .attr("class", "x axis")
    .attr("transform", "translate(0," + height + ")")
    .call(xAxis);

  chartAxes.append("text")
    .attr("text-anchor", "middle")
    .attr("transform", "translate("+ (width/2) +","+(height+(3*margin.bottom)/4)+")")
    .text("Matches");
	
  //Y axis
  chartAxes.append("g")
    .attr("class", "y axis")
    .call(yAxis)
    .selectAll(".tick text")
      .text(null)
    .filter(powerOfTen)
      .text(10)
    .append("tspan")
      .attr("dy", "-.7em")
      .text(function(d) { return Math.round(Math.log(d) / Math.LN10); });

  chartAxes.append("text")
     .attr("text-anchor", "middle")
     .attr("transform", "translate("+ (-2*margin.left/3) +","+(height/2)+")rotate(-90)")
     .text("Count");
     
  function update() {
 
  	var barSet = function() {
      var counts = Array(d3.max(viz_data, function(d) {return d.m;})).fill(0);
      for(var i = 0; i< viz_data.length; i++) {
          var num = viz_data[i].m;
          counts[num] = counts[num] ? counts[num]+1 : 1;
      }
      return counts;
    };

  	x.domain(barSet().map(function(d, i) {return i;}));
		y.domain([0.1, d3.max(barSet(), function(d) {return d;})*10]);

    chartAxes.select(".x.axis").call(xAxis);
    chartAxes.select(".y.axis").call(yAxis)
    .selectAll(".tick text")
      .text(null)
    .filter(powerOfTen)
      .text(10)
    .append("tspan")
      .attr("dy", "-.7em")
      .text(function(d) { return Math.round(Math.log(d) / Math.LN10); });

    var barWidth = width/barSet().length;

    var bars=chartBody.selectAll("rect")
      .data(barSet(), function(d, i) {return i;});

    var barsText=chartBody.selectAll("text")
    	.data(barSet(), function(d, i) {return i;});

    bars.enter()
      .append("rect")
      .attr("class", "bar")

    barsText.enter()
    	.append("text")
      .attr("dy","2em")
      .attr("text-anchor","middle");

    bars.attr("x", function(d, i) {return x(i);})
    	.attr("y", function(d) {return y(d);})
      .attr("width", x.rangeBand())
      .attr("height", function(d) {return height-y(d);});

   	barsText.attr("x", function(d, i) {return x(i)+x.rangeBand()/2;})
    	.attr("y", function(d) {return y(d);})
    	.text(function(d) { return d; });

    bars.exit().remove();
    barsText.exit().remove();
  }
  return {update: update};
}

var viz2 = barChart();

function powerOfTen(d) {
  	return d / Math.pow(10, Math.ceil(Math.log(d) / Math.LN10 - 1e-12)) === 1;
	}

function viz_refresh() {
    viz1.update();
    viz2.update();
}

$('a[data-toggle="tab"]').on('shown.bs.tab', viz1.unclick);