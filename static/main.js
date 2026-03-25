window.onload = function () {
  //Reference the DropDownList.
  var year = document.getElementById("year-dropdown");

  //Loop and add the Year values to DropDownList.
  for (var i = 2000; i <= 2050; i++) {
    var option = document.createElement("OPTION");
    option.innerHTML = i;
    option.value = i;
    year.appendChild(option);
  }
};

document.addEventListener("DOMContentLoaded", () => {
  fetch("/crime-news")
    .then((response) => response.json())
    .then((data) => {
      const newsContainer = document.getElementById("crime-news");
      newsContainer.innerHTML = "";

      if (data.error) {
        newsContainer.innerHTML = `<p>Error: ${data.error}</p>`;
        return;
      }

      if (data.length === 0) {
        newsContainer.innerHTML = "<p>No recent crime news available.</p>";
        return;
      }

      data.forEach((article) => {
        const item = document.createElement("div");
        item.classList.add("news-item");
        item.innerHTML = `
                    <h3><a href="${article.url}" target="_blank">${
          article.title
        }</a></h3>
                    <p>${article.description || "No description available."}</p>
                `;
        newsContainer.appendChild(item);
      });
    })
    .catch((error) => {
      document.getElementById(
        "crime-news"
      ).innerHTML = `<p>Failed to load news: ${error}</p>`;
    });
});
