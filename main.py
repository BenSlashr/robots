from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Union
import httpx
import re
import asyncio
from urllib.parse import urljoin, urlparse

app = FastAPI(title="Robots.txt Checker", description="Vérificateur de robots.txt selon les règles de Googlebot")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic
class AnalyzeRequest(BaseModel):
    url: Optional[str] = None
    content: Optional[str] = None
    user_agents: List[str]
    test_paths: List[str] = []

class RobotGroup(BaseModel):
    user_agent: str
    allow_rules: List[str]
    disallow_rules: List[str]
    sitemaps: List[str]

class TestResult(BaseModel):
    path: str
    user_agent: str
    allowed: bool
    matched_rule: Optional[str]

class Status(BaseModel):
    code: int
    message: str
    size: Optional[int] = None

class AnalyzeResponse(BaseModel):
    status: Status
    groups: List[RobotGroup]
    test_results: List[TestResult]
    warnings: List[str]

# Constantes
MAX_SIZE = 500 * 1024  # 500 KiB
MAX_REDIRECTS = 5
TIMEOUT = 30

class RobotsParser:
    def __init__(self, content: str):
        self.original_content = content
        self.content = self._preprocess_content(content)
        self.groups = []
        self.warnings = []
        self._parse()

    def _preprocess_content(self, content: str) -> str:
        """Prétraite le contenu selon les règles de Googlebot"""
        # Limiter à 500 KiB
        if len(content.encode('utf-8')) > MAX_SIZE:
            self.warnings.append(f"Fichier tronqué à {MAX_SIZE // 1024} KiB (Google ignore le reste)")
            # Trouver la position de coupure en UTF-8
            truncated = content.encode('utf-8')[:MAX_SIZE]
            try:
                content = truncated.decode('utf-8')
            except UnicodeDecodeError:
                # Couper au dernier caractère valide
                content = truncated.decode('utf-8', errors='ignore')
        
        # Remplacer les caractères invalides par �
        content = content.encode('utf-8', errors='replace').decode('utf-8')
        
        return content

    def _parse(self):
        """Parse le contenu du robots.txt"""
        lines = self.content.split('\n')
        current_group = None
        current_user_agents = []
        
        for line_num, line in enumerate(lines, 1):
            # Supprimer les commentaires
            if '#' in line:
                line = line[:line.index('#')]
            
            line = line.strip()
            if not line:
                continue
            
            # Diviser la ligne en directive et valeur
            if ':' not in line:
                self.warnings.append(f"Ligne {line_num} ignorée (format invalide): {line}")
                continue
            
            directive, value = line.split(':', 1)
            directive = directive.strip().lower()
            value = value.strip()
            
            if directive == 'user-agent':
                # Nouveau groupe
                if current_group and current_user_agents:
                    # Finaliser le groupe précédent
                    for ua in current_user_agents:
                        self.groups.append(RobotGroup(
                            user_agent=ua,
                            allow_rules=current_group['allow'][:],
                            disallow_rules=current_group['disallow'][:],
                            sitemaps=current_group['sitemaps'][:]
                        ))
                
                current_user_agents = [value]
                current_group = {
                    'allow': [],
                    'disallow': [],
                    'sitemaps': []
                }
            
            elif directive == 'allow':
                if current_group is not None:
                    current_group['allow'].append(value)
                else:
                    self.warnings.append(f"Règle Allow ignorée (pas de User-agent): {line}")
            
            elif directive == 'disallow':
                if current_group is not None:
                    current_group['disallow'].append(value)
                else:
                    self.warnings.append(f"Règle Disallow ignorée (pas de User-agent): {line}")
            
            elif directive == 'sitemap':
                if current_group is not None:
                    current_group['sitemaps'].append(value)
                else:
                    # Les sitemaps peuvent être globales
                    if not current_group:
                        current_group = {'allow': [], 'disallow': [], 'sitemaps': []}
                        current_user_agents = ['*']
                    current_group['sitemaps'].append(value)
            
            elif directive in ['crawl-delay', 'noindex', 'host', 'clean-param']:
                self.warnings.append(f"Directive ignorée par Google: {directive}")
            
            else:
                self.warnings.append(f"Directive inconnue: {directive}")
        
        # Finaliser le dernier groupe
        if current_group and current_user_agents:
            for ua in current_user_agents:
                self.groups.append(RobotGroup(
                    user_agent=ua,
                    allow_rules=current_group['allow'][:],
                    disallow_rules=current_group['disallow'][:],
                    sitemaps=current_group['sitemaps'][:]
                ))
        
        # Vérifications
        if not any(group.user_agent == '*' for group in self.groups):
            self.warnings.append("Aucun groupe User-agent: * trouvé (recommandé)")

    def _match_user_agent(self, user_agent: str) -> Optional[RobotGroup]:
        """Trouve le groupe le plus spécifique pour un user-agent"""
        user_agent_lower = user_agent.lower()
        
        # 1. Correspondance exacte
        for group in self.groups:
            if group.user_agent.lower() == user_agent_lower:
                return group
        
        # 2. Correspondance par préfixe
        best_match = None
        best_length = 0
        
        for group in self.groups:
            group_ua = group.user_agent.lower()
            if group_ua != '*' and user_agent_lower.startswith(group_ua):
                if len(group_ua) > best_length:
                    best_match = group
                    best_length = len(group_ua)
        
        if best_match:
            return best_match
        
        # 3. Joker *
        for group in self.groups:
            if group.user_agent == '*':
                return group
        
        return None

    def _match_path(self, path: str, pattern: str) -> bool:
        """Vérifie si un chemin correspond à un motif robots.txt"""
        if not pattern:
            return True
        
        # Échapper les caractères spéciaux regex sauf * et $
        escaped_pattern = re.escape(pattern)
        
        # Remplacer les \* par .* (n'importe quel nombre de caractères)
        escaped_pattern = escaped_pattern.replace(r'\*', '.*')
        
        # Gérer l'ancrage de fin avec $
        if pattern.endswith('$'):
            escaped_pattern = escaped_pattern[:-2] + '$'  # Supprimer \$ et ajouter $
        else:
            # Si pas d'ancrage $, la correspondance peut être partielle
            if not escaped_pattern.endswith('.*'):
                escaped_pattern += '.*'
        
        try:
            return bool(re.match(escaped_pattern, path))
        except re.error:
            return False

    def is_allowed(self, user_agent: str, path: str) -> tuple[bool, Optional[str]]:
        """Détermine si un chemin est autorisé pour un user-agent"""
        group = self._match_user_agent(user_agent)
        
        if not group:
            # Pas de règles = tout autorisé
            return True, None
        
        # Collecter toutes les règles qui correspondent
        matching_allow = []
        matching_disallow = []
        
        for rule in group.allow_rules:
            if self._match_path(path, rule):
                matching_allow.append(rule)
        
        for rule in group.disallow_rules:
            if self._match_path(path, rule):
                matching_disallow.append(rule)
        
        # Trouver la règle la plus longue
        all_matches = []
        for rule in matching_allow:
            all_matches.append((len(rule), 'allow', rule))
        for rule in matching_disallow:
            all_matches.append((len(rule), 'disallow', rule))
        
        if not all_matches:
            return True, None
        
        # Trier par longueur décroissante
        all_matches.sort(reverse=True)
        
        # En cas d'égalité, Allow l'emporte
        best_length = all_matches[0][0]
        best_matches = [match for match in all_matches if match[0] == best_length]
        
        # Chercher Allow en priorité
        for length, rule_type, rule in best_matches:
            if rule_type == 'allow':
                return True, f"Allow: {rule}"
        
        # Sinon prendre Disallow
        for length, rule_type, rule in best_matches:
            if rule_type == 'disallow':
                return False, f"Disallow: {rule}"
        
        return True, None

async def fetch_robots_txt(url: str) -> tuple[str, int, str]:
    """Récupère le contenu du robots.txt depuis une URL"""
    parsed_url = urlparse(url)
    if not parsed_url.netloc:
        raise HTTPException(status_code=400, detail="URL invalide")
    
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        try:
            response = await client.get(robots_url)
            
            # Vérifier la taille
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > MAX_SIZE:
                return "", 413, f"Fichier trop volumineux ({content_length} bytes > {MAX_SIZE})"
            
            content = response.text
            if len(content.encode('utf-8')) > MAX_SIZE:
                return "", 413, f"Contenu trop volumineux"
            
            return content, response.status_code, response.reason_phrase or "OK"
            
        except httpx.TimeoutException:
            return "", 408, "Timeout lors de la récupération"
        except httpx.RequestError as e:
            return "", 500, f"Erreur de réseau: {str(e)}"

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_robots(request: AnalyzeRequest):
    """Analyse un fichier robots.txt"""
    
    if not request.url and not request.content:
        raise HTTPException(status_code=400, detail="URL ou contenu requis")
    
    if request.url and request.content:
        raise HTTPException(status_code=400, detail="URL et contenu mutuellement exclusifs")
    
    # Récupération du contenu
    if request.url:
        content, status_code, status_message = await fetch_robots_txt(request.url)
        if status_code != 200:
            # Traiter les erreurs selon les règles de Googlebot
            if status_code >= 400:
                # 4xx/5xx = tout autorisé
                return AnalyzeResponse(
                    status=Status(code=status_code, message=status_message),
                    groups=[],
                    test_results=[
                        TestResult(
                            path=path,
                            user_agent=ua,
                            allowed=True,
                            matched_rule="Fichier inaccessible - tout autorisé"
                        )
                        for path in request.test_paths
                        for ua in request.user_agents
                    ],
                    warnings=[f"Fichier robots.txt inaccessible (code {status_code}). Google autorise tout."]
                )
    else:
        content = request.content
        status_code = 200
        status_message = "Contenu fourni directement"
    
    # Parser le robots.txt
    parser = RobotsParser(content)
    
    # Tests des chemins
    test_results = []
    for path in request.test_paths:
        for user_agent in request.user_agents:
            allowed, matched_rule = parser.is_allowed(user_agent, path)
            test_results.append(TestResult(
                path=path,
                user_agent=user_agent,
                allowed=allowed,
                matched_rule=matched_rule
            ))
    
    return AnalyzeResponse(
        status=Status(
            code=status_code,
            message=status_message,
            size=len(content.encode('utf-8')) if content else 0
        ),
        groups=parser.groups,
        test_results=test_results,
        warnings=parser.warnings
    )

@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    return {"message": "Robots.txt Checker API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 