/*
  Person 3 should replace this with Person 1's deployed Azure Function URL.

  Example:
  https://your-function-app.azurewebsites.net/api/process-diet-data
*/
const API_ENDPOINT =
  "https://YOUR-FUNCTION-APP.azurewebsites.net/api/process-diet-data";

let allResults = {};
let filteredResults = {};

let barChart;
let lineChart;
let pieChart;

const sampleData = {
  paleo: {
    average_protein_g: 88.67,
    average_carbs_g: 129.55,
    average_fat_g: 135.67,
    recipe_count: 1274
  },
  vegan: {
    average_protein_g: 56.16,
    average_carbs_g: 254.0,
    average_fat_g: 103.3,
    recipe_count: 1522
  },
  keto: {
    average_protein_g: 101.27,
    average_carbs_g: 57.97,
    average_fat_g: 153.12,
    recipe_count: 1512
  },
  mediterranean: {
    average_protein_g: 101.11,
    average_carbs_g: 152.91,
    average_fat_g: 101.42,
    recipe_count: 1753
  },
  dash: {
    average_protein_g: 69.28,
    average_carbs_g: 160.54,
    average_fat_g: 101.15,
    recipe_count: 1745
  }
};

const statusMessage = document.getElementById("statusMessage");
const resultsTable = document.getElementById("resultsTable");
const searchInput = document.getElementById("searchInput");
const dietFilter = document.getElementById("dietFilter");

function setStatus(message, type = "") {
  statusMessage.textContent = message;
  statusMessage.className = `status-message ${type}`;
}

function formatDietName(diet) {
  return diet.charAt(0).toUpperCase() + diet.slice(1);
}

function normalizeApiData(data) {
  const source = data.results || data.data || data;

  if (!source || typeof source !== "object" || Array.isArray(source)) {
    throw new Error("The API returned an invalid response.");
  }

  return source;
}

async function loadDashboardData() {
  const startTime = performance.now();

  setStatus("Loading data from the Azure Function...");

  try {
    let data;

    /*
      This fallback allows Person 2 to develop the UI before the Azure
      Function is deployed. Once Person 1 provides the endpoint, the API
      response will be used automatically.
    */
    if (API_ENDPOINT.includes("YOUR-FUNCTION-APP")) {
      await new Promise((resolve) => setTimeout(resolve, 500));
      data = sampleData;
      setStatus("Displaying sample data. Azure endpoint not configured.");
    } else {
      const response = await fetch(API_ENDPOINT);

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      data = normalizeApiData(await response.json());
      setStatus("Data loaded successfully from Azure.", "success");
    }

    allResults = data;
    filteredResults = { ...allResults };

    const executionMilliseconds = Math.round(
      performance.now() - startTime
    );

    document.getElementById("executionTime").textContent =
      `${executionMilliseconds} ms`;

    populateDietFilter();
    renderDashboard();
  } catch (error) {
    console.error(error);
    setStatus(`Unable to load dashboard data: ${error.message}`, "error");
  }
}

function populateDietFilter() {
  const diets = Object.keys(allResults).sort();

  dietFilter.innerHTML = `<option value="all">All Diet Types</option>`;

  diets.forEach((diet) => {
    const option = document.createElement("option");
    option.value = diet;
    option.textContent = formatDietName(diet);
    dietFilter.appendChild(option);
  });
}

function applyFilters() {
  const searchTerm = searchInput.value.trim().toLowerCase();
  const selectedDiet = dietFilter.value;

  filteredResults = Object.fromEntries(
    Object.entries(allResults).filter(([diet]) => {
      const matchesSearch = diet.toLowerCase().includes(searchTerm);
      const matchesDiet =
        selectedDiet === "all" || selectedDiet === diet;

      return matchesSearch && matchesDiet;
    })
  );

  renderDashboard();
}

function clearFilters() {
  searchInput.value = "";
  dietFilter.value = "all";
  filteredResults = { ...allResults };
  renderDashboard();
}

function renderDashboard() {
  const diets = Object.keys(filteredResults);
  const values = Object.values(filteredResults);

  updateMetadata(values);
  updateTable(diets, values);
  updateCharts(diets, values);
}

function updateMetadata(values) {
  const totalRecipes = values.reduce(
    (total, item) => total + Number(item.recipe_count || 0),
    0
  );

  document.getElementById("dietCount").textContent = values.length;
  document.getElementById("recipeCount").textContent =
    totalRecipes.toLocaleString();
}

function updateTable(diets, values) {
  if (values.length === 0) {
    resultsTable.innerHTML = `
      <tr>
        <td colspan="5">No matching diet types found.</td>
      </tr>
    `;
    return;
  }

  resultsTable.innerHTML = diets
    .map((diet, index) => {
      const item = values[index];

      return `
        <tr>
          <td>${formatDietName(diet)}</td>
          <td>${Number(item.average_protein_g).toFixed(2)}</td>
          <td>${Number(item.average_carbs_g).toFixed(2)}</td>
          <td>${Number(item.average_fat_g).toFixed(2)}</td>
          <td>${Number(item.recipe_count).toLocaleString()}</td>
        </tr>
      `;
    })
    .join("");
}

function destroyCharts() {
  [barChart, lineChart, pieChart].forEach((chart) => {
    if (chart) {
      chart.destroy();
    }
  });
}

function updateCharts(diets, values) {
  destroyCharts();

  const labels = diets.map(formatDietName);

  const chartColors = [
    "#64a0f4",
    "#13b981",
    "#c77df1",
    "#ff9f43",
    "#ff6b81"
  ];

  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: "#eeeeee"
        }
      }
    },
    scales: {
      x: {
        ticks: {
          color: "#b8c2d0"
        },
        grid: {
          color: "#292d35"
        }
      },
      y: {
        ticks: {
          color: "#b8c2d0"
        },
        grid: {
          color: "#292d35"
        }
      }
    }
  };

  barChart = new Chart(document.getElementById("barChart"), {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Protein (g)",
          data: values.map((item) => item.average_protein_g),
          backgroundColor: "#64a0f4"
        },
        {
          label: "Carbs (g)",
          data: values.map((item) => item.average_carbs_g),
          backgroundColor: "#13b981"
        },
        {
          label: "Fat (g)",
          data: values.map((item) => item.average_fat_g),
          backgroundColor: "#c77df1"
        }
      ]
    },
    options: commonOptions
  });

  lineChart = new Chart(document.getElementById("lineChart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Recipe Count",
          data: values.map((item) => item.recipe_count),
          borderColor: "#4dd0e1",
          backgroundColor: "rgba(77, 208, 225, 0.2)",
          pointBackgroundColor: "#4dd0e1",
          pointRadius: 5,
          fill: true,
          tension: 0.35
        }
      ]
    },
    options: commonOptions
  });

  pieChart = new Chart(document.getElementById("pieChart"), {
    type: "pie",
    data: {
      labels,
      datasets: [
        {
          label: "Recipe Distribution",
          data: values.map((item) => item.recipe_count),
          backgroundColor: chartColors
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: "#eeeeee"
          }
        }
      }
    }
  });
}

document
  .getElementById("refreshButton")
  .addEventListener("click", loadDashboardData);

document
  .getElementById("applyFilterButton")
  .addEventListener("click", applyFilters);

document
  .getElementById("clearFilterButton")
  .addEventListener("click", clearFilters);

searchInput.addEventListener("input", applyFilters);
dietFilter.addEventListener("change", applyFilters);

loadDashboardData();