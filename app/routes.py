from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
import os
import base64
import json
from .utils import (
    extract_text_from_pdf,
    generate_latex_section,
    analyze_objectives,
    analyze_activities,
    analyze_exercises,
    analyze_lexicon,
    is_valid_pdf, create_overleaf_link, save_latex_file, init_gemini
)

bp = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/config')
def config():
    return render_template('config.html')

@bp.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """Gérer la configuration de l'API."""
    if request.method == 'POST':
        data = request.get_json()
        api_key = data.get('apiKey')
        
        if not api_key:
            return jsonify({'error': 'Clé API manquante'}), 400
            
        # Stocker la clé API dans une variable d'environnement
        os.environ['GEMINI_API_KEY'] = api_key
        
        # Réinitialiser le modèle Gemini avec la nouvelle clé
        try:
            init_gemini()
            return jsonify({'message': 'Configuration mise à jour avec succès'})
        except Exception as e:
            return jsonify({'error': f'Erreur lors de la configuration: {str(e)}'}), 400
            
    # GET: Vérifier si la clé API est configurée
    api_key_configured = 'GEMINI_API_KEY' in os.environ
    return jsonify({'configured': api_key_configured})

@bp.route('/api/upload', methods=['POST'])
def upload_file():
    """Gérer l'upload de fichier PDF."""
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400

    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Le fichier doit être un PDF'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    if not is_valid_pdf(filepath):
        os.remove(filepath)
        return jsonify({'error': 'Le fichier n\'est pas un PDF valide'}), 400

    try:
        text = extract_text_from_pdf(filepath)
        os.remove(filepath)  # Nettoyer le fichier après extraction
        return jsonify({'text': text})
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': f'Erreur lors de l\'extraction du texte: {str(e)}'}), 500

@bp.route('/api/analyze', methods=['POST'])
def api_analyze():
    """Analyser le texte avec l'API Gemini."""
    if 'GEMINI_API_KEY' not in os.environ:
        return jsonify({'error': 'Clé API non configurée. Veuillez configurer votre clé API dans les paramètres.'}), 400

    data = request.get_json()
    if not data or 'text' not in data or 'type' not in data:
        return jsonify({'error': 'Données manquantes'}), 400

    text = data['text']
    analysis_type = data['type']

    try:
        if analysis_type == 'objectifs':
            result = analyze_objectives(text)
        elif analysis_type == 'activites':
            result = analyze_activities(text)
        elif analysis_type == 'exercices':
            result = analyze_exercises(text)
        elif analysis_type == 'lexique':
            result = analyze_lexicon(text)
        else:
            return jsonify({'error': 'Type d\'analyse invalide'}), 400

        # Créer le lien Overleaf
        overleaf_link = create_overleaf_link(result)
        
        return jsonify({
            'result': result,
            'overleaf_link': overleaf_link
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/save', methods=['POST'])
def api_save_result():
    """Sauvegarder le résultat en fichier LaTeX."""
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Contenu manquant'}), 400

    try:
        filepath = save_latex_file(
            data['content'],
            data.get('filename', 'analyse'),
            current_app.config['GENERATED_FOLDER']
        )
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la sauvegarde: {str(e)}'}), 500

@bp.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier n\'a été envoyé'}), 400

        file = request.files['file']
        action = request.form.get('action', 'objectifs')  # Par défaut, analyse des objectifs

        if file.filename == '':
            return jsonify({'error': 'Aucun fichier n\'a été sélectionné'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Type de fichier non autorisé. Seuls les fichiers PDF sont acceptés'}), 400

        if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
            os.makedirs(current_app.config['UPLOAD_FOLDER'])

        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            text = extract_text_from_pdf(filepath)
            
            # Sélectionner la fonction d'analyse appropriée
            analysis_functions = {
                'objectifs': analyze_objectives,
                'activites': analyze_activities,
                'exercices': analyze_exercises,
                'lexique': analyze_lexicon
            }
            
            if action not in analysis_functions:
                raise ValueError(f"Action d'analyse non reconnue: {action}")
            
            # Effectuer l'analyse
            analysis_result = analysis_functions[action](text)
            
            # Générer le document LaTeX complet
            latex_content = generate_latex_section(analysis_result, action)
            
            # Encoder le contenu LaTeX en base64
            latex_base64 = base64.b64encode(latex_content.encode('utf-8')).decode('utf-8')
            
            return jsonify({
                'result': latex_content,
                'status': 'success',
                'latex_base64': latex_base64
            })

        except Exception as e:
            return jsonify({'error': f'Erreur lors de l\'analyse: {str(e)}'}), 500
        
        finally:
            # Nettoyer le fichier temporaire
            try:
                os.remove(filepath)
            except:
                current_app.logger.warning(f"Impossible de supprimer le fichier temporaire: {filepath}")

    except Exception as e:
        return jsonify({'error': f'Erreur lors du traitement: {str(e)}'}), 500

@bp.route('/save-api-key', methods=['POST'])
def save_api_key():
    try:
        api_key = request.form.get('api_key')
        if not api_key:
            return jsonify({'error': 'Clé API manquante'}), 400

        # Sauvegarder la clé API de manière sécurisée
        # TODO: Implémenter le stockage sécurisé de la clé API
        
        return jsonify({
            'message': 'Clé API sauvegardée avec succès',
            'status': 'success'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/prompts', methods=['GET', 'POST'])
def manage_prompts():
    if request.method == 'GET':
        # Retourner les prompts par défaut
        default_prompts = {
            'objectifs': {
                'title': 'Analyse des Objectifs',
                'description': 'Extraire et structurer les objectifs pédagogiques',
                'prompt': 'Analyser les objectifs d\'apprentissage dans le texte suivant...'
            },
            'activites': {
                'title': 'Analyse des Activités',
                'description': 'Identifier et organiser les activités pédagogiques',
                'prompt': 'Identifier les activités pédagogiques dans le texte suivant...'
            },
            'exercices': {
                'title': 'Analyse des Exercices',
                'description': 'Extraire et structurer les exercices',
                'prompt': 'Analyser les exercices et problèmes dans le texte suivant...'
            },
            'lexique': {
                'title': 'Analyse du Lexique',
                'description': 'Extraire les termes importants et leurs définitions',
                'prompt': 'Identifier les termes techniques et leurs définitions dans le texte suivant...'
            }
        }
        return jsonify(default_prompts)

    elif request.method == 'POST':
        try:
            prompts = request.json
            # TODO: Valider et sauvegarder les prompts
            return jsonify({
                'message': 'Prompts sauvegardés avec succès',
                'status': 'success'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
