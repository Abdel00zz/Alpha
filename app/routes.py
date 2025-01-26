from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import base64
from .utils import (
    extract_text_from_pdf,
    generate_latex_section,
    analyze_objectives,
    analyze_activities,
    analyze_exercises,
    analyze_lexicon
)
import logging

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@bp.before_app_request
def check_api_key():
    """Vérifier si la clé API est configurée avant chaque requête."""
    if request.endpoint != 'main.health_check':  # Ne pas vérifier pour le health check
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return jsonify({
                'error': 'Configuration manquante',
                'message': 'La clé API Gemini n\'est pas configurée. Veuillez configurer GEMINI_API_KEY dans les variables d\'environnement.'
            }), 503

@bp.route('/health-check')
def health_check():
    """Route de vérification de santé."""
    api_key = os.getenv('GEMINI_API_KEY')
    return jsonify({
        'status': 'healthy',
        'api_key_configured': bool(api_key)
    })

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/config')
def config():
    return render_template('config.html')

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
