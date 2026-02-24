const apiKey = CONFIG.YOUTUBE_API_KEY;
let currentAnalysisResult = null;

// 1. AUTO-DETECT VIDEO
window.addEventListener("DOMContentLoaded", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.url?.includes("youtube.com/watch")) {
    const urlParams = new URLSearchParams(new URL(tab.url).search);
    const videoId = urlParams.get("v");
    if (videoId) document.getElementById("videoId").value = videoId;
  }
});

const isTigrinya = (text) => /[\u1200-\u137F]/.test(text);

// 2. ANALYZE (LOCAL AI)
document.getElementById("analyze").onclick = async () => {
  const videoId = document.getElementById("videoId").value.trim();
  if (!videoId) return alert("Please enter a Video ID");

  const btn = document.getElementById("analyze");
  const statsDiv = document.getElementById("total-display");
  const commentsDiv = document.getElementById("comments");
  const cardsDiv = document.getElementById("cards");

  // Reset UI
  btn.disabled = true;
  btn.innerText = "Processing...";
  statsDiv.innerText = "Step 1: Fetching from YouTube...";
  commentsDiv.innerHTML = "";
  cardsDiv.innerHTML = "";

  try {
    // 15 pages = 1500 comments. This takes time to filter.
    const rawData = await fetchCommentsFromYouTube(videoId, 15);

    if (rawData.length === 0) {
      statsDiv.innerText = "No Tigrigna found.";
      btn.disabled = false;
      btn.innerText = "Analyze Sentiment";
      return;
    }

    statsDiv.innerText = `Step 2: Sending ${rawData.length} to the Model...`;

    // Increased timeout for local processing
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 seconds

    const response = await fetch("http://127.0.0.1:5000/analyze-sentiment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ comments: rawData.map((c) => c.textDisplay) }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    const data = await response.json();

    if (data.status === "success") {
      currentAnalysisResult = data;
      statsDiv.innerText = `Analysis Results (${data.total_analyzed} comments)`;
      document.getElementById("download-analysis").style.display = "block";
      renderCards(data);
    } else {
      throw new Error(data.error || "Server returned an error");
    }
  } catch (e) {
    console.error("Local Error:", e);
    statsDiv.innerText = "Error: Check Console (F12)";
    alert(
      "Connection Failed. 1. Is app.py running? 2. Is CORS enabled in Flask?",
    );
  } finally {
    btn.disabled = false;
    btn.innerText = "Analyze Sentiment";
  }
};

// 3. COLLECT DATASET
document.getElementById("collect").onclick = async () => {
  const videoId = document.getElementById("videoId").value.trim();
  const btn = document.getElementById("collect");
  btn.disabled = true;
  try {
    const allComments = await fetchCommentsFromYouTube(videoId, null);
    if (allComments.length === 0) return alert("No Tigrigna found.");
    downloadCSV(allComments, `tig_dataset_${videoId}.csv`);
  } catch (e) {
    alert(e.message);
  } finally {
    btn.disabled = false;
  }
};

// 4. DOWNLOAD SORTED BY CONFIDENCE
document.getElementById("download-analysis").onclick = () => {
  if (!currentAnalysisResult) return;
  let rows = [];

  ["neutral", "negative", "positive"].forEach((sentiment) => {
    let list = currentAnalysisResult.results[sentiment] || [];

    // Internal sort by confidence (highest first)
    let sorted = [...list].sort((a, b) => b.confidence - a.confidence);

    sorted.forEach((item) => {
      rows.push({
        text: item.text,
        label: sentiment,
      });
    });
  });

  // Generate a random 4-digit number for the filename
  const randomId = Math.floor(1000 + Math.random() * 9000);
  const filename = `pseudo_labels_${randomId}.csv`;

  downloadCSV(rows, filename);
};

// HELPER: FETCH WITH STATUS UPDATES
async function fetchCommentsFromYouTube(videoId, limitPages) {
  let allComments = [];
  let nextPageToken = "";
  let pageCount = 0;
  const statsDiv = document.getElementById("total-display");

  do {
    const url = `https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId=${videoId}&maxResults=100&key=${apiKey}&pageToken=${nextPageToken}`;
    const res = await fetch(url);
    const data = await res.json();
    if (data.error) throw new Error(data.error.message);
    if (!data.items) break;

    const filtered = data.items
      .map((i) => ({
        textDisplay: i.snippet.topLevelComment.snippet.textDisplay,
      }))
      .filter((c) => isTigrinya(c.textDisplay));

    allComments = allComments.concat(filtered);
    nextPageToken = data.nextPageToken;
    pageCount++;

    // Update status so user knows it isn't frozen
    statsDiv.innerText = `Fetching: Found ${allComments.length} Tigrigna...`;

    if (limitPages && pageCount >= limitPages) break;
  } while (nextPageToken);
  return allComments;
}

// HELPER: CSV
function downloadCSV(data, filename) {
  // Only two headers: text and label
  let csv = "\uFEFFtext,label\n";

  data.forEach((i) => {
    let cleanText = (i.textDisplay || i.text || "")
      .toString()
      .replace(/"/g, '""') // Escape quotes
      .replace(/\n/g, " "); // Remove line breaks

    let label = i.label || "";

    csv += `"${cleanText}","${label}"\n`;
  });

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();

  // Cleanup
  setTimeout(() => URL.revokeObjectURL(url), 100);
}
// 5. UI: RENDER & HIDE/SHOW
let lastSelectedType = null;

function renderCards(apiResponse) {
  const cardsDiv = document.getElementById("cards");
  const title = document.getElementById("category-title");
  const listDiv = document.getElementById("comments");

  if (!cardsDiv) return;
  cardsDiv.innerHTML = "";

  ["positive", "neutral", "negative"].forEach((type) => {
    const count = apiResponse.counts[type] || 0;
    const card = document.createElement("div");
    card.className = `card ${type}`;
    card.innerHTML = `${type.toUpperCase()}<br><b>${count}</b>`;

    card.onclick = () => {
      // 1. TOGGLE HIDE: If clicking the same card again
      if (lastSelectedType === type) {
        card.classList.remove("active");
        if (title) title.style.display = "none";
        if (listDiv) {
          listDiv.innerHTML = "";
          listDiv.scrollTop = 0; // Reset scroll on hide
        }
        lastSelectedType = null;
        return;
      }

      // 2. SHOW NEW CATEGORY
      document
        .querySelectorAll(".card")
        .forEach((c) => c.classList.remove("active"));
      card.classList.add("active");
      lastSelectedType = type;

      if (title) {
        title.innerText = `${type} comments`;
        title.style.display = "block";
      }

      if (listDiv) {
        // Clear old list first
        listDiv.innerHTML = "";

        // --- THE FIX: Reset scroll position to the top ---
        listDiv.scrollTop = 0;

        const list = apiResponse.results[type] || [];
        const sorted = [...list].sort((a, b) => b.confidence - a.confidence);

        listDiv.innerHTML = sorted
          .map(
            (c) =>
              `<div class="comment text-${type}">
             <p>${c.text}</p>
           </div>`,
          )
          .join("");
      }
    };
    cardsDiv.appendChild(card);
  });
}
