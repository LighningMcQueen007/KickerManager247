# app.py
from flask import Flask, render_template_string, request
import pandas as pd
from best_team_prognose import main as compute_team
import io
from contextlib import redirect_stdout

# Vereinslogos Dictionary hier einfügen
logos = {
    "Bayern": "https://upload.wikimedia.org/wikipedia/commons/1/1b/FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg",
    "Dortmund": "https://upload.wikimedia.org/wikipedia/commons/6/67/Borussia_Dortmund_logo.svg",
    "Leipzig": "https://upload.wikimedia.org/wikipedia/commons/d/d6/VEREINFACHTES_LOGO_-_RB_Leipzig.svg",
    "Leverkusen": "https://upload.wikimedia.org/wikipedia/de/f/f7/Bayer_Leverkusen_Logo.svg",
    "Frankfurt": "https://upload.wikimedia.org/wikipedia/de/3/32/Logo_Eintracht_Frankfurt_1998.svg",
    "Wolfsburg": "https://upload.wikimedia.org/wikipedia/commons/f/f3/Logo-VfL-Wolfsburg.svg",
    "Stuttgart": "https://upload.wikimedia.org/wikipedia/commons/e/eb/VfB_Stuttgart_1893_Logo.svg",
    "Gladbach": "https://upload.wikimedia.org/wikipedia/commons/8/81/Borussia_M%C3%B6nchengladbach_logo.svg",
    "Bremen": "https://upload.wikimedia.org/wikipedia/commons/b/be/SV-Werder-Bremen-Logo.svg",
    "Köln": "https://upload.wikimedia.org/wikipedia/commons/1/10/Wappen_1_FC_Koeln.png",
    "Freiburg": "https://upload.wikimedia.org/wikipedia/de/b/bf/SC_Freiburg_Logo.svg",
    "Hoffenheim": "https://upload.wikimedia.org/wikipedia/commons/e/e7/Logo_TSG_Hoffenheim.svg",
    "Augsburg": "https://upload.wikimedia.org/wikipedia/de/b/b5/Logo_FC_Augsburg.svg",
    "Union": "https://upload.wikimedia.org/wikipedia/commons/4/44/1._FC_Union_Berlin_Logo.svg",
    "Mainz": "https://upload.wikimedia.org/wikipedia/commons/9/9e/Logo_Mainz_05.svg",
    "Heidenheim": "https://upload.wikimedia.org/wikipedia/commons/9/9d/1._FC_Heidenheim_1846.svg",
    "HSV": "https://upload.wikimedia.org/wikipedia/commons/f/f7/Hamburger_SV_logo.svg",
    "Pauli": "https://upload.wikimedia.org/wikipedia/de/b/b3/Fc_st_pauli_logo.svg"
}



app = Flask(__name__)

EXCEL_PATH = "spieler_mit_position.xlsx"


# Spieler einlesen
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
      font-family: 'Segoe UI', sans-serif;
      background: linear-gradient(160deg, #0f172a, #1e293b);
      margin: 0;
      padding: 20px;
      color: #f1f5f9;
    }
    h1, h2 {
      color: #facc15;
      text-align: center;
      text-transform: uppercase;
      letter-spacing: 2px;
    }
    form {
      margin: 20px auto;
      max-width: 700px;
      background: rgba(255,255,255,0.05);
      padding: 20px;
      border-radius: 15px;
      backdrop-filter: blur(10px);
      box-shadow: 0 0 20px rgba(250,204,21,0.2);
    }
    label { font-weight: bold; }
    input[type="submit"] {
      padding: 14px;
      background: #facc15;
      color: #0f172a;
      font-weight: bold;
      border: none;
      border-radius: 12px;
      font-size: 18px;
      cursor: pointer;
      transition: all 0.3s;
      margin-top: 10px;
      width: 100%;
    }
    input[type="submit"]:hover {
      background: #eab308;
      transform: scale(1.02);
    }
    pre {
      background: rgba(0,0,0,0.6);
      padding: 15px;
      border-radius: 10px;
      overflow-x: auto;
      box-shadow: inset 0 0 10px rgba(0,0,0,0.4);
      font-family: monospace;
    }
    .multi-container {
      margin-bottom: 20px;
    }
    .search-input {
      width: 100%;
      padding: 10px;
      border-radius: 8px;
      border: none;
      outline: none;
      background: rgba(255,255,255,0.1);
      color: #f1f5f9;
    }
    .dropdown {
      max-height: 200px;
      overflow-y: auto;
      border-radius: 8px;
      background: rgba(0,0,0,0.4);
      margin-top: 5px;
    }
    .dropdown-item {
      padding: 8px;
      cursor: pointer;
      transition: background 0.2s;
    }
    .dropdown-item:hover { background: rgba(250,204,21,0.2); }
    .dropdown-item.selected {
      background: #facc15;
      color: #0f172a;
    }
    .selected-list {
      margin-top: 5px;
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
    }
    .chip {
      background: #facc15;
      color: #0f172a;
      padding: 5px 10px;
      border-radius: 15px;
      font-size: 14px;
      font-weight: bold;
    }
    /* Spielfeld */
    .field {
      margin: 20px auto;
      width: 100%;
      max-width: 600px;       /* kleiner */
      aspect-ratio: 2/3;
      background: radial-gradient(circle at center, #065f46, #064e3b);
      border: 4px solid #facc15;
      border-radius: 20px;
      padding: 15px;
      display: flex;
      flex-direction: column;
      justify-content: space-evenly;
    }

    .row {
      display: flex;
      justify-content: center;
      gap: 25px;   /* enger */
    }

    .player {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      color: white;
      font-family: sans-serif;
    }

    .player-club {
      display: flex;
      align-items: center;
      justify-content: center;
      margin-top: 3px;
      font-size: 12px;
      color: #444;
    }

    .club-logo {
      width: 20px;
      height: 20px;
      object-fit: contain;
      margin-right: 5px;
    }

    .player-points {
      margin-top: 2px;
      font-size: 13px;
      font-weight: bold;
      color: #111;
    }


    .jersey {
      width: 70px;
      height: 70px;
      background-color: #c00; /* Trikot-Hintergrundfarbe */
      border-radius: 8px;
      margin: 0 auto;
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .club-logo-on-jersey {
      width: 36px;
      height: 36px;
      object-fit: contain;
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      z-index: 2;
    }

    .position-label {
      position: absolute;
      bottom: 2px;
      right: 2px;
      font-size: 10px;
      font-weight: bold;
      color: white;
      text-shadow: 1px 1px 2px black;
      z-index: 3;
    }


    /* kleine Ärmel */
    .jersey::before, .jersey::after {
      content: "";
      position: absolute;
      top: 15px;
      width: 20px;
      height: 20px;
      background: inherit;
      border: 2px solid #fff;
      border-radius: 4px;
    }
    .jersey::before { left: -20px; }
    .jersey::after { right: -20px; }

    .player-name {
      margin-top: 8px;
      font-size: 16px;   /* größer als vorher */
      font-weight: bold;
      text-align: center;
      max-width: 90px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .player-name {
      margin-top: 5px;
      font-size: 12px;
      text-align: center;
    }
  </style>
</head>
<body>
  <h1>Beste 37-Mio-Kombi</h1>
  <p style="text-align:center;">Formation: 3-4-3</p>

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
      <input type="number" name="max_spieler_pro_verein" value="1" min="1" style="width:100px; padding:5px; border-radius:5px; border:none; background:rgba(255,255,255,0.1); color:white;">
    </div>

    <input type="submit" value="Berechnen">
  </form>

  {% if result %}
    <h2>Dein Team</h2>
    <div class="field">
      <div class="row">
        {% set forwards = team | selectattr("Position","equalto","FORWARD") | list %}
        {% for p in forwards %}
          <div class="player">
            <div class="jersey">
              <img src="{{ logos.get(p['Verein'], '') }}" alt="{{ p['Verein'] }} Logo" class="club-logo-on-jersey">
              <span class="position-label">{{ p["Position"][:2] }}</span>
            </div>
            <div class="player-name">{{ p["Angezeigter Name"] }}</div>
            <div class="player-points">{{ p["Punkte"]|int }} Pkt</div>
          </div>
        {% endfor %}
      </div>

      <div class="row">
        {% set forwards = team | selectattr("Position","equalto","MIDFIELDER") | list %}
        {% for p in forwards %}
          <div class="player">
            <div class="jersey">
              <img src="{{ logos.get(p['Verein'], '') }}" alt="{{ p['Verein'] }} Logo" class="club-logo-on-jersey">
              <span class="position-label">{{ p["Position"][:2] }}</span>
            </div>
            <div class="player-name">{{ p["Angezeigter Name"] }}</div>
            <div class="player-points">{{ p["Punkte"]|int }} Pkt</div>
          </div>
        {% endfor %}
      </div>

      <div class="row">
        {% set forwards = team | selectattr("Position","equalto","DEFENDER") | list %}
        {% for p in forwards %}
          <div class="player">
            <div class="jersey">
              <img src="{{ logos.get(p['Verein'], '') }}" alt="{{ p['Verein'] }} Logo" class="club-logo-on-jersey">
              <span class="position-label">{{ p["Position"][:2] }}</span>
            </div>
            <div class="player-name">{{ p["Angezeigter Name"] }}</div>
            <div class="player-points">{{ p["Punkte"]|int }} Pkt</div>
          </div>
        {% endfor %}
      </div>

      <div class="row">
        {% set forwards = team | selectattr("Position","equalto","GOALKEEPER") | list %}
        {% for p in forwards %}
          <div class="player">
            <div class="jersey">
              <img src="{{ logos.get(p['Verein'], '') }}" alt="{{ p['Verein'] }} Logo" class="club-logo-on-jersey">
              <span class="position-label">{{ p["Position"][:2] }}</span>
            </div>
            <div class="player-name">{{ p["Angezeigter Name"] }}</div>
            <div class="player-points">{{ p["Punkte"]|int }} Pkt</div>
          </div>
        {% endfor %}
      </div>

    </div>
    <h2>Details</h2>
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
      max_spieler_pro_verein = int(request.form.get("max_spieler_pro_verein", 1))

      buf = io.StringIO()
      with redirect_stdout(buf):
          team = compute_team(
              EXCEL_PATH,
              wunschspieler=wunschspieler,
              ausgeschlossen=ausgeschlossen,
              max_spieler_pro_verein=max_spieler_pro_verein
          )
      result_text = buf.getvalue()


    return render_template_string(
        HTML_PAGE,
        players=players_list,
        result=result_text,
        team=team if request.method == "POST" else [],
        logos=logos  # hier hinzufügen
    )



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
