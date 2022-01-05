let chart;
let chart2;

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

        const power2 = data.bat;
        const point2 = [date, power2];
        chart.series[1].addPoint(point2, true, shift);
        
        setTimeout(requestData, 1000);
        //document.getElementById("power").innerHTML = data.power.toFixed(0);
    }
}

async function requestData2() {
    //console.log("solar_refresh");
    const response = await fetch('solar.data2');
    if (response.ok) {
        const data = await response.json();
        const power = data.power
        const date = data.start
        console.log(date)
        const date2 = new Date(date)
        console.log(date2)
        chart2.series.pointStart = date2
        chart2.series[0].setData(data.min);
        console.log(data.min[100])
        //chart2.series[1] = [[0,0],[0,0];
        //chart2.series[2] = [[0,0],[0,0];
        setTimeout(requestData2, 1000);
        document.getElementById("power").innerHTML = data.power.toFixed(0);
    }
}
