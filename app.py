# app.py
from flask import Flask, render_template_string, request
import pandas as pd
from best_team_prognose import main as compute_team
import io
from contextlib import redirect_stdout

app = Flask(__name__)

EXCEL_PATH = "spieler_mit_position.xlsx"

# Spieler einmal einlesen
df_players = pd.read_excel(EXCEL_PATH)
df_players = df_players.dropna(subset=["Name","Position","MW mio.","Pkt"])
df_players["Marktwert"] = pd.to_numeric(df_players["MW mio."], errors="coerce") * 1_000_000
df_players["Punkte"] = pd.to_numeric(df_players["Pkt"], errors="coerce")
df_players["Verein"] = df_players["Team"]
df_players["ID"] = df_players["Name"]
df_players["Angezeigter Name"] = df_players["Name"]
players_list = df_players[["ID","Angezeigter Name","Verein","Position","Marktwert","Punkte"]].to_dict("records")

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>Bestes Kicker-Team</title>
  <style>
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: #f9fafb;
      margin: 0;
      padding: 40px;
      color: #333;
    }
    h1, h2 { color: #1f2937; }
    form {
      margin-bottom: 30px;
    }
    input[type="submit"] {
      padding: 12px 20px;
      background: #4f46e5;
      color: white;
      border: none;
      border-radius: 10px;
      font-size: 16px;
      cursor: pointer;
      transition: background 0.3s;
      margin-top: 10px;
      width: 100%;
    }
    input[type="submit"]:hover { background: #4338ca; }
    pre {
      background: #f3f4f6;
      padding: 15px;
      border-radius: 10px;
      overflow-x: auto;
      box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .multi-container { margin-bottom: 20px; }
    .search-input {
      width: 100%;
      padding: 8px;
      border-radius: 8px;
      border: 1px solid #ccc;
      box-shadow: 0 2px 5px rgba(0,0,0,0.05);
      margin-bottom: 5px;
    }
    .dropdown {
      max-height: 200px;
      overflow-y: auto;
      border: 1px solid #ccc;
      border-radius: 8px;
      background: #fff;
      box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .dropdown-item {
      padding: 8px;
      cursor: pointer;
    }
    .dropdown-item:hover { background: #eef2ff; }
    .dropdown-item.selected {
      background: #4f46e5;
      color: white;
    }
    .selected-list {
      margin-top: 5px;
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
    }
    .chip {
      background: #4f46e5;
      color: white;
      padding: 5px 10px;
      border-radius: 15px;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <h1>Beste 37-Mio-Kombi</h1>
  <p>Formation: 3-4-3</p>

  <h2>Einstellungen</h2>
  <form method="POST">
    <div class="multi-container">
      <label>Wunschspieler:</label>
      <input type="text" placeholder="Spieler suchen..." class="search-input" id="wunsch-search">
      <div class="dropdown" id="wunsch-dropdown"></div>
      <div class="selected-list" id="wunsch-selected"></div>
    </div>

    <div class="multi-container">
      <label>Ausgeschlossene Spieler:</label>
      <input type="text" placeholder="Spieler suchen..." class="search-input" id="ausgeschlossen-search">
      <div class="dropdown" id="ausgeschlossen-dropdown"></div>
      <div class="selected-list" id="ausgeschlossen-selected"></div>
    </div>

    <div class="multi-container">
      <label>Max Spieler pro Verein:</label>
      <input type="number" name="max_spieler_pro_verein" value="1" min="1" style="width:100px; padding:5px; border-radius:5px; border:1px solid #ccc;">
    </div>


    <input type="submit" value="Berechnen">
  </form>

  {% if result %}
    <h2>Ergebnis</h2>
    <pre>{{ result }}</pre>
  {% endif %}

  <script>
    const players = {{ players|tojson }};

    function setupMultiSelect(searchInputId, dropdownId, nameAttr, selectedListId) {
      const searchInput = document.getElementById(searchInputId);
      const dropdown = document.getElementById(dropdownId);
      const selectedList = document.getElementById(selectedListId);
      const selected = new Set();

      function renderDropdown(filter="") {
        dropdown.innerHTML = "";
        const filtered = players.filter(p => p["Angezeigter Name"].toLowerCase().includes(filter.toLowerCase()));
        filtered.forEach(p => {
          const div = document.createElement("div");
          div.textContent = p["Angezeigter Name"] + " (" + p["Verein"] + ")";
          div.classList.add("dropdown-item");
          if (selected.has(p["Angezeigter Name"])) div.classList.add("selected");
          div.addEventListener("click", () => {
            if (selected.has(p["Angezeigter Name"])) selected.delete(p["Angezeigter Name"]);
            else selected.add(p["Angezeigter Name"]);
            renderDropdown(searchInput.value);
            updateHiddenInputs();
            renderSelectedList();
          });
          dropdown.appendChild(div);
        });
      }

      function updateHiddenInputs() {
        const oldInputs = document.querySelectorAll(`input[name='${nameAttr}']`);
        oldInputs.forEach(i => i.remove());
        selected.forEach(val => {
          const input = document.createElement("input");
          input.type = "hidden";
          input.name = nameAttr;
          input.value = val;
          document.querySelector("form").appendChild(input);
        });
      }

      function renderSelectedList() {
        selectedList.innerHTML = "";
        selected.forEach(val => {
          const chip = document.createElement("span");
          chip.textContent = val;
          chip.classList.add("chip");
          selectedList.appendChild(chip);
        });
      }

      searchInput.addEventListener("input", () => renderDropdown(searchInput.value));
      renderDropdown();
    }

    setupMultiSelect("wunsch-search", "wunsch-dropdown", "wunschspieler", "wunsch-selected");
    setupMultiSelect("ausgeschlossen-search", "ausgeschlossen-dropdown", "ausgeschlossen", "ausgeschlossen-selected");
  </script>
</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def index():
    result_text = ""
    if request.method == "POST":
      wunschspieler = set(request.form.getlist("wunschspieler"))
      ausgeschlossen = set(request.form.getlist("ausgeschlossen"))

      # Neuen Wert aus Formular auslesen
      max_spieler_pro_verein = int(request.form.get("max_spieler_pro_verein", 1))

      buf = io.StringIO()
      with redirect_stdout(buf):
          compute_team(
              EXCEL_PATH,
              wunschspieler=wunschspieler,
              ausgeschlossen=ausgeschlossen,
              max_spieler_pro_verein=max_spieler_pro_verein
          )
      result_text = buf.getvalue()


    return render_template_string(
        HTML_PAGE,
        players=players_list,
        result=result_text
    )

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))  # nimmt Render-PORT oder 3000 lokal
    app.run(host="0.0.0.0", port=port, debug=False)

