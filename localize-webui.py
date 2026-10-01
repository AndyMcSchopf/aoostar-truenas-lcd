#!/usr/bin/env python3
from pathlib import Path
p=Path('/app/webui.py')
s=p.read_text(encoding='utf-8')
# Upstream editor contains a mixture of French/Chinese/English UI literals.
# Keep route/API code untouched and translate presentation strings only.
repl={
'AOOSTAR Screen Editor v2':'AOOSTAR TrueNAS LCD Editor',
'AOOSTAR TrueNAS Screen Editor':'AOOSTAR TrueNAS LCD Editor',
'Éditeur':'Editor','Editeur':'Editor','Aperçu':'Vorschau','Apercu':'Vorschau',
'Ajouter':'Hinzufügen','Supprimer':'Löschen','Enregistrer':'Speichern','Sauvegarder':'Speichern',
'Annuler':'Abbrechen','Fermer':'Schließen','Ouvrir':'Öffnen','Charger':'Laden',
'Importer':'Importieren','Exporter':'Exportieren','Actualiser':'Aktualisieren',
'Rafraîchir':'Aktualisieren','Rafraichir':'Aktualisieren','Réinitialiser':'Zurücksetzen',
'Paramètres':'Einstellungen','Parametres':'Einstellungen','Configuration':'Konfiguration',
'Panneau':'Panel','Panneaux':'Panels','Élément':'Element','Éléments':'Elemente',
'Element':'Element','Elements':'Elemente','Capteur':'Sensor','Capteurs':'Sensoren',
'Valeur':'Wert','Valeurs':'Werte','Texte':'Text','Police':'Schriftart',
'Taille':'Größe','Couleur':'Farbe','Position':'Position','Largeur':'Breite','Hauteur':'Höhe',
'Fond':'Hintergrund','Image de fond':'Hintergrundbild','Durée':'Dauer','Duree':'Dauer',
'Vitesse':'Geschwindigkeit','Nom':'Name','Type':'Typ','Fichier':'Datei',
'Précédent':'Zurück','Precedent':'Zurück','Suivant':'Weiter','Déplacer':'Verschieben',
'Dupliquer':'Duplizieren','Visible':'Sichtbar','Alignement':'Ausrichtung',
'Gauche':'Links','Droite':'Rechts','Centre':'Zentriert','Haut':'Oben','Bas':'Unten',
'Save':'Speichern','Delete':'Löschen','Add':'Hinzufügen','Preview':'Vorschau',
'Background':'Hintergrund','Font':'Schriftart','Color':'Farbe','Sensor':'Sensor',
'Panels':'Panels','Panel':'Panel','Import':'Importieren','Export':'Exportieren',
'Refresh':'Aktualisieren','Settings':'Einstellungen','Text':'Text',
# Common Chinese literals observed in AOOSTAR editor variants
'保存':'Speichern','删除':'Löschen','添加':'Hinzufügen','取消':'Abbrechen','预览':'Vorschau',
'背景':'Hintergrund','字体':'Schriftart','颜色':'Farbe','传感器':'Sensor','面板':'Panel',
'设置':'Einstellungen','导入':'Importieren','导出':'Exportieren','刷新':'Aktualisieren',
'文本':'Text','位置':'Position','宽度':'Breite','高度':'Höhe','大小':'Größe',
'名称':'Name','类型':'Typ','文件':'Datei','确定':'OK','关闭':'Schließen'
}
# Longest first prevents partial replacement from defeating a longer phrase.
for a,b in sorted(repl.items(), key=lambda kv: len(kv[0]), reverse=True):
    s=s.replace(a,b)
s=s.replace('<html>', '<html lang="de">').replace('<html ', '<html lang="de" ', 1) if '<html lang=' not in s else s
p.write_text(s, encoding='utf-8')
print(f'WebUI lokalisiert: {len(repl)} Ersetzungen definiert')
