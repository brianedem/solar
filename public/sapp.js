let chart;

// determine local timezone offset to UTC time, in milliseconds
const offset = new Date().getTimezoneOffset() * 60*1000;

async function requestData() {
    //console.log("solar_refresh");
    const response = await fetch('solar.data');
    if (response.ok) {
        const data = await response.json();
        const date = new Date(data.date).getTime()-offset;
        const power = data.power;
        const point = [date, power];
        const series = chart.series[0],
            shift = series.data.length > 100;

        chart.series[0].addPoint(point, true, shift);
        setTimeout(requestData, 1000);
        document.getElementById("power").innerHTML = data.power.toFixed(0);
    }
}
