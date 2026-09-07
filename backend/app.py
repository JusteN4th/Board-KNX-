import json
import io
import os
import uuid
from functools import wraps

from flask import Flask, request, send_file, jsonify, session, render_template, redirect
import mysql.connector
import qrcode
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)
from webauthn.helpers import bytes_to_base64url, base64url_to_bytes
from webauthn.helpers.structs import PublicKeyCredentialDescriptor
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'une_cle_secrete_tres_complexe_pour_les_sessions'
RP_ID = "projetdocuyanisnathan.fr"
ORIGIN = "https://projetdocuyanisnathan.fr"

# ---------------------------------------------------------------------------
# Connexion à la base de données MySQL (avec encodage UTF-8 forcé)
# ---------------------------------------------------------------------------


def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'db'),
        user=os.environ.get('DB_USER', 'klx_user'),
        password=os.environ.get('DB_PASSWORD', 'klx_password'),
        database=os.environ.get('DB_NAME', 'klx_doc_db'),
        charset='utf8mb4',
        use_unicode=True
    )

# ---------------------------------------------------------------------------
# Helpers de sécurité
# ---------------------------------------------------------------------------


def require_login(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get('user'):
            return redirect('/login')
        return view_func(*args, **kwargs)
    return wrapped


def require_admin(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect('/admin')
        return view_func(*args, **kwargs)
    return wrapped

# ---------------------------------------------------------------------------
# Page d'accueil & Déconnexion
# ---------------------------------------------------------------------------


@app.route('/')
def accueil():
    return render_template('index.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/register')
def register():
    return render_template('register.html')

# ---------------------------------------------------------------------------
# Espace formateur : Tableau de bord principal
# ---------------------------------------------------------------------------


@app.route('/admin')
def admin_index():
    if session.get('role') == 'admin':
        return redirect('/admin/creer-apprenti')
    return render_template('admin.html')


@app.route('/admin/creer-apprenti', methods=['GET', 'POST'])
@require_admin
def creer_apprenti():
    qr_url = None
    lien_enrolement = None
    apprenti_nom = None
    error = None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        prenom = request.form.get('prenom')
        nom = request.form.get('nom')

        if prenom and nom:
            username = f"{prenom.strip().capitalize()} {nom.strip().upper()}"
            token = str(uuid.uuid4())
            try:
                cursor.execute(
                    "INSERT INTO users (username, role, enrollment_token) VALUES (%s, 'apprenti', %s)",
                    (username, token)
                )
                conn.commit()
                lien_enrolement = f"https://{request.host}/enroll?token={token}"
                apprenti_nom = username
                qr_url = f"/api/qrcode?data={lien_enrolement}"
            except mysql.connector.Error as err:
                error = f"Erreur : Ce nom d'apprenti existe peut-être déjà. ({err})"

    # Récupération des données pour le panel
    cursor.execute("SELECT id, username, role FROM users")
    users_list = cursor.fetchall()

    cursor.execute("SELECT id, name FROM classes")
    classes_list = cursor.fetchall()

    cursor.execute("SELECT id, name FROM modules")
    modules_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'admin_apprenti.html',
        error=error,
        qr_url=qr_url,
        lien_enrolement=lien_enrolement,
        apprenti_nom=apprenti_nom,
        current_user=session.get('user'),
        users=users_list,
        classes=classes_list,
        modules=modules_list
    )

# ---------------------------------------------------------------------------
# Routes de gestion du panel formateur (Classes & Utilisateurs)
# ---------------------------------------------------------------------------


@app.route('/admin/promote/<int:target_user_id>', methods=['POST'])
@require_admin
def promote_user(target_user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET role = 'admin' WHERE id = %s", (target_user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/admin/creer-apprenti')


@app.route('/admin/reset-key/<int:target_user_id>', methods=['POST'])
@require_admin
def reset_key(target_user_id):
    token = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    # On supprime l'ancienne passkey et on génère un token d'enrôlement neuf
    cursor.execute("DELETE FROM passkeys WHERE user_id = %s",
                   (target_user_id,))
    cursor.execute(
        "UPDATE users SET enrollment_token = %s WHERE id = %s", (token, target_user_id))
    conn.commit()

    cursor.execute("SELECT username FROM users WHERE id = %s",
                   (target_user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    # Redirige avec le lien d'enrôlement direct pour l'admin
    lien = f"https://{request.host}/enroll?token={token}"
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Réinitialisation - Banc KLX</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body style="background: #f4f7f6; height: 100vh; display: flex; align-items: center; justify-content: center;">
        <div class="card p-4 text-center shadow" style="border-radius: 15px; max-width: 450px;">
            <h4 class="text-success mb-3">Clé réinitialisée pour {user[0]} !</h4>
            <p class="text-muted">Voici le nouveau lien d'enrôlement à transmettre à l'utilisateur :</p>
            <input type="text" class="form-control text-center mb-3" value="{lien}" readonly onclick="this.select();">
            <a href="/admin/creer-apprenti" class="btn btn-primary rounded-pill">Retour au panel</a>
        </div>
    </body>
    </html>
    """


@app.route('/admin/class/create', methods=['POST'])
@require_admin
def create_class():
    name = request.form.get('class_name')
    if name:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO classes (name) VALUES (%s)", (name,))
            conn.commit()
        except:
            pass
        finally:
            cursor.close()
            conn.close()
    return redirect('/admin/creer-apprenti')


@app.route('/admin/class/assign', methods=['POST'])
@require_admin
def assign_class():
    user_id = request.form.get('user_id')
    class_id = request.form.get('class_id')
    if user_id and class_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO user_classes (user_id, class_id) VALUES (%s, %s)", (user_id, class_id))
            conn.commit()
        except:
            pass
        finally:
            cursor.close()
            conn.close()
    return redirect('/admin/creer-apprenti')


@app.route('/admin/module/permit', methods=['POST'])
@require_admin
def permit_module():
    module_id = request.form.get('module_id')
    target_type = request.form.get('target_type')
    target_id = request.form.get('target_id')

    if module_id and target_type and target_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if target_type == 'user':
                cursor.execute(
                    "INSERT INTO module_visibility_users (module_id, user_id) VALUES (%s, %s)", (module_id, target_id))
            elif target_type == 'class':
                cursor.execute(
                    "INSERT INTO module_visibility_classes (module_id, class_id) VALUES (%s, %s)", (module_id, target_id))
            conn.commit()
        except:
            pass
        finally:
            cursor.close()
            conn.close()
    return redirect('/admin/creer-apprenti')


@app.route('/api/qrcode')
def generer_qr():
    data = request.args.get('data')
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

# ---------------------------------------------------------------------------
# WebAuthn & Connexion
# ---------------------------------------------------------------------------


@app.route('/api/webauthn/register/options', methods=['POST'])
def webauthn_register_options():
    data = request.get_json()
    username = data.get('username')
    user_id = data.get('user_id')

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name="Doc Banc KLX",
        user_id=str(user_id).encode('utf-8'),
        user_name=username,
        user_display_name=username,
    )
    session['challenge'] = bytes_to_base64url(options.challenge)
    return options_to_json(options), 200, {'Content-Type': 'application/json'}


@app.route('/api/webauthn/register/verify', methods=['POST'])
def webauthn_register_verify():
    data = request.get_json()
    user_id = data.get('user_id')

    try:
        verification = verify_registration_response(
            credential=data['credential'],
            expected_challenge=base64url_to_bytes(session['challenge']),
            expected_rp_id=RP_ID,
            expected_origin=f"https://{request.host}",
        )
        conn = get_db_connection()
        cursor = conn.cursor()
        credential_id_b64 = bytes_to_base64url(verification.credential_id)
        public_key_b64 = bytes_to_base64url(verification.credential_public_key)

        cursor.execute(
            "INSERT INTO passkeys (user_id, credential_id, public_key, sign_count) VALUES (%s, %s, %s, %s)",
            (user_id, credential_id_b64, public_key_b64, verification.sign_count)
        )
        cursor.execute(
            "UPDATE users SET enrollment_token = NULL WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "ok", "message": "Clé d'accès enregistrée avec succès !"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/api/webauthn/login/options', methods=['POST'])
def webauthn_login_options():
    data = request.get_json()
    username = data.get('username')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Utilisateur inconnu."}), 400

    user_id = user[0]
    cursor.execute(
        "SELECT credential_id, public_key, sign_count FROM passkeys WHERE user_id = %s", (user_id,))
    passkeys = cursor.fetchall()

    if not passkeys:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Aucune clé d'accès enregistrée."}), 400

    allowed_credentials = [PublicKeyCredentialDescriptor(
        id=base64url_to_bytes(pk[0])) for pk in passkeys]
    options = generate_authentication_options(
        rp_id=RP_ID, allow_credentials=allowed_credentials)
    session['challenge'] = bytes_to_base64url(options.challenge)
    session['login_user_id'] = user_id

    cursor.close()
    conn.close()
    return options_to_json(options), 200, {'Content-Type': 'application/json'}


@app.route('/api/webauthn/login/verify', methods=['POST'])
def webauthn_login_verify():
    data = request.get_json()
    user_id = session.get('login_user_id')

    if not user_id:
        return jsonify({"status": "error", "message": "Session expirée."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT credential_id, public_key, sign_count FROM passkeys WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()

    if not row:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Clé introuvable."}), 400

    public_key_db = row[1]
    sign_count_db = row[2]

    try:
        verification = verify_authentication_response(
            credential=data['credential'],
            expected_challenge=base64url_to_bytes(session['challenge']),
            expected_rp_id=RP_ID,
            expected_origin=f"https://{request.host}",
            credential_public_key=base64url_to_bytes(public_key_db),
            credential_current_sign_count=sign_count_db,
        )
        cursor.execute(
            "SELECT username, role FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()

        if user_data:
            session['user'] = user_data[0]
            session['role'] = user_data[1]
            session['user_id'] = user_id

        cursor.close()
        conn.close()
        return jsonify({"status": "ok", "message": "Connexion réussie !"})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/enroll')
def enroll():
    token = request.args.get('token')
    if not token:
        return "Erreur : Aucun token fourni.", 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username FROM users WHERE enrollment_token = %s", (token,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        user_id = user[0]
        username = user[1]
        return f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Enrôlement - Banc KLX</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/@github/webauthn-json/dist/browser-global/webauthn-json.browser-global.js"></script>
        </head>
        <body style="background-color: #f4f7f6; height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0;">
            <div class="card text-center p-4 border-0 shadow" style="border-radius: 15px; max-width: 400px; width: 100%;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">👋</div>
                <h3 class="mb-3">Bienvenue {username} !</h3>
                <p class="text-muted mb-4">Pour accéder à la documentation des TP sans mot de passe, vous devez créer une clé d'accès sécurisée.</p>
                <button id="registerBtn" class="btn btn-success w-100 py-2 fs-5 rounded-pill">
                    🔒 Créer ma clé d'accès
                </button>
            </div>
            <script>
                document.getElementById('registerBtn').addEventListener('click', async () => {{
                    try {{
                        const optionsRes = await fetch('/api/webauthn/register/options', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{username: '{username}', user_id: {user_id}}})
                        }});
                        const options = await optionsRes.json();
                        const credential = await webauthnJSON.create({{ publicKey: options }});
                        const verifyRes = await fetch('/api/webauthn/register/verify', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{credential: credential, user_id: {user_id}}})
                        }});
                        const result = await verifyRes.json();
                        if (result.status === 'ok') {{
                            alert('Succès ! Votre clé est enregistrée. Vous allez être redirigé.');
                            window.location.href = '/docs';
                        }} else {{
                            alert('Erreur : ' + result.message);
                        }}
                    }} catch (error) {{
                        console.error(error);
                        alert("L'enregistrement a été annulé ou a échoué.");
                    }}
                }});
            </script>
        </body>
        </html>
        """
    else:
        return "Erreur : Ce lien est invalide ou a déjà été utilisé.", 403

# ---------------------------------------------------------------------------
# Gestion des modules
# ---------------------------------------------------------------------------


@app.route('/supprimer-module/<int:module_id>', methods=['POST'])
@require_admin
def supprimer_module(module_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM modules WHERE id = %s", (module_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/docs')


@app.route('/ajouter-module', methods=['POST'])
@require_admin
def ajouter_module():
    name = request.form.get('name')
    description = request.form.get('description')
    image_file = request.files.get('image')
    doc_file = request.files.get('document')
    comment = request.form.get('comment', '')

    if image_file and doc_file:
        img_filename = secure_filename(image_file.filename)
        doc_filename = secure_filename(doc_file.filename)

        img_save_path = os.path.join('static', 'img', img_filename)
        doc_save_path = os.path.join('static', 'docs', doc_filename)

        os.makedirs(os.path.dirname(img_save_path), exist_ok=True)
        os.makedirs(os.path.dirname(doc_save_path), exist_ok=True)

        image_file.save(img_save_path)
        doc_file.save(doc_save_path)

        conn = get_db_connection()
        cursor = conn.cursor()

# 1. D'abord, insérer le module avec le commentaire
        cursor.execute(
            "INSERT INTO modules (name, description, image_path, comment) VALUES (%s, %s, %s, %s)",
            (name, description, f"/static/img/{img_filename}", comment)
        )
        
        # 2. Ensuite, récupérer l'ID généré pour ce module
        module_id = cursor.lastrowid
        
        # 3. Enfin, insérer la documentation liée à cet ID
        cursor.execute(
            "INSERT INTO documentation (module_id, title, file_path) VALUES (%s, %s, %s)",
            (module_id, f"Doc {name}", f"/static/docs/{doc_filename}")
        )
    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/docs')


@app.route('/docs')
@require_login
def docs_page():
    user_id = session.get('user_id')
    role = session.get('role')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if role == 'admin':
        requete = """
            SELECT m.id, m.name, m.description, m.image_path, m.comment, d.file_path AS doc_path 
            FROM modules m 
            LEFT JOIN documentation d ON m.id = d.module_id
        """
        cursor.execute(requete)
    else:
        requete = """
            SELECT DISTINCT m.id, m.name, m.description, m.image_path, d.file_path AS doc_path 
            FROM modules m 
            LEFT JOIN documentation d ON m.id = d.module_id
            LEFT JOIN module_visibility_users mvu ON m.id = mvu.module_id
            LEFT JOIN module_visibility_classes mvc ON m.id = mvc.module_id
            LEFT JOIN user_classes uc ON mvc.class_id = uc.class_id
            WHERE mvu.user_id = %s OR uc.user_id = %s
        """
        cursor.execute(requete, (user_id, user_id))

    modules = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('docs.html', modules=modules, current_user=session.get('user'), role=role)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
