# Cahier des charges — Application Python Tkinter de test de providers IA

## 1. Objet

Développer une application desktop en **Python** avec interface graphique **Tkinter** permettant de **configurer, tester, comparer et historiser** plusieurs providers d’IA ainsi que les modèles qu’ils proposent, sur les modalités suivantes :

* **Texte**
* **Image**
* **Audio**
* **Vidéo**
* **Autres modalités si supportées par le provider**

L’application doit servir d’outil local de travail pour évaluer différents fournisseurs, leurs modèles, leurs paramètres, leurs performances, leur coût et leur stabilité.

---

## 2. Providers minimum à supporter

L’application devra prévoir au minimum la prise en charge des providers suivants :

* **MiniMax**
* **Z.ai**
* **OpenAI**
* **Alibaba**
* **Anthropic**
* **OpenRouter**

L’architecture devra être **extensible** afin de permettre l’ajout futur d’autres providers sans refonte majeure.

---

## 3. Objectifs fonctionnels

L’application devra permettre de :

1. **Configurer plusieurs providers**
2. **Gérer plusieurs comptes / abonnements / credentials par provider**
3. **Enregistrer les paramètres d’accès**
4. **Gérer l’authentification par API key, token et OAuth/qauth**
5. **Lister, créer, modifier et stocker les modèles**
6. **Tester les modèles en texte, image et audio**
7. **Comparer les résultats entre modèles et providers**
8. **Historiser les tests**
9. **Noter les modèles et les résultats**
10. **Exporter les données utiles**

---

## 4. Contraintes techniques

* Langage : **Python 3.11+**
* Interface : **Tkinter** (ttk autorisé)
* L’application devra fonctionner à la fois en **mode GUI desktop** et en **mode CLI**
* Le mode CLI devra être utilisable aussi bien par un **humain** que par un **agent IA**
* Le mode CLI devra être conçu pour fonctionner en **ligne de commande uniquement**, avec des commandes explicites, stables et scriptables
* Les principales fonctionnalités métier devront être accessibles depuis les deux interfaces, avec une logique commune partagée
* Code modulaire, maintenable et structuré
* Gestion robuste des erreurs
* Persistance locale des données
* Limitation des dépendances externes au strict utile
* Projet facilement lançable et documenté

---

## 5. Gestion des providers

Pour chaque provider, l’application devra permettre de gérer :

* nom du provider
* statut actif / inactif
* URL de base
* endpoint(s)
* version d’API si applicable
* type d’authentification
* en-têtes personnalisés
* timeout
* stratégie de retry
* proxy éventuel
* commentaires / notes internes

Le système devra être conçu de manière générique, avec possibilité d’ajouter des **champs spécifiques par provider**.

---

## 6. Gestion des comptes, abonnements et credentials

L’application devra impérativement gérer **plusieurs profils d’accès par provider**.

Exemples :

* OpenAI perso
* OpenAI pro
* OpenAI test
* OpenRouter compte A
* OpenRouter compte B

Chaque profil devra pouvoir stocker :

* nom du profil
* provider associé
* API key
* bearer token
* OAuth / qauth token
* refresh token
* client id
* client secret
* organisation / project id si nécessaire
* commentaires
* date de création / modification
* statut actif / inactif
* statut de validité

Fonctions attendues :

* créer un profil
* modifier un profil
* supprimer un profil
* dupliquer un profil
* activer / désactiver un profil
* tester la connexion

### Sécurité minimale

* masquer les secrets dans l’interface
* révélation manuelle sur action utilisateur
* ne jamais afficher les secrets complets dans les logs
* prévoir une abstraction permettant un futur stockage chiffré

---

## 7. Gestion obligatoire de OAuth / qauth

La prise en charge de **OAuth / qauth** est obligatoire dans la conception.

L’interface devra permettre de renseigner au minimum :

* type d’authentification
* client id
* client secret
* token d’accès
* refresh token
* date d’expiration
* scopes
* authorization URL
* token endpoint
* champs additionnels libres

Fonctions attendues :

* test d’authentification
* rafraîchissement du token
* stockage des informations d’auth
* structure extensible pour implémentations spécifiques par provider

Si certains flux OAuth réels ne peuvent pas être finalisés immédiatement faute de documentation précise, l’application devra au minimum fournir :

* une **architecture prête**
* une **GUI complète**
* des **connecteurs mockés ou partiels** clairement identifiés

---

## 8. Gestion des modèles

L’application devra permettre, pour chaque provider :

* récupérer la liste des modèles via API si disponible
* ajouter des modèles manuellement
* modifier les fiches modèles
* supprimer / désactiver un modèle
* classer les modèles
* noter les modèles
* ajouter des tags et commentaires

### Métadonnées attendues par modèle

* nom technique
* nom affiché
* provider associé
* type principal : texte / image / audio / vidéo / multimodal / autre
* statut actif / inactif
* favori
* note
* tags
* coût estimé input/output si connu
* contexte max si connu
* capacités connues
* limites connues
* commentaires libres

### Capacités conseillées à tracer

* chat
* reasoning
* vision
* image generation
* video generation
* video understanding
* transcription
* speech
* embeddings
* tool calling
* JSON output
* streaming

---

## 9. Paramètres de test et presets

L’application devra permettre d’enregistrer des **presets de test** par modèle ou par type de tâche.

### 9.1 Tests texte

Paramètres à gérer :

* system prompt
* user prompt
* temperature
* top_p
* max_tokens
* frequency_penalty
* presence_penalty
* stop sequences
* seed si supporté
* JSON mode / structured output si supporté
* streaming si supporté

### 9.2 Tests image

Paramètres à gérer :

* prompt
* negative prompt
* taille
* ratio
* qualité
* steps
* seed
* format de sortie
* nombre d’images

### 9.3 Tests audio

Paramètres à gérer :

* fichier d’entrée
* type d’opération : transcription / speech / translation
* voice
* format
* sample rate
* langue
* temperature
* diarization si supporté
* timestamps si supporté

### 9.4 Tests vidéo

Paramètres à gérer lorsque supportés :

* prompt
* negative prompt
* image ou vidéo source
* durée
* résolution
* ratio
* fps
* seed
* format de sortie
* nombre de variantes
* mode génération / édition / transformation / upscaling
* piste audio éventuelle
* paramètres spécifiques provider

### 9.5 Autres modalités

L’architecture devra permettre d’ajouter d’autres types de tests si certains providers exposent des capacités supplémentaires, par exemple :

* embeddings
* vision analysis
* document understanding
* reranking
* moderation
* tool calling spécialisé
* tâches multimodales avancées

### Fonctions attendues pour les presets

* créer
* enregistrer
* renommer
* modifier
* dupliquer
* supprimer
* appliquer rapidement
* versionner si possible à terme

---

## 10. Interface de test (Test Lab)

L’interface principale de test devra permettre de :

* sélectionner un provider
* sélectionner un profil de credentials
* sélectionner un modèle
* sélectionner une modalité : texte / image / audio / vidéo / autre si disponible
* charger un preset
* saisir ou modifier les paramètres
* exécuter un test
* voir la requête envoyée
* voir la réponse brute
* voir une réponse formatée
* mesurer la latence
* afficher le statut de succès ou d’échec
* afficher le coût estimé si disponible
* sauvegarder le résultat dans l’historique

---

## 11. Historique des tests

Tous les tests devront être historisés localement.

### Données à conserver

* date / heure
* provider
* profil utilisé
* modèle
* type de tâche
* paramètres
* requête éventuelle
* réponse
* latence
* coût estimé
* statut succès / échec
* message d’erreur
* note utilisateur
* référence du ou des fichiers utilisés

### Fonctions attendues

* filtrer l’historique
* rechercher dans l’historique
* relancer un test depuis l’historique
* dupliquer un test
* comparer plusieurs tests côte à côte
* exporter en JSON / CSV

---

## 12. Comparaison des résultats

L’application devra proposer un mode de comparaison permettant de confronter plusieurs modèles ou providers selon :

* temps de réponse
* coût estimé
* qualité perçue
* stabilité
* résultat brut
* fichiers de sortie générés
* note utilisateur

### Fonction complémentaire recommandée

Un mode **multi-run** permettant d’exécuter le même prompt sur plusieurs modèles et d’afficher un comparatif synthétique.

Ce mode devra idéalement fonctionner aussi pour les cas image, audio et vidéo lorsque cela est pertinent.

---

## 13. Système de notation et d’évaluation

L’application devra intégrer une notation :

### Par modèle

* note globale
* coût
* vitesse
* qualité
* stabilité
* pertinence
* commentaire libre

### Par test

* note du résultat
* qualité du rendu
* conformité à la demande
* commentaires libres

### Par provider

* stabilité générale
* qualité globale
* qualité de l’intégration
* commentaires

---

## 14. Tableau de bord et indicateurs

Le dashboard pourra afficher :

* nombre de providers configurés
* nombre de profils actifs
* nombre de modèles disponibles
* derniers tests exécutés
* derniers échecs
* latence moyenne
* coût moyen estimé
* modèles favoris
* providers en erreur

### Indicateur de santé recommandé

Pour chaque provider / profil :

* OK
* auth invalide
* endpoint KO
* timeout
* non testé

---

## 15. Stockage local

Le stockage devra être persistant et structuré.

### Solution recommandée

* **SQLite** pour les données métiers
* **JSON** éventuel pour certaines préférences ou exports

### Données à stocker

* providers
* credentials
* profils OAuth/qauth
* modèles
* presets
* historiques
* notes
* paramètres UI
* favoris

Une couche dédiée de persistance devra être mise en place.

---

## 16. Architecture logicielle recommandée

Structure cible recommandée :

```text
app/
  app.py
  ui/
  models/
  services/
  providers/
  storage/
  utils/
  config/
  tests/
```

### Organisation attendue

* `app.py` : point d’entrée
* `ui/` : vues Tkinter, formulaires, dialogues, tableaux
* `models/` : entités métier
* `services/` : logique applicative
* `providers/` : adaptateurs par provider
* `storage/` : persistance SQLite/JSON
* `utils/` : helpers techniques
* `config/` : constantes, paramètres globaux
* `tests/` : tests unitaires minimum

### Abstraction provider attendue

Créer une classe de base de provider avec au minimum :

* test de connexion
* récupération des modèles
* appel texte
* appel image
* appel audio
* récupération ou normalisation des capacités

Chaque provider concret devra implémenter cette interface, même partiellement.

---

## 17. Interfaces utilisateur attendues

L’application devra proposer **deux modes d’utilisation complémentaires** :

1. **une interface graphique Tkinter** pour l’usage humain interactif
2. **une interface CLI** pour l’usage en terminal, aussi bien par un humain que par un agent IA

Les deux interfaces devront reposer sur une **même couche métier** afin d’éviter les divergences fonctionnelles.

### 17.1 Interface graphique

L’interface GUI devra être sobre, lisible et pratique.

### Organisation recommandée

* menu ou panneau latéral
* barre de statut
* zone de logs techniques
* zones formulaires claires
* tableaux/listes filtrables
* fenêtres de dialogue d’édition

### Sections recommandées

* Dashboard
* Providers
* Credentials
* Models
* Test Lab
* History
* Settings

### 17.2 Interface CLI

Le mode CLI devra permettre d’exécuter les principales opérations sans interface graphique.

#### Objectifs

* usage humain en terminal
* usage automatisé dans des scripts
* usage par un agent IA pilotant l’application uniquement via ligne de commande
* sorties lisibles en console et exploitables par machine

#### Exigences CLI

* commandes stables et explicites
* aide intégrée (`--help`)
* sous-commandes organisées par domaine fonctionnel
* options nommées claires
* possibilité d’entrée/sortie non interactive
* codes de retour cohérents
* affichage texte lisible pour humain
* possibilité de sortie structurée de type JSON pour intégration agent / script

#### Commandes cibles recommandées

* gestion des providers
* gestion des credentials
* gestion des modèles
* exécution de tests texte / image / audio
* récupération d’historique
* export de résultats
* test de connexion
* import / export de configuration

#### Exemples de philosophie de commandes

* `app providers list`
* `app providers add`
* `app credentials test`
* `app models sync`
* `app run text`
* `app run image`
* `app history list`
* `app export history --format json`

Le mode CLI devra être pensé dès la conception, et non comme un ajout secondaire.

---

## 18. Journal technique et debug

Un panneau de debug devra permettre d’afficher :

* URL appelée
* méthode HTTP
* payload envoyé
* headers masqués
* code HTTP
* réponse brute
* durée d’exécution
* message d’erreur détaillé

Ce panneau est important pour diagnostiquer les problèmes d’intégration.

---

## 19. Performances et robustesse

L’application devra prévoir :

* validation des champs
* gestion des erreurs réseau
* gestion des timeouts
* gestion des erreurs d’authentification
* gestion des réponses invalides
* gestion des providers partiellement implémentés
* logs lisibles
* messages utilisateur compréhensibles

### Point important

Les appels réseau ne devront pas bloquer l’interface. Il faudra prévoir un mécanisme adapté, par exemple :

* threads
* file de tâches
* exécution asynchrone compatible avec Tkinter

---

## 20. Documentation, automatisation et Skill

Le projet devra prévoir une documentation suffisamment claire pour permettre :

* une prise en main rapide par un utilisateur humain
* une exploitation simple du mode CLI
* une intégration future dans des workflows automatisés
* la création d’un **Skill** dédié pour agent IA si nécessaire

### Documentation attendue

* guide d’installation
* guide de lancement GUI
* guide de lancement CLI
* exemples de commandes
* exemples de sorties JSON
* description des principales entités métier
* description des fichiers de configuration
* description des limitations connues

### Préparation Skill / agent

L’application devra être pensée pour être pilotable par un agent via CLI, avec :

* commandes déterministes
* sorties structurées
* erreurs explicites
* documentation orientée automatisation
* exemples d’appels reproductibles

### Livrable recommandé complémentaire

* un dossier ou fichier de spécification pour un futur **Skill** décrivant les commandes disponibles, les entrées, les sorties et les cas d’usage

---

## 21. Fonctions complémentaires recommandées

### Import / export

* export de configuration
* import de configuration
* export d’historique
* sauvegarde de jeux de tests

### Bibliothèque de prompts de test

Prévoir des prompts standards :

* résumé
* extraction JSON
* traduction
* classification
* génération image
* transcription audio

### Sandbox / mock

Prévoir un mode de démonstration avec :

* provider mock
* modèles fictifs
* réponses simulées

### Gestion des quotas et coûts

Quand disponible, tracer :

* coût input/output
* devise
* limites RPM/TPM
* quota connu
* estimation de coût par test

### Gestion des favoris

* favoris
* modèles stables
* modèles économiques
* premium
* à éviter

### Queue de tests

Prévoir à terme la possibilité de préparer plusieurs tests puis de les lancer en série.

---

## 22. Compatibilité et stratégie d’intégration API

Les providers ayant des API hétérogènes, l’application devra adopter :

* une couche d’abstraction commune
* des adaptateurs spécifiques par provider
* éventuellement un adaptateur **OpenAI-like** générique pour les APIs compatibles

Les écarts entre APIs devront être **normalisés côté application**.

---

## 23. MVP recommandé

### Périmètre MVP

* gestion des providers
* gestion multi-credentials
* gestion des modèles
* test texte
* structure prête pour image, audio, vidéo et autres modalités
* historique local
* notation simple
* persistance SQLite
* interface Tkinter de base

### V2

* image et audio complets
* OAuth/qauth enrichi
* comparaison multi-run
* import/export
* coûts estimés
* logs avancés

### V3

* benchmark automatisé
* statistiques avancées
* dashboard enrichi
* chiffrement local des secrets
* système de plugins providers

---

## 24. Livrables attendus

Le projet devra inclure :

1. l’arborescence du projet
2. le code source complet initial
3. les fichiers de configuration nécessaires
4. un `requirements.txt`
5. un `README.md`
6. une documentation d’usage GUI
7. une documentation d’usage CLI
8. une documentation technique minimale de l’architecture
9. des données d’exemple si utile
10. un plan d’évolution
11. une base de documentation permettant la création d’un **Skill** ou d’une intégration pilotable par agent

---

## 25. Critères de réussite

Le projet sera considéré comme satisfaisant si :

* l’application se lance simplement
* l’application fonctionne en mode GUI et en mode CLI
* plusieurs providers peuvent être configurés
* plusieurs comptes par provider sont gérables
* OAuth/qauth est prévu proprement dans l’architecture
* les modèles sont stockables et modifiables, y compris avec des types vidéo ou autres modalités si supportées
* des tests texte peuvent être lancés depuis l’interface GUI et depuis la CLI
* l’historique et les notes sont sauvegardés
* la documentation de la CLI et la préparation d’un Skill sont prévues
* l’architecture est propre et extensible
* les limitations éventuelles sont clairement identifiées

---

## 26. Hypothèses et limites acceptables

* certains providers pourront être intégrés initialement de façon partielle
* certaines modalités avancées comme la vidéo ou d’autres capacités spécifiques pourront être disponibles uniquement pour certains providers
* certains flows OAuth réels pourront être préparés sans implémentation complète immédiate
* certaines métadonnées modèles/capacités/coûts pourront être saisies manuellement si l’API ne les expose pas
* l’objectif premier est d’obtenir une **base sérieuse, exploitable et extensible**, pas un produit final figé

---

## 27. Résumé exécutif

L’application attendue est un **outil desktop Python/Tkinter de pilotage et de test de providers IA**, pensé comme une base professionnelle pour :

* configurer plusieurs fournisseurs
* gérer plusieurs abonnements
* tester plusieurs modèles
* comparer les résultats
* conserver un historique exploitable
* noter la qualité, la vitesse, le coût et la stabilité

Le projet doit être **pragmatique, modulaire, robuste et évolutif**.
