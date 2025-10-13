// Example: Fraud status pie chart
document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById("fraudChart").getContext("2d");
    const fraudCount = document.querySelectorAll("td:contains('FRAUD')").length;
    const normalCount = document.querySelectorAll("td:contains('NORMAL')").length;

    new Chart(ctx, {
        type: "pie",
        data: {
            labels: ["Fraud", "Normal"],
            datasets: [{
                data: [fraudCount, normalCount],
                backgroundColor: ["#d9534f", "#5cb85c"]
            }]
        }
    });
});