# 🧰 Guide de mise en place (développeurs)

> **Objectif** : permettre à n’importe quel·le dev de cloner le repo, installer les dépendances, lancer le projet Pygame et commencer à coder sous **VS Code** en quelques minutes.

---

## ✅ Prérequis

* **Python** 3.10+ (3.12 recommandé)
* **Git**
* **VS Code** + extension **Python** (Microsoft)
* (Optionnel) Extensions: *Pylance*, *Ruff* (lint), *Error Lens*

Vérifier les versions :

```bash
python --version  # ou: python3 --version / py --version (Windows)
git --version
```

---

## ⚡ TL;DR — Setup rapide

### macOS / Linux

```bash
git clone <URL_DU_REPO>
cd <NOM_DU_REPO>
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt  # sinon: pip install pygame
code .  # ouvre VS Code dans le projet
```

### Windows (PowerShell)

```powershell
git clone <URL_DU_REPO>
cd <NOM_DU_REPO>
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt  # sinon: pip install pygame
code .
```

> Si l’activation échoue sous PowerShell :

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 🗂️ Structure du projet (recommandée)

```
<NOM_DU_REPO>/
├─ src/
│  └─ main.py            # point d’entrée
├─ assets/
│  ├─ sprites/
│  └─ sounds/
├─ .vscode/
│  ├─ launch.json        # config F5
│  └─ settings.json      # réglages projet
├─ requirements.txt      # dépendances (ex: pygame)
├─ .gitignore            # ignore venv, caches, etc.
├─ README.md             # ce fichier
└─ .venv/                # environnement virtuel (non versionné)
```

---

## 🧪 Installation des dépendances

Installe toutes les libs listées (pygame, etc.) :

```bash
pip install -r requirements.txt
```


---

## ▶️ Lancer le projet

### Option A — Avec VS Code (F5)

1. **Ctrl/Cmd+Shift+P → Python: Select Interpreter** → choisir `.venv` du projet.
2. Appuyer sur **F5** (config “Run Pygame”).

Exemple de `.vscode/launch.json` :

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run Pygame",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/src/main.py",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "env": { "PYGAME_HIDE_SUPPORT_PROMPT": "1" }
    }
  ]
}
```

### Option B — En terminal

```bash
python src/main.py  # ou: python3 src/main.py / py src/main.py
```

---


## 🔀 Workflow Git minimal

1. **Cloner** : `git clone <URL_DU_REPO>`
2. **Créer une branche** : `git checkout -b feat/nom-fonctionnalite`
3. **Commit** :

   ```bash
   git add .
   git commit -m "feat: ajouter l’écran titre"
   ```
4. **Push** : `git push -u origin feat/nom-fonctionnalite`
5. **Pull Request** → review → merge vers `main`.

