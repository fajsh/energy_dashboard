# Energie Dashboard Schweiz 2025

## Projektbeschreibung
Interaktives Dashboard zur Analyse von Energieproduktion und -verbrauch sowie die regionalen Unterschieden in der Schweiz.

Die Daten basieren auf der offiziellen Elektrizitätsstatistik des Bundesamts für Energie (https://www.bfe.admin.ch/bfe/de/home/versorgung/statistik-und-geodaten/energiestatistiken/elektrizitaetsstatistik.html). 

Das Dashboard wurde im Rahmen des Moduls CDS-111-Datenvisualisierung HS25 erstellt. 

## Architektur
- Datenimport: /data
- Visualisierungen: /plots
- Layout & UI: /layout
- Globale Zustände: /state

## Starten
streamlit run app.py
