/**
 * Obsługa podstrony szczegółów produktu:
 * - Odczyt parametru 'id' z URL
 * - Dynamiczny fetch z data/products.json
 * - Utrudnienie 5.0 #1: Atrybuty specyfikacji widoczne dopiero po interakcji (<details>)
 * - Utrudnienie 5.0 #2: Losowa kolejność renderowania atrybutów w specyfikacji
 */

document.addEventListener("DOMContentLoaded", () => {
  const urlParams = new URLSearchParams(window.location.search);
  const productId = parseInt(urlParams.get("id"), 10);

  const loadingEl = document.getElementById("loading-state");
  const errorEl = document.getElementById("error-state");
  const containerEl = document.getElementById("product-details-container");

  if (isNaN(productId)) {
    showError();
    return;
  }

  // Symulacja opóźnienia sieciowego (300-800ms)
  const delay = Math.floor(Math.random() * (800 - 300 + 1)) + 300;

  setTimeout(() => {
    fetch("data/products.json")
      .then((res) => {
        if (!res.ok) throw new Error("Błąd sieci");
        return res.json();
      })
      .then((products) => {
        const product = products.find((p) => p.id === productId);
        if (!product) {
          showError();
          return;
        }
        renderProductDetails(product);
      })
      .catch((err) => {
        console.error("Błąd ładowania szczegółów:", err);
        showError();
      });
  }, delay);

  function showError() {
    loadingEl.style.display = "none";
    errorEl.style.display = "block";
  }

  // Funkcja tasująca tablicę (Fisher-Yates shuffle) - wymóg 5.0: losowa kolejność cech
  function shuffle(array) {
    const copy = [...array];
    for (let i = copy.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
  }

  function renderProductDetails(product) {
    loadingEl.style.display = "none";
    containerEl.style.display = "block";

    // Lista cech szczegółowych (łącznie wraz z ogólnymi daje 24 atrybuty)
    const rawSpecs = [
      { key: "procesor", label: "Procesor", val: product.procesor },
      { key: "ram_gb", label: "Pamięć RAM", val: `${product.ram_gb} GB` },
      { key: "dysk_ssd_gb", label: "Dysk SSD", val: `${product.dysk_ssd_gb} GB` },
      { key: "karta_graficzna", label: "Karta graficzna", val: product.karta_graficzna },
      { key: "ekran_cale", label: "Przekątna ekranu", val: `${product.ekran_cale}"` },
      { key: "rozdzielczosc", label: "Rozdzielczość", val: product.rozdzielczosc },
      { key: "system_operacyjny", label: "System operacyjny", val: product.system_operacyjny },
      { key: "waga_kg", label: "Waga urządzenia", val: `${product.waga_kg} kg` },
      { key: "kolor", label: "Kolor obudowy", val: product.kolor },
      { key: "kod_producenta", label: "Kod producenta", val: product.kod_producenta || "Brak danych" },
      { key: "porty_usb", label: "Liczba portów USB", val: product.porty_usb },
      { key: "pojemnosc_baterii_wh", label: "Pojemność baterii", val: `${product.pojemnosc_baterii_wh} Wh` }
    ];

    // Tasujemy kolejność specyfikacji technicznej
    const shuffledSpecs = shuffle(rawSpecs);

    const specsItemsHtml = shuffledSpecs
      .map(
        (s) => `
        <div class="spec-item" data-spec-key="${s.key}">
          <span class="spec-label">${s.label}</span>
          <span class="spec-value ${s.key}">${s.val}</span>
        </div>
      `
      )
      .join("");

    const reviewsText = product.liczba_opinii !== null ? `${product.liczba_opinii} opinii klientów` : "Brak zarejestrowanych opinii";
    const warrantyText = product.gwarancja_miesiace !== null ? `${product.gwarancja_miesiace} miesięcy gwarancji producenta` : "Brak danych gwarancyjnych";

    containerEl.setAttribute("data-id", product.id);
    containerEl.setAttribute("data-currency", product.waluta);
    containerEl.setAttribute("data-base-price", product.cena_bazowa_pln);

    containerEl.innerHTML = `
      <div class="product-detail-header">
        <div class="badge-row">
          <span class="badge badge-category kategoria">${product.kategoria}</span>
          <span class="badge badge-in-stock dostepnosc">${product.dostepnosc}</span>
        </div>
        <h1 class="nazwa" style="font-size: 1.85rem; margin: 0.5rem 0;">${product.nazwa}</h1>
        <div class="product-meta">
          <span class="producent">Producent: <strong>${product.producent}</strong></span>
          <span class="ocena">Ocena społeczności: <strong>⭐ ${product.ocena} / 5.0</strong> (${reviewsText})</span>
          <span class="data-dodania">Data wprowadzenia do oferty: ${product.data_dodania}</span>
          <span class="gwarancja">Okres gwarancyjny: ${warrantyText}</span>
        </div>
        <div style="margin-top: 1.25rem;">
          <span style="font-size: 0.9rem; color: var(--text-muted);">Cena brutto:</span>
          <div class="product-price cena" style="font-size: 2rem;">${product.cena_tekst}</div>
        </div>
      </div>

      <!-- Interaktywny element: wymóg 5.0 (atrybut widoczny dopiero po interakcji/kliknięciu) -->
      <details id="tech-specs-toggle" class="detail-specs-details">
        <summary id="specs-summary-btn">
          🛠️ Pełna specyfikacja techniczna (kliknij, aby rozwinąć)
        </summary>
        <div class="spec-list" id="specs-container">
          ${specsItemsHtml}
        </div>
      </details>
    `;
  }
});
