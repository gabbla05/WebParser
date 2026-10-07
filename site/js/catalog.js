/**
 * Obsługa katalogu produktów:
 * - Dynamiczne pobieranie danych przez fetch z pliku data/products.json
 * - Doładowywanie porcjami po kliknięciu "Wczytaj więcej"
 * - Sztuczne opóźnienie 400-1200 ms (wymóg 300-2000 ms)
 * - Podział na 2 struktury: karty (<article>) oraz tabela (<table>)
 * - Atrybuty semantyczne oraz data-* (data-id, data-rating, data-stock)
 */

document.addEventListener("DOMContentLoaded", () => {
  const BATCH_SIZE = 35;
  let allProducts = [];
  let currentIndex = 0;
  let isLoading = false;

  const gridContainer = document.getElementById("products-grid");
  const tableSection = document.getElementById("table-section");
  const tableBody = document.getElementById("products-table-body");
  const btnLoadMore = document.getElementById("btn-load-more");
  const btnSpinner = document.getElementById("btn-spinner");
  const btnText = btnLoadMore.querySelector(".btn-text");
  const endMessage = document.getElementById("end-message");
  const loadedCountEl = document.getElementById("loaded-count");
  const totalCountEl = document.getElementById("total-db-count");

  // Pobranie bazy produktów przez fetch
  fetch("data/products.json")
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      allProducts = data;
      totalCountEl.textContent = allProducts.length;
      // Załaduj pierwszą porcję po starcie
      loadNextBatch();
    })
    .catch((err) => {
      console.error("Błąd ładowania produktów:", err);
      btnText.textContent = "Błąd wczytywania danych";
    });

  btnLoadMore.addEventListener("click", () => {
    if (!isLoading && currentIndex < allProducts.length) {
      loadNextBatch();
    }
  });

  function getBadgeClass(dostepnosc) {
    if (dostepnosc.includes("magazynie")) return "badge-in-stock";
    if (dostepnosc.includes("sztuki")) return "badge-last-items";
    if (dostepnosc.includes("Brak")) return "badge-out-of-stock";
    return "badge-shipping";
  }

  function renderCard(product) {
    const card = document.createElement("article");
    card.className = "product-card produkt";
    card.setAttribute("data-id", product.id);
    card.setAttribute("data-rating", product.ocena);
    card.setAttribute("data-in-stock", product.dostepnosc.includes("magazynie") || product.dostepnosc.includes("sztuki"));
    card.setAttribute("data-category", product.kategoria);
    
    // Utrudnienie 4.0: Cechy dostępne WYŁĄCZNIE w data-* (brak w widocznej treści)
    card.setAttribute("data-vat", product.stawka_vat);
    card.setAttribute("data-energy-class", product.klasa_energetyczna);
    card.setAttribute("data-stock-count", product.stan_magazynowy_sztuk);

    const badgeClass = getBadgeClass(product.dostepnosc);
    const reviewsHtml = product.liczba_opinii !== null 
      ? `(${product.liczba_opinii} opinii)` 
      : `<span class="brak-danych">brak opinii</span>`;

    const warrantyHtml = product.gwarancja_miesiace !== null
      ? `${product.gwarancja_miesiace} mies.`
      : `<span class="brak-danych">brak informacji</span>`;

    card.innerHTML = `
      <div>
        <div class="badge-row">
          <span class="badge badge-category kategoria">${product.kategoria}</span>
          <span class="badge ${badgeClass} dostepnosc">${product.dostepnosc}</span>
        </div>
        <h3 class="product-title nazwa">
          <a href="${product.link_szczegoly}">${product.nazwa}</a>
        </h3>
        <div class="product-meta">
          <span class="producent">Producent: <strong>${product.producent}</strong></span>
          <span class="ocena">Ocena: <strong>⭐ ${product.ocena}</strong> ${reviewsHtml}</span>
          <span class="data-dodania">Dodano: ${product.data_dodania}</span>
          <span class="gwarancja">Gwarancja: ${warrantyHtml}</span>
        </div>
      </div>
      <div class="product-footer">
        <div class="product-price cena">${product.cena_tekst}</div>
        <a href="${product.link_szczegoly}" class="btn-details odnosnik">Szczegóły</a>
      </div>
    `;
    return card;
  }

  function renderTableRow(product) {
    const tr = document.createElement("tr");
    tr.className = "product-row produkt";
    tr.setAttribute("data-id", product.id);
    tr.setAttribute("data-rating", product.ocena);
    tr.setAttribute("data-in-stock", product.dostepnosc.includes("magazynie") || product.dostepnosc.includes("sztuki"));
    
    // Utrudnienie 4.0: Cechy dostępne WYŁĄCZNIE w data-*
    tr.setAttribute("data-vat", product.stawka_vat);
    tr.setAttribute("data-energy-class", product.klasa_energetyczna);
    tr.setAttribute("data-stock-count", product.stan_magazynowy_sztuk);

    const badgeClass = getBadgeClass(product.dostepnosc);
    const reviewsText = product.liczba_opinii !== null ? `(${product.liczba_opinii})` : "brak";
    const warrantyText = product.gwarancja_miesiace !== null ? `${product.gwarancja_miesiace} mies.` : "—";

    tr.innerHTML = `
      <td class="nazwa">
        <a href="${product.link_szczegoly}" style="color: var(--text-main); font-weight: 600; text-decoration: none;">
          ${product.nazwa}
        </a>
      </td>
      <td class="kategoria">${product.kategoria}</td>
      <td class="producent">${product.producent}</td>
      <td class="cena" style="font-weight: 700; color: var(--primary-color);">${product.cena_tekst}</td>
      <td class="dostepnosc"><span class="badge ${badgeClass}">${product.dostepnosc}</span></td>
      <td class="ocena">⭐ ${product.ocena} <span style="font-size: 0.8rem; color: var(--text-muted);">${reviewsText}</span></td>
      <td class="data-dodania">${product.data_dodania}</td>
      <td class="gwarancja">${warrantyText}</td>
      <td><a href="${product.link_szczegoly}" class="btn-details odnosnik" style="padding: 0.35rem 0.6rem; font-size: 0.75rem;">Zobacz</a></td>
    `;
    return tr;
  }

  function loadNextBatch() {
    isLoading = true;
    btnLoadMore.disabled = true;
    btnSpinner.style.display = "inline-block";
    btnText.textContent = "Ładowanie danych...";

    // Sztuczne losowe opóźnienie w przedziale 400 - 1100 ms (wymóg: 300-2000 ms)
    const delay = Math.floor(Math.random() * (1100 - 400 + 1)) + 400;

    setTimeout(() => {
      const nextBatch = allProducts.slice(currentIndex, currentIndex + BATCH_SIZE);

      if (nextBatch.length > 0) {
        // Wymóg: 2 struktury (karty oraz tabela)
        // 70% porcji trafia do kart, 30% do tabeli
        tableSection.style.display = "block";

        const splitIndex = Math.ceil(nextBatch.length * 0.7);
        const cardItems = nextBatch.slice(0, splitIndex);
        const tableItems = nextBatch.slice(splitIndex);

        cardItems.forEach((p) => {
          gridContainer.appendChild(renderCard(p));
        });

        tableItems.forEach((p) => {
          tableBody.appendChild(renderTableRow(p));
        });

        currentIndex += nextBatch.length;
        loadedCountEl.textContent = currentIndex;
      }

      isLoading = false;
      btnSpinner.style.display = "none";

      if (currentIndex >= allProducts.length) {
        btnLoadMore.style.display = "none";
        endMessage.style.display = "block";
      } else {
        btnLoadMore.disabled = false;
        btnText.textContent = "Wczytaj więcej produktów";
      }
    }, delay);
  }
});
