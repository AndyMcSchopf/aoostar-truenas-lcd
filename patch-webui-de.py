from pathlib import Path
p=Path("/app/webui.py");s=p.read_text(encoding="utf-8",errors="replace")
R={"AOOSTAR Screen Editor":"AOOSTAR TrueNAS LCD – Editor","Image fond":"Hintergrundbild","Uploader image":"Bild hochladen","Snap grille":"Am Raster ausrichten","Grille:":"Rastergröße:","Transition panneaux:":"Panel-Wechsel:","secondes":"Sekunden","Appliquer":"Übernehmen","Live Vorschau OFF":"Live-Vorschau AUS","Live Vorschau ON":"Live-Vorschau EIN","Labels disponibles (clic pour copier):":"Verfügbare Sensoren (anklicken zum Kopieren):","Actions":"Aktionen","Unité":"Einheit","Valeur":"Wert","Dupliquer":"Duplizieren","Supprimer":"Löschen","Exporter JSON":"JSON exportieren","Importer JSON":"JSON importieren","Annuler":"Abbrechen","Créer panel":"Panel erstellen","Creer panel":"Panel erstellen","CPU温度":"CPU-Temperatur","CPU占用":"CPU-Auslastung","RAM占用":"RAM-Auslastung","RAM温度":"RAM-Temperatur","GPU温度":"GPU-Temperatur"}
for a,b in R.items():s=s.replace(a,b)
inject="\ntry:\n    import sys\n    sys.path.insert(0, '/app')\n    from webui_de import install_routes\n    install_routes(app)\nexcept Exception as e:\n    print('German UI helper warning:', e)\n\n"
i=s.find("app.run(")
s=s[:i]+inject+s[i:] if i>=0 else s+inject
p.write_text(s,encoding="utf-8")
print("German UI patch applied")
