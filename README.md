# 🚀 Système d'Information et de Documentation - Banc KLX

[![Statut](https://img.shields.io/badge/Statut-En%20D%C3%A9veloppement-orange)](#)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue)](#)
[![License](https://img.shields.io/badge/License-Propri%C3%A9taire-red)](#)

## 📖 À propos du projet

Ce projet consiste à concevoir et déployer une plateforme de documentation technique centralisée et sécurisée pour les travaux pratiques (TP) réalisés sur les **bancs KLX**. 

L'objectif principal est de fournir une **Interface Homme-Machine (IHM) web fluide et hautement sécurisée**, permettant aux apprentis d'accéder instantanément à la documentation d'un module assigné, sans jamais avoir besoin de retenir un mot de passe, grâce à une authentification moderne par clé d'accès (Passkey/WebAuthn).

## ✨ Fonctionnalités Principales

* **Gestion Documentaire Centralisée :** Base de données liant chaque module physique du banc KLX à sa documentation technique (PDF, guides, schémas).
* **Authentification "Passwordless" :** 
  * Création du profil par l'Administrateur/Formateur.
  * Génération d'une URL sécurisée avec token à usage unique affichée sous forme de **QR Code**.
  * Scan du QR Code par l'apprenti et enregistrement d'une clé d'accès (biométrie, code PIN de l'appareil, clé physique).
  * Connexions ultérieures instantanées et sécurisées (anti-phishing).
* **Administration :** Panneau dédié aux formateurs pour la gestion des apprentis, des modules et des ressources documentaires.
* **Déploiement Isolé :** Conçu pour fonctionner sur un réseau physique dédié (Serveur, Routeur, Switch) garantissant un environnement cloisonné pour les TP.

## 🛠️ Stack Technique

* **Interface Web & Backend :** *[À définir : ex. Python (FastAPI/Flask) / Node.js / HTML-JS-CSS]*
* **Base de Données :** MySQL
* **Infrastructure :** Docker & Docker Compose
* **Sécurité :** WebAuthn / Passkeys
* **Réseau :** Architecture LAN spécifique (Switch, Routeur)

## 🏗️ Architecture du Système

Le projet repose sur une architecture micro-services gérée par **Docker** :
- `db` : Conteneur MySQL pour stocker les utilisateurs, les tokens d'enrôlement et les métadonnées documentaires.
- `web` : Conteneur hébergeant l'API (logique WebAuthn, distribution de l'IHM) et le serveur web.

## 🚀 Installation & Déploiement

### Prérequis
* Un serveur hôte configuré sur le réseau local (LAN TP).
* Docker et Docker Compose installés sur le serveur.
* Équipements réseaux (Routeur, Switch) interconnectant le serveur et les postes des bancs KLX.

### Lancement

1. Clonez ce dépôt :
   ```bash
   git clone https://github.com/votre-nom-utilisateur/projet-banc-klx.git
   cd projet-banc-klx
   ```

2. Lancez les conteneurs (en arrière-plan) :
   ```bash
   docker-compose up -d
   ```

3. Accédez à l'application :
   Ouvrez un navigateur sur un poste du réseau local et pointez vers l'adresse IP du serveur (ex: `http://192.168.1.100`).

## 📂 Structure du Répertoire

```text
├── docker-compose.yml     # Orchestration des conteneurs (MySQL + Serveur Web)
├── /backend               # Code source de l'IHM et du serveur (API, WebAuthn)
│   ├── Dockerfile
│   └── ...
├── /database              # Scripts d'initialisation de la BDD (init.sql)
├── /docs                  # Documentation annexe, Cahier des Charges, Rapport global
└── README.md              # Présentation du projet (ce fichier)
```

## 📈 Gestion de Projet & Traçabilité

* Les *commits* sur ce dépôt sont lissés dans le temps pour assurer une traçabilité claire du développement.
* Le code est documenté et structuré.
* Un **rapport global du projet** (synthétisant les besoins, l'organisation, la réalisation et la rétrospective) sera inclus dans le dossier `/docs` pour la revue finale.

## 👥 Contributeurs
* **[Votre Nom / Équipe]** - *Développement, Réseau, et Sécurité*
