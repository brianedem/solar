let chart;

async function requestData() {
    console.log("solar_refresh")
    const response = await fetch('solar.data');
    if (response.ok) {
	const data = await response.json();
	const date = data.date
	const power = data.power
	const point = [new Date(date).getTime(), power]
	const series = chart.series[0],
	    shift = series.data.length > 20;

	chart.series[0].addPoint(point, true, shift);
	setTimeout(requestData, 5000);
	document.getElementById("power").innerHTML = data.power.toFixed(0)
    }
}
