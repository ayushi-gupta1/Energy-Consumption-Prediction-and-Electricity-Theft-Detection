(function () {
  const d = window.dashboardData || {};

  const body = document.body;
  const themeToggle = document.getElementById("themeToggle");

  function applyTheme(theme) {
    if (theme === "light") {
      body.classList.remove("theme-dark");
      if (themeToggle) themeToggle.innerHTML = '<i class="bi bi-brightness-high-fill me-1"></i>Light';
    } else {
      body.classList.add("theme-dark");
      if (themeToggle) themeToggle.innerHTML = '<i class="bi bi-moon-stars-fill me-1"></i>Dark';
    }
    localStorage.setItem("gridguard-theme", theme);
  }

  const savedTheme = localStorage.getItem("gridguard-theme") || "dark";
  applyTheme(savedTheme);
  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      const next = body.classList.contains("theme-dark") ? "light" : "dark";
      applyTheme(next);
      window.location.reload();
    });
  }

  const isDark = body.classList.contains("theme-dark");
  const palette = {
    text: isDark ? "#dce8ff" : "#1a2f47",
    grid: isDark ? "rgba(160,182,224,0.13)" : "rgba(45,86,130,0.12)",
    tooltipBg: isDark ? "#0d162a" : "#0f2744",
    panel: isDark ? "rgba(15,24,43,0.92)" : "#ffffff"
  };

  const common = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: palette.text,
          font: { weight: "700" }
        }
      },
      tooltip: {
        backgroundColor: palette.tooltipBg,
        titleColor: "#ffffff",
        bodyColor: "#ffffff",
        padding: 10
      }
    },
    scales: {
      x: { ticks: { color: palette.text }, grid: { color: palette.grid } },
      y: { ticks: { color: palette.text }, grid: { color: palette.grid } }
    }
  };

  function theftScatterPoints(labels, actual, theftFlags) {
    const points = [];
    for (let i = 0; i < labels.length; i += 1) {
      if (Number(theftFlags[i]) === 1) points.push({ x: labels[i], y: actual[i] });
    }
    return points;
  }

  const mainCtx = document.getElementById("mainChart");
  let mainChart = null;
  if (mainCtx) {
    const theftPts = theftScatterPoints(d.main_labels, d.actual_vals, d.theft_vals);
    mainChart = new Chart(mainCtx, {
      type: "line",
      data: {
        labels: d.main_labels,
        datasets: [
          {
            label: "Actual Consumption",
            data: d.actual_vals,
            borderColor: "#f08c00",
            backgroundColor: "rgba(240,140,0,0.2)",
            borderWidth: 3,
            pointRadius: function (ctx) {
              const idx = ctx.dataIndex;
              return idx === ctx.dataset.data.length - 1 ? 4.5 : 0;
            },
            pointBackgroundColor: "#ffd166",
            tension: 0.3,
            fill: true
          },
          {
            label: "Predicted Baseline",
            data: d.pred_vals,
            borderColor: "#4dabf7",
            borderDash: [6, 4],
            borderWidth: 2.5,
            pointRadius: 0,
            tension: 0.3
          },
          {
            type: "scatter",
            label: "Theft Flag",
            data: theftPts,
            pointBackgroundColor: "#ff4d4f",
            pointBorderColor: "#ffffff",
            pointBorderWidth: 1.8,
            pointRadius: 5.2
          }
        ]
      },
      options: {
        ...common,
        plugins: {
          ...common.plugins,
          title: {
            display: true,
            text: "Live Grid Consumption vs Predicted Baseline",
            color: palette.text,
            font: { size: 18, weight: "800" },
            padding: { top: 8, bottom: 12 }
          }
        }
      }
    });
  }

  function setLiveStatus(text) {
    const node = document.getElementById("liveStatus");
    if (node) node.textContent = text;
  }

  function startLiveMode() {
    if (!mainChart || d.mode !== "live") return;

    setLiveStatus("Connecting...");

    // Start from an empty window and fill as live points arrive.
    mainChart.data.labels = [];
    mainChart.data.datasets[0].data = [];
    mainChart.data.datasets[1].data = [];
    mainChart.data.datasets[2].data = [];
    mainChart.update();

    const wsQuery = d.live_query || {};
    const maxWindow = 60;
    let pointsReceived = 0;

    const socket = io({
      transports: ["websocket"],
      query: {
        meter: wsQuery.meter || "",
        start: wsQuery.start || "",
        end: wsQuery.end || ""
      }
    });

    socket.on("connect", function () {
      setLiveStatus("Connected");
    });

    socket.on("disconnect", function () {
      setLiveStatus("Disconnected");
    });

    socket.on("connect_error", function () {
      setLiveStatus("Connect failed");
    });

    socket.on("live_error", function () {
      setLiveStatus("No data");
    });

    socket.on("live_point", function (payload) {
      const labels = mainChart.data.labels;
      const actual = mainChart.data.datasets[0].data;
      const predicted = mainChart.data.datasets[1].data;
      const theftFlags = [];

      labels.push(payload.datetime);
      actual.push(Number(payload.actual));
      predicted.push(Number(payload.predicted));

      // Keep chart smooth and bounded in size for long-running sessions.
      while (labels.length > maxWindow) {
        labels.shift();
        actual.shift();
        predicted.shift();
      }

      for (let i = 0; i < labels.length; i += 1) {
        theftFlags.push(0);
      }
      theftFlags[theftFlags.length - 1] = Number(payload.theft) === 1 ? 1 : 0;

      mainChart.data.datasets[2].data = theftScatterPoints(labels, actual, theftFlags);
      mainChart.update("none");

      pointsReceived += 1;
      setLiveStatus("Connected " + pointsReceived + " pts");
    });
  }

  const gaugeCtx = document.getElementById("riskGaugeChart");
  if (gaugeCtx) {
    const score = Number(d.risk_score || 0);
    new Chart(gaugeCtx, {
      type: "doughnut",
      data: {
        labels: ["Risk", "Safe"],
        datasets: [{
          data: [score, Math.max(0, 100 - score)],
          backgroundColor: ["#ff4d4f", "#2f9e44"],
          borderWidth: 0,
          cutout: "72%"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        rotation: -90,
        circumference: 180,
        plugins: {
          legend: { display: false },
          tooltip: { enabled: false },
          title: {
            display: true,
            text: "Risk Score: " + score.toFixed(2) + "%",
            color: palette.text,
            font: { size: 18, weight: "800" }
          }
        }
      }
    });
  }

  const dailyCtx = document.getElementById("dailyTheftChart");
  if (dailyCtx) {
    new Chart(dailyCtx, {
      type: "bar",
      data: { labels: d.daily_labels, datasets: [{ label: "Theft Cases", data: d.daily_values, backgroundColor: "#ff4d4f" }] },
      options: common
    });
  }

  const hourlyCtx = document.getElementById("hourlyPatternChart");
  if (hourlyCtx) {
    new Chart(hourlyCtx, {
      type: "line",
      data: {
        labels: d.hourly_labels,
        datasets: [
          { label: "Actual Avg", data: d.hourly_actual, borderColor: "#f08c00", borderWidth: 3, tension: 0.3 },
          { label: "Predicted Avg", data: d.hourly_pred, borderColor: "#4dabf7", borderWidth: 3, tension: 0.3 }
        ]
      },
      options: common
    });
  }

  const scatterCtx = document.getElementById("scatterChart");
  if (scatterCtx) {
    const normal = [];
    const theft = [];
    (d.scatter_points || []).forEach((p) => {
      const point = { x: p.predicted, y: p.actual };
      if (Number(p.theft) === 1) theft.push(point);
      else normal.push(point);
    });

    new Chart(scatterCtx, {
      type: "scatter",
      data: {
        datasets: [
          { label: "Normal", data: normal, backgroundColor: "rgba(77,171,247,0.58)" },
          { label: "Theft Flag", data: theft, backgroundColor: "rgba(255,77,79,0.85)" }
        ]
      },
      options: {
        ...common,
        scales: {
          x: { ...common.scales.x, title: { display: true, text: "Predicted", color: palette.text, font: { weight: "700" } } },
          y: { ...common.scales.y, title: { display: true, text: "Actual", color: palette.text, font: { weight: "700" } } }
        }
      }
    });
  }

  const errCtx = document.getElementById("errorDistChart");
  if (errCtx) {
    new Chart(errCtx, {
      type: "bar",
      data: { labels: d.hist_labels, datasets: [{ label: "Frequency", data: d.hist_values, backgroundColor: "#12b886" }] },
      options: common
    });
  }

  const fleetCtx = document.getElementById("fleetChart");
  if (fleetCtx) {
    new Chart(fleetCtx, {
      type: "bar",
      data: { labels: d.fleet_labels, datasets: [{ label: "Theft Rate (%)", data: d.fleet_values, backgroundColor: "#4dabf7" }] },
      options: common
    });
  }

  startLiveMode();
})();
