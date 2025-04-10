# SpaceExplore
a simple video game
---

**But du jeu**  
Chaque joueur incarne un commandant spatial : collecter des totems en explorant des systèmes planétaires et retourner sur son Système d’Origine (couleur du vaisseau) avec une collection gagnante.

---

**Mise en Place**  
- *Plateau* : Grille de 24×24 cases ; placement aléatoire de 7 systèmes Capitale (2×2 cases) et 8 systèmes Planète, en respectant les distances minimales.  
- *Systèmes* : Chaque système Capitale possède un rack avec cartes « Relation-Faction » et un stock de totems répartis par faction.
- *Joueur* : Couleur de vaisseau aléatoire parmi 7 ; le Système d’Origine correspond à cette couleur ; placement du vaisseau sur un système au hasard lors du setup (peut être sur le Système d’Origine).
- *Factions* : 6 factions ABCDEF , réparties dans les rack de couleur correpondante:
| Couleur  | Factions (avec nombre)                |
|----------|----------------------------------------|
| Jaune    | A (6), B (1)                          |
| Rouge    | C (2), D (5)                          |
| Violet   | E (4), F (3)                          |
| Orange   | A (4), B (1), D (1), F (1)            |
| Vert     | A (3), C (1), D (1), E (2)            |
| Bleu     | A (1), B (1), C (1), D (2), E (1), F (1) |
| Rose     | A (4), D (2), E (1)                   |

---

**Déroulement d’un Tour**  
Le joueur peut réaliser une seule fois par tour chacune des actions suivantes :  
- **Déplacement** : Jusqu’à 4 cases (diagonales et orthogonal) ; impossible de se déplacer à l'intérieur d'un même système (d'une des 4 cases à une autre) ; arrivée sur un système caché le révèle et affiche la première carte « Relation-Faction ».  
- **Récolte** : Sur un système Planétaire révélé, prélever un totem correspondant à la faction indiquée par la carte Relation-Faction du rack.  
- **Dépôt** : Déposer un totem sur le système courant dans le rack associé.  
- **Influence** : Sur un système Capitale révélé, faire défiler la pile des cartes « Relation-Faction » pour modifier la faction affichée.  
- **Observation** : Si le vaisseau n'est sur aucun système, révéler temporairement (2 sec, mode non bloquant) un système caché au clic. (Action utilisable une seule fois par tour)

---

**Conditions de Victoire et Fin de Partie**  
La partie se termine si :  
- Un joueur atteint son Système d’Origine et remplit une des conditions suivantes avec ses totems :  
  - Au moins un totem de chaque faction (A, B, C, D, E, F)  
  - Au moins un totem de chaque couleur (7 couleurs)  
  - 3 totems de la même couleur provenant de 3 factions différentes  
  - 3 totems de la même faction provenant de 3 couleurs différentes  
- Ou après 40 tours (ou si tous les autres joueurs abandonnent).

**Scoring**  
Le score est la somme des valeurs propres des totems + 100 points de bonus pour chaque groupe de 3 (ou plus) totems identiques par couleur ou par faction.

---
