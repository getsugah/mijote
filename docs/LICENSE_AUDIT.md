# Audit de licence de Mijote — 8 novembre 2026

## Conclusion et périmètre

Aucune incompatibilité bloquante identifiée pour placer les éléments propres à
Mijote sous PolyForm Noncommercial 1.0.0, dans la mesure des droits détenus par
Getsugah. Les composants tiers conservent leurs licences respectives ; cet audit
ne les place pas sous PolyForm et ne présume pas qu’une bibliothèque impose sa
licence à toute l’application.

Examen des sources, scripts, visuels, manifestes verrouillés et textes de licence
installés : 19 paquets Python de production, 7 paquets supplémentaires de tests,
96 paquets npm dont 46 installés et 50 variantes optionnelles absentes. Pour ces
dernières, les métadonnées des versions exactes ont été vérifiées auprès du registre
officiel npm ; leurs binaires ne font pas partie des sources du projet.

Le répertoire n’a pas d’historique Git local. Aucun code tiers propriétaire ou
élément de code sous GPL/AGPL imposant une licence incompatible n’a été identifié
dans les fichiers examinés ; cette vérification ne démontre pas à elle seule
l’origine de chaque ligne ni l’absence de droits tiers inconnus.

## Dépendances et obligations

Les versions, expressions de licence et provenances sont dans
[THIRD_PARTY_MANIFEST.json](../THIRD_PARTY_MANIFEST.json). Les 76 textes de licence
et notice collectés sont reproduits sans modifier leur formulation dans
[THIRD_PARTY_NOTICES.txt](../THIRD_PARTY_NOTICES.txt).

| Groupe | Licences et traitement |
| --- | --- |
| FastAPI, SQLAlchemy, Alembic, Pydantic, h11, AnyIO et autres dépendances Python | Principalement MIT ; conserver leurs mentions |
| Uvicorn, Starlette, Click, IDNA, MarkupSafe, HTTPX et HTTPcore | BSD-3-Clause ; conserver copyrights, conditions et avertissements |
| OpenTelemetry, TypeScript, fake-indexeddb | Apache-2.0 ; conserver licence, mentions applicables et notices fournies |
| typing-extensions | PSF-2.0 ; conserver le texte et les mentions |
| Vue, Vite, Rollup, esbuild et majorité des paquets npm | MIT ; conserver les notices ; variantes natives couvertes par les distributions parentes lorsqu’elles ne fournissent pas de fichier séparé |
| Autres composants JavaScript et notices embarquées | BSD-2-Clause, BSD-3-Clause, ISC, CC0 et autres permissions reproduites dans les textes amont |
| Pillow et codecs embarqués | MIT-CMU pour Pillow ; notices intégrales des bibliothèques natives conservées, dont FreeType, HarfBuzz, JPEG, PNG, WebP, AVIF et OpenJPEG |
| Certifi, dépendance de tests | MPL-2.0 ; fichiers distincts, non modifiés et non intégrés au code propre de Mijote |
| packaging, dépendance de tests | Apache-2.0 OR BSD-2-Clause, selon le choix permis par sa licence |

La MPL de Certifi est un copyleft limité aux fichiers, compatible avec la présence
de code sous une autre licence dans le même ensemble. Certifi n’est pas une
dépendance de production verrouillée ni une partie du frontend. Sa présence dans
l’environnement de tests n’impose pas MPL à Mijote. Référence :
[FAQ officielle Mozilla](https://www.mozilla.org/en-US/MPL/2.0/FAQ/).

### Mentions GPL trouvées dans les annexes de Pillow

- FreeType propose une alternative entre GPL et FreeType License. La voie retenue
  pour cette distribution est **FTL**, avec conservation de son texte et de son crédit.
  Voir [FreeType](https://freetype.org/license.html).
- Les mentions GPL de XZ concernent notamment ses scripts et son système de
  construction. La bibliothèque **liblzma 5.8.4 est sous 0BSD**, d’après sa
  [notice officielle](https://raw.githubusercontent.com/tukaani-project/xz/v5.8.4/COPYING).
  L’annexe fournie dans la roue Pillow contient un ancien résumé parlant de domaine
  public : ce texte est conservé sans altération et la distinction documentée.
- Ces mentions ne permettent pas de conclure que Mijote serait GPL, ni que le
  choix de PolyForm pour le code propre du projet serait bloqué.

### Distribution compilée

Le bundle JavaScript initialement examiné ne contenait aucune mention de licence.
Un simple inventaire des noms dans le README n’aurait pas suffi à accompagner les
copies de Vue et des autres éléments distribués. Les textes et notices sont donc
fournis dans `frontend/public/legal/`, repris par le build Vite et le Dockerfile
existants. Le code de l’application et ses règles de construction restent inchangés.

La copie complète du fichier de licence de Pillow couvre les notices embarquées
de sa roue. Les licences et notices présentes dans les distributions Python ne
doivent pas être retirées de l’image installée.

L’audit n’est pas un inventaire complet des systèmes Debian, Python et Node des
images de base. Si une image Docker complète est publiée ultérieurement, ses
paquets système restent sous leurs licences propres, y compris GPL/LGPL lorsqu’elles
s’appliquent. Cette agrégation ne place pas automatiquement le code Mijote sous ces
licences, mais leurs obligations de redistribution et de fourniture de sources
applicables doivent être respectées.

## Titulaire et visuels

Getsugah a autorisé ce pseudonyme comme mention de copyright pour les éléments
sur lesquels il détient des droits. Le projet a été développé à sa demande avec
l’assistance de Codex ; aucun droit n’est inventé ou attribué à un assistant.

L’origine du nom et du SVG, puis séparément celle des deux icônes PNG, a été
confirmée par Getsugah comme une création pour ce projet avec Codex. Les PNG sont
des variantes simplifiées, pas des exports identiques. Les fichiers n’ont pas été
modifiés. Les limites de vérification et le périmètre des droits sont décrits dans
[ASSETS.md](../ASSETS.md).

Les recettes, images importées, bases, sauvegardes et paramètres privés sont exclus
de la publication du code. La licence du projet ne donne aucun droit sur les
contenus importés appartenant à des tiers.

## Application de PolyForm

- `LICENSE` contient les octets du [texte officiel](https://polyformproject.org/licenses/noncommercial/1.0.0.txt), sans ajout, traduction ou substitution.
- SHA-256 du texte récupéré : `ffcca38841adb694b6f380647e15f17c446a4d1656fed51a1e2041d064c94cc8`.
- `NOTICE` porte séparément la ligne `Required Notice: Copyright 2026 Getsugah`.
- README et COMMERCIAL.md décrivent les usages gratuits, les possibilités de
  modification et redistribution et les usages commerciaux non couverts, sans
  remplacer les termes ni supprimer les usages expressément permis à certaines organisations.
- Le projet est à code consultable ; la restriction commerciale ne correspond
  pas à la [définition open source de l’OSI](https://opensource.org/osd).
- Toute modification de dépendance nécessite de revoir l’inventaire et les textes ;
  `scripts/sync_legal.py` synchronise seulement les copies des documents existants.

Cet audit technique est limité aux éléments examinés et aux versions indiquées.
Il ne constitue pas une garantie sur des droits inconnus ou une consultation juridique.
