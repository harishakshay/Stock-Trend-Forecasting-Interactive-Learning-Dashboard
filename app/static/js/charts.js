let mainChartInstance = null;
let predictChartInstance = null;

(function initMainDashboardChart() {
  try {

    if (typeof dates === 'undefined' || typeof prices === 'undefined') return;

    const canvas = document.getElementById('stockChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (mainChartInstance) mainChartInstance.destroy();

    mainChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: dates,
        datasets: [
          {
            label: 'Close Price',
            data: prices,
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59,130,246,0.2)',
            fill: true,
            tension: 0.25,
            pointBackgroundColor: '#3b82f6',
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          title: {
            display: true,
          },
        },
        scales: {
          x: { title: { display: true, text: 'Date' } },
          y: { title: { display: true, text: 'Close Price (₹)' } },
        },
      },
    });
  } catch (err) {
    console.error('Error initializing main dashboard chart:', err);
  }
})();

// 2. Predict Form Handler

const form = document.getElementById('predictForm');
if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    try {
      const res = await fetch('/predict-next', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      const result = await res.json();
      const reportDiv = document.getElementById('predictionReport');
      const reportText = document.getElementById('reportText');

      if (!reportDiv || !reportText) return;

      // Handle API errors
      if (result.error) {
        reportDiv.classList.remove('hidden');
        reportText.innerHTML = `
          <span class="text-red-600 font-semibold">Error:</span> ${result.error}
        `;
        return;
      }

      // Display prediction report
      reportDiv.classList.remove('hidden');
      reportText.innerHTML = `
        Predicted Next Close Price: <strong>₹${result.prediction}</strong><br>
        Personalized Suggestion: <strong>${result.suggestion}</strong><br>
        Last 30 Days Trend: <strong>${result.trend}</strong><br>
        Volatility: <strong>${result.volatility}%</strong>
      `;

      const canvas = document.getElementById('priceChart');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');

      const last30 = Array.isArray(result.last_30_days)
        ? result.last_30_days
        : [];

      const labels = last30.map((_, i) => `Day ${i + 1}`);
      labels.push('Prediction');

      const prices = [...last30, result.prediction];

      if (predictChartInstance) predictChartInstance.destroy();

      predictChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Close Price',
              data: prices,
              borderColor: '#28a745',
              backgroundColor: 'rgba(40,167,69,0.2)',
              fill: true,
              tension: 0.2,
              pointBackgroundColor: [
                ...Array(last30.length).fill('#3b82f6'),
                '#f87171', 
              ],
            },
          ],
        },
        options: {
          responsive: true,
          plugins: {
            legend: { display: false },
            title: {
              display: true,
              text: 'Last 30 Days + Prediction',
              font: { size: 14, weight: 'bold' },
            },
          },
          scales: {
            x: { title: { display: true, text: 'Days' } },
            y: { title: { display: true, text: 'Close Price (₹)' } },
          },
        },
      });
    } catch (err) {
      console.error('Prediction error:', err);
      const reportDiv = document.getElementById('predictionReport');
      const reportText = document.getElementById('reportText');
      if (reportDiv && reportText) {
        reportDiv.classList.remove('hidden');
        reportText.innerHTML = `
          <span class="text-red-600 font-semibold">Error:</span> Unable to fetch prediction.
        `;
      }
    }
  });
}

if (window.Chart) {
  console.log('Chart.js version:', Chart.version);
}
