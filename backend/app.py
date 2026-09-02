import json
import io
import os
import uuid

from flask import Flask, request, send_file, jsonify, session, render_template
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

app = Flask(__name__)
app.secret_key = 'une_cle_secrete_tres_complexe_pour_les_sessions'
RP_ID = "projetdocuyanisnathan.fr"
ORIGIN = "https://projetdocuyanisnathan.fr"


# ---------------------------------------------------------------------------
# Connexion à la base de données MySQL
# ---------------------------------------------------------------------------
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'db'),
        user=os.environ.get('DB_USER', 'klx_user'),
        password=os.environ.get('DB_PASSWORD', 'klx_password'),
        database=os.environ.get('DB_NAME', 'klx_doc_db')
    )


# ---------------------------------------------------------------------------
# Page d'accueil
# ---------------------------------------------------------------------------
@app.route('/')
def accueil():
    return """
    <h1>Bienvenue sur l'IHM du Banc KLX</h1>
    <ul>
        <li><a href="/admin/creer-apprenti">Espace Formateur : Créer un accès Apprenti</a></li>
        <li><a href="/login">Espace Apprenti : Se connecter</a></li>
    </ul>
    """


# ---------------------------------------------------------------------------
# Espace formateur : création d'un compte apprenti + QR code d'enrôlement
# ---------------------------------------------------------------------------
@app.route('/admin/creer-apprenti', methods=['GET', 'POST'])
def creer_apprenti():
    html_form = """
    <h2>Créer un accès pour un apprenti</h2>
    <form method="POST">
        Nom de l'apprenti : <input type="text" name="username" required>
        <button type="submit">Générer le QR Code</button>
    </form>
    """

    if request.method == 'POST':
        username = request.form['username']
        token = str(uuid.uuid4())

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, role, enrollment_token) VALUES (%s, 'apprenti', %s)",
                (username, token)
            )
            conn.commit()

            lien_enrolement = f"https://{request.host}/enroll?token={token}"

            return f"""
            <h3>Compte créé pour {username} !</h3>
            <p>Demandez à l'apprenti de scanner ce QR Code ou copiez le lien ci-dessous :</p>
            <img src="/api/qrcode?data={lien_enrolement}" alt="QR Code d'enrôlement">
            <br>
            <a href="{lien_enrolement}" target="_blank">Lien direct d'enrôlement</a>
            <br><br>
            <a href="/admin/creer-apprenti">Créer un autre compte</a>
            """
        except mysql.connector.Error as err:
            return f"Erreur : Ce nom d'apprenti existe peut-être déjà. ({err})"
        finally:
            cursor.close()
            conn.close()

    return html_form


# ---------------------------------------------------------------------------
# Génération dynamique de l'image du QR Code
# ---------------------------------------------------------------------------
@app.route('/api/qrcode')
def generer_qr():
    data = request.args.get('data')
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


# ---------------------------------------------------------------------------
# WebAuthn — Enregistrement (création de la clé d'accès / Passkey)
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
            "UPDATE users SET enrollment_token = NULL WHERE id = %s",
            (user_id,)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "ok", "message": "Clé d'accès enregistrée avec succès !"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


# ---------------------------------------------------------------------------
# Page d'enrôlement (ouverte via le QR code / lien à usage unique)
# ---------------------------------------------------------------------------
@app.route('/enroll')
def enroll():
    token = request.args.get('token')
    if not token:
        return "Erreur : Aucun token fourni.", 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE enrollment_token = %s", (token,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        user_id = user[0]
        username = user[1]

        return f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Enrôlement - Banc KLX</title>
            <script src="https://unpkg.com/@github/webauthn-json/dist/browser-global/webauthn-json.browser-global.js"></script>
        </head>
        <body style="font-family: Arial; text-align: center; margin-top: 50px;">
            <h2>Bienvenue {username} !</h2>
            <p>Pour accéder à la documentation des TP sans mot de passe, vous devez créer une clé d'accès.</p>
            <button id="registerBtn" style="padding: 15px 30px; font-size: 16px;">
                🔒 Créer ma clé d'accès (Passkey)
            </button>

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
# WebAuthn — Connexion (Passkey déjà enregistrée)
# ---------------------------------------------------------------------------
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
        "SELECT credential_id, public_key, sign_count FROM passkeys WHERE user_id = %s",
        (user_id,)
    )
    passkeys = cursor.fetchall()

    if not passkeys:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Aucune clé d'accès enregistrée."}), 400

    allowed_credentials = [
        PublicKeyCredentialDescriptor(id=base64url_to_bytes(pk[0]))
        for pk in passkeys
    ]

    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=allowed_credentials,
    )

    session['challenge'] = bytes_to_base64url(options.challenge)
    session['login_user_id'] = user_id

    cursor.close()
    conn.close()
    return options_to_json(options), 200, {'Content-Type': 'application/json'}


@app.route('/api/webauthn/login/verify', methods=['POST'])
def webauthn_login_verify():
    data = request.get_json()
    username = data.get('username')
    user_id = session.get('login_user_id')

    if not user_id:
        return jsonify({"status": "error", "message": "Session expirée."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT credential_id, public_key, sign_count FROM passkeys WHERE user_id = %s",
        (user_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return jsonify({"status": "error", "message": "Clé introuvable."}), 400

    credential_id_db = row[0]
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

        session['user'] = username
        return jsonify({"status": "ok", "message": "Connexion réussie !"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


# ---------------------------------------------------------------------------
# Page de connexion (formulaire login.html)
# ---------------------------------------------------------------------------
@app.route('/login')
def login_page():
    return render_template('login.html')


# ---------------------------------------------------------------------------
# Page de documentation (accessible une fois connecté)
# ---------------------------------------------------------------------------
@app.route('/docs')
def docs_page():
    # En production, on vérifierait ici si l'utilisateur est bien connecté
    # if 'user' not in session:
    #     return redirect('/login')

    conn = get_db_connection()
    # Le paramètre dictionary=True permet de récupérer les résultats sous forme de dictionnaire
    cursor = conn.cursor(dictionary=True) 
    
    # On récupère tous les modules de la base de données
    cursor.execute("SELECT * FROM modules")
    modules = cursor.fetchall()
    
    cursor.close()
    conn.close()

    # On envoie la variable 'modules' au template HTML
    return render_template('docs.html', modules=modules)

