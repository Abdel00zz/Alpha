import os
import base64
import google.generativeai as genai
from PyPDF2 import PdfReader
import mimetypes
from flask import current_app
import logging
import json
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_gemini():
    """Initialiser le modèle Gemini."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("La clé API Gemini n'est pas configurée")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')

def extract_text_from_pdf(filepath):
    """Extraire le texte d'un fichier PDF."""
    with open(filepath, 'rb') as file:
        reader = PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text

def is_valid_pdf(file_path):
    """Check if a file is a valid PDF."""
    try:
        if not os.path.exists(file_path):
            return False
            
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type != 'application/pdf':
            return False
            
        # Double check with PyPDF2
        try:
            with open(file_path, 'rb') as f:
                PdfReader(f)
            return True
        except:
            return False
            
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du fichier PDF: {str(e)}")
        return False

def get_default_prompts():
    """Get default prompts for each section type."""
    return {
        'objectifs': {
            'title': 'Objectifs',
            'description': 'Analyse des objectifs pédagogiques',
            'prompt': """Analyze this math lesson and generate LaTeX code for the objectives section.
                    Format: \section{Objectifs}\begin{itemize}\item [Objective]\end{itemize}"""
        },
        'activites': {
            'title': 'Activités',
            'description': 'Analyse des activités et exercices résolus',
            'prompt': """Analyze this math lesson and generate LaTeX code for the activities section.
                    Format: \section{Activités}\begin{enumerate}\item [Activity]\end{enumerate}"""
        },
        'exercices': {
            'title': 'Exercices',
            'description': 'Analyse des exercices à faire',
            'prompt': """Analyze this math lesson and generate LaTeX code for the exercises section.
                    Format: \section{Exercices}\begin{enumerate}\item [Exercise]\end{enumerate}"""
        },
        'lexique': {
            'title': 'Lexique',
            'description': 'Analyse du vocabulaire mathématique',
            'prompt': """Analyze this math lesson and generate LaTeX code for the lexicon section.
                    Format: \section{Lexique}\begin{description}\item[Term] Definition\end{description}"""
        }
    }

def load_prompts():
    """Load custom prompts from config file or return defaults."""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.loads(f.read())
        return get_default_prompts()
    except Exception as e:
        logger.error(f"Erreur lors du chargement des prompts: {str(e)}")
        return get_default_prompts()

def save_prompts(prompts):
    """Save custom prompts to config file."""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des prompts: {str(e)}")
        return False

def analyze_objectives(text):
    """Analyser les objectifs pédagogiques dans le texte."""
    model = init_gemini()
    prompt = """Analysez le texte suivant et identifiez les objectifs pédagogiques.
    Structurez votre réponse en LaTeX avec les sections suivantes :
    - Objectifs généraux
    - Objectifs spécifiques
    - Compétences visées
    
    Texte à analyser :
    {text}
    """
    response = model.generate_content(prompt.format(text=text))
    return response.text

def analyze_activities(text):
    """Analyser les activités pédagogiques dans le texte."""
    model = init_gemini()
    prompt = """Analysez le texte suivant et identifiez les activités pédagogiques.
    Structurez votre réponse en LaTeX avec les sections suivantes :
    - Description de l'activité
    - Modalités de mise en œuvre
    - Ressources nécessaires
    - Durée estimée
    
    Texte à analyser :
    {text}
    """
    response = model.generate_content(prompt.format(text=text))
    return response.text

def analyze_exercises(text):
    """Analyser les exercices dans le texte."""
    model = init_gemini()
    prompt = """Analysez le texte suivant et identifiez les exercices.
    Structurez votre réponse en LaTeX avec les sections suivantes :
    - Énoncé
    - Consignes
    - Critères d'évaluation
    - Niveau de difficulté
    
    Texte à analyser :
    {text}
    """
    response = model.generate_content(prompt.format(text=text))
    return response.text

def analyze_lexicon(text):
    """Analyser le lexique dans le texte."""
    model = init_gemini()
    prompt = """Analysez le texte suivant et identifiez les termes techniques importants.
    Structurez votre réponse en LaTeX avec les sections suivantes :
    - Terme
    - Définition
    - Contexte d'utilisation
    - Exemples
    
    Texte à analyser :
    {text}
    """
    response = model.generate_content(prompt.format(text=text))
    return response.text

def generate_latex_section(content, section_type):
    """Générer une section LaTeX à partir du contenu analysé."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    template = """\\documentclass{article}
\\usepackage[utf8]{inputenc}
\\usepackage[french]{babel}
\\usepackage{hyperref}
\\usepackage{enumitem}

\\title{Analyse de Document Pédagogique}
\\author{PDF Analyzer}
\\date{\\today}

\\begin{document}
\\maketitle

\\section{%s}
\\textit{Analyse générée le %s}

%s

\\end{document}
"""
    
    titles = {
        'objectifs': 'Analyse des Objectifs Pédagogiques',
        'activites': 'Analyse des Activités Pédagogiques',
        'exercices': 'Analyse des Exercices',
        'lexique': 'Analyse du Lexique'
    }
    
    return template % (
        titles.get(section_type, 'Analyse'),
        timestamp,
        content
    )

def create_overleaf_base64(latex_content):
    """Create a base64 encoded URL for Overleaf."""
    try:
        if not latex_content:
            raise ValueError("Le contenu LaTeX est vide")
            
        latex_bytes = latex_content.encode('utf-8')
        base64_latex = base64.b64encode(latex_bytes).decode('utf-8')
        return f"data:application/x-tex;base64,{base64_latex}"
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'URL Overleaf: {str(e)}")
        raise ValueError(f"Erreur lors de la création de l'URL Overleaf: {str(e)}")

def create_overleaf_link(latex_content):
    """Créer un lien vers Overleaf avec le contenu LaTeX."""
    base_url = "https://www.overleaf.com/docs"
    template = """\\documentclass{article}
\\usepackage[utf8]{inputenc}
\\usepackage[french]{babel}
\\usepackage{hyperref}
\\usepackage{enumitem}

\\title{Analyse de Document Pédagogique}
\\author{PDF Analyzer}
\\date{\\today}

\\begin{document}
\\maketitle

%s

\\end{document}
"""
    full_content = template % latex_content
    encoded_content = base64.b64encode(full_content.encode('utf-8')).decode('utf-8')
    return f"{base_url}?snip={encoded_content}"

def save_latex_file(content, filename, folder):
    """Save LaTeX content to a file."""
    try:
        if not content or not filename or not folder:
            raise ValueError("Le contenu, le nom de fichier et le dossier sont requis")
            
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            
        filepath = os.path.join(folder, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return filepath
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du fichier LaTeX: {str(e)}")
        raise ValueError(f"Erreur lors de la sauvegarde du fichier LaTeX: {str(e)}")
