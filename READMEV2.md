Markdown
# 🚀 Système d'Information et de Documentation - Banc KLX

[![Statut](https://img.shields.io/badge/Statut-En%20D%C3%A9veloppement-orange)](#)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue)](#)
[![License](https://img.shields.io/badge/License-Propri%C3%A9taire-red)](#)

## 📖 À propos du projet

Ce projet consiste à concevoir et déployer une plateforme de documentation technique centralisée et sécurisée pour les travaux pratiques (TP) réalisés sur les **bancs KLX**. 

L'objectif principal est de fournir une **Interface Homme-Machine (IHM) web fluide et hautement sécurisée**, permettant aux apprentis d'accéder instantanément à la documentation d'un module assigné, sans jamais avoir besoin de retenir un mot de passe, grâce à une authentification moderne par clé d'accès (Passkey/WebAuthn).

## ✨ Fonctionnalités Principales

* **Gestion Documentaire Centralisée :** Base de données liant chaque module physique du banc KLX à sa documentation technique (PDF, guides, schémas) et son illustration visuelle.
* **Suivi Pédagogique :** Interface d'ajout de modules incluant une section de commentaires dédiée aux formateurs pour laisser des consignes spécifiques.
* **Authentification "Passwordless" :** 
  * Création du profil par l'Administrateur/Formateur.
  * Génération d'une URL sécurisée avec token à usage unique affichée sous forme de **QR Code**.
  * Scan du QR Code par l'apprenti et enregistrement d'une clé d'accès (biométrie, code PIN de l'appareil, clé physique).
  * Connexions ultérieures instantanées et sécurisées (anti-phishing).
* **Administration :** Panneau dédié aux formateurs pour la gestion des apprentis, des modules et des ressources documentaires (supportant des fichiers jusqu'à 50 Mo).
* **Déploiement Isolé :** Conçu pour fonctionner sur un réseau physique dédié (Serveur, Routeur, Switch) garantissant un environnement cloisonné pour les TP.

## 🛠️ Stack Technique

* **Serveur Web & Proxy :** Nginx
* **Backend :** Python (Flask)
* **Frontend :** HTML / CSS / JavaScript
* **Base de Données :** MySQL
* **Infrastructure :** Docker & Docker Compose
* **Sécurité :** WebAuthn / Passkeys & Certificats SSL/TLS

## 🏗️ Architecture du Système

Le projet repose sur une architecture micro-services gérée par **Docker** :
- `proxy` (Nginx) : Gère le trafic entrant, le chiffrement HTTPS et l'autorisation des uploads de fichiers volumineux.
- `web` (Flask) : Conteneur hébergeant l'API (logique WebAuthn, gestion des modules, distribution de l'IHM).
- `db` (MySQL) : Conteneur de base de données pour stocker les utilisateurs, les modules, les commentaires formateurs et les métadonnées documentaires.

## 🚀 Installation & Déploiement

### Prérequis
* Un serveur hôte configuré sur le réseau local (LAN TP).
* Docker et Docker Compose installés sur le serveur.
* Équipements réseaux (Routeur, Switch) interconnectant le serveur et les postes des bancs KLX.

### Lancement

1. Clonez ce dépôt :
   ```bash
   git clone [https://github.com/votre-nom-utilisateur/projet-banc-klx.git](https://github.com/votre-nom-utilisateur/projet-banc-klx.git)
   cd projet-banc-klx
Lancez les conteneurs (en arrière-plan) en forçant la construction :

Bash
sudo docker compose up -d --build
Accédez à l'application :
Ouvrez un navigateur sur un poste du réseau local et pointez vers le domaine configuré (ex: https://projetdocuyanisnathan.fr).

📂 Structure du Répertoire
Plaintext
├── docker-compose.yml     # Orchestration des conteneurs (Nginx + Flask + MySQL)
├── /nginx                 # Configuration du reverse proxy et certificats SSL
├── /backend               # Code source de l'IHM et du serveur (app.py, templates HTML)
│   ├── Dockerfile
│   └── ...
├── /database              # Scripts d'initialisation de la BDD (init.sql)
├── /docs                  # Documentation annexe, Cahier des Charges, Rapport global
└── README.md              # Présentation du projet (ce fichier)
📈 Gestion de Projet & Traçabilité
Les commits sur ce dépôt sont lissés dans le temps pour assurer une traçabilité claire du développement.

Le code est documenté (PEP 8) et structuré.

Un rapport global du projet (synthétisant les besoins, l'organisation, la réalisation et la rétrospective) sera inclus dans le dossier /docs pour la revue finale.

👥 Contributeurs
Nathan Bussolaro - Développement, Réseau, et Sécurité (BTS CIEL)
