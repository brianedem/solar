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
        const series = chart.series[0],
            shift = series.data.length > 200;

        const inverter = data.power;
        let point = [date, inverter];
        chart.series[0].addPoint(point, true, shift);

        const solar = data.bus_v * data.solar_i;
        point = [date, solar];
        chart.series[1].addPoint(point, true, shift);

        const charge = data.bus_v * data.charge_i;
        point = [date, charge];
        chart.series[2].addPoint(point, true, shift);

        const discharge = data.bus_v * data.discharge_i;
        point = [date, discharge];
        chart.series[3].addPoint(point, true, shift);

        setTimeout(requestData, 1000);
        document.getElementById("power").innerHTML = data.power.toFixed(0);
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
        //document.getElementById("power").innerHTML = data.power.toFixed(0);
    }
}
