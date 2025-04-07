# 🟡 Wolves Esports - Valorant Scrim Dashboard

This is a custom-built analytics dashboard created for **Wolves Esports Valorant** to analyze scrim performance in depth, featuring:

- 📊 **Map Win Rates & Round Insights**
- 🧩 **5-Agent Composition Win Rates**
- 🔫 **Pistol Round & 2nd Round Conversion Rates**
- 📈 **Post-Plant Success vs Retake Stats**
- 🔢 **Player Agent Stats (with filtering)**

Built using **Streamlit**, **Plotly**, and custom CSS to match Wolves' black and yellow branding.

---

## 🗂️ Features Breakdown

### 📊 Overview Tab
- Date filter range
- Map-wise win/draw/loss breakdown
- Horizontal bar chart for win rates

### 🧩 Map Composition Win Rates
- Select map to view top 5-agent comps
- Tracks win/draw/loss results for each comp
- Styled like rib.gg with agent icons

### 📈 Round Insights
- Filter by date and map
- Attack vs Defense WR based on starting side
- Highlighted table for quick insights
- 🔄 Post-Plant Success: stacked bar chart (Attack vs Retake)

### 🔫 Pistol Insights
- Win rates for first and second pistols by map
- 🍰 2nd round conversion pie charts:
  - WW/WL: conversion after pistol win
  - LL/LW: rebound after pistol loss

### 🔢 Player Agent Stats
- Select any player and filter by date/map
- Aggregated stats by agent: Rounds, K/D, ACS, FK, Plants, etc.
- Auto-averaged view (not raw match-by-match)

---

## 🛠️ Tech Stack
- **Streamlit** for interactive UI
- **Plotly** for dynamic charts
- **Pandas** for all data handling
- **Excel**-friendly CSV format for easy updates
- **Wolves theme** with black + #FDB913 yellow

---

## 🚀 Getting Started

1. Clone the repo
```bash
git clone https://github.com/yourusername/wolves-valorant-dashboard.git
cd wolves-valorant-dashboard
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run the dashboard
```bash
streamlit run streamlit_dashboard.py
```

Make sure `cleaned_score.csv`, `form.csv`, and the agent icons are present.

---

## 📁 Data Structure

### cleaned_score.csv
- Map, Date, Outcome, Start, First Pistol, Second Pistol
- Atk_PP_Success, Def_PP_Success
- Atk 2nd, Def 2nd

### form.csv
- Player, Date, Agent, Map (Column 1), Rounds, Kills, Deaths, Assists, FK, ACS, Plants, etc.
- Tracked 1 row per player per match

---

## 📸 Screenshots

![Dashboard Screenshot](assets/screenshot.png)

---

## 📣 Credits

Built and maintained by **Ominous**  
📍 Analyst @ Wolves Esports  
🐦 [@_SushantJha](https://x.com/_SushantJha)

---

## 📌 TODO / Future Work
- Add heatmaps or agent radar charts
- Export summary PDFs for weekly reports

---

