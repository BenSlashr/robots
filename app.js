// Configuration de l'API
const API_BASE_URL = 'http://localhost:8000';

// Éléments du DOM
const form = document.getElementById('robotsForm');
const siteUrlInput = document.getElementById('siteUrl');
const robotsContentTextarea = document.getElementById('robotsContent');
const userAgentsSelect = document.getElementById('userAgents');
const testPathsTextarea = document.getElementById('testPaths');
const resultsSection = document.getElementById('resultsSection');

// Gestion de l'exclusion mutuelle entre URL et contenu
siteUrlInput.addEventListener('input', function() {
    if (this.value.trim()) {
        robotsContentTextarea.disabled = true;
        robotsContentTextarea.classList.add('bg-gray-700', 'cursor-not-allowed');
    } else {
        robotsContentTextarea.disabled = false;
        robotsContentTextarea.classList.remove('bg-gray-700', 'cursor-not-allowed');
    }
});

robotsContentTextarea.addEventListener('input', function() {
    if (this.value.trim()) {
        siteUrlInput.disabled = true;
        siteUrlInput.classList.add('bg-gray-700', 'cursor-not-allowed');
    } else {
        siteUrlInput.disabled = false;
        siteUrlInput.classList.remove('bg-gray-700', 'cursor-not-allowed');
    }
});

// Auto-complétion pour l'URL
siteUrlInput.addEventListener('blur', function() {
    const url = this.value.trim();
    if (url && !url.includes('/robots.txt')) {
        // Ajouter /robots.txt si pas déjà présent
        if (url.endsWith('/')) {
            this.value = url + 'robots.txt';
        } else {
            this.value = url + '/robots.txt';
        }
    }
});

// Gestion de la soumission du formulaire
form.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(form);
    const siteUrl = formData.get('siteUrl');
    const robotsContent = formData.get('robotsContent');
    const testPaths = formData.get('testPaths');
    
    // Validation
    if (!siteUrl && !robotsContent) {
        showError('Veuillez fournir soit une URL soit le contenu du robots.txt');
        return;
    }
    
    // Récupération des user-agents sélectionnés
    const selectedUserAgents = Array.from(userAgentsSelect.selectedOptions).map(option => option.value);
    if (selectedUserAgents.length === 0) {
        showError('Veuillez sélectionner au moins un User-Agent');
        return;
    }
    
    // Préparation des données pour l'API
    const requestData = {
        user_agents: selectedUserAgents,
        test_paths: testPaths ? testPaths.split('\n').filter(path => path.trim()) : []
    };
    
    if (siteUrl) {
        requestData.url = siteUrl;
    } else {
        requestData.content = robotsContent;
    }
    
    // Affichage du loader
    showLoader();
    
    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        const result = await response.json();
        displayResults(result);
        
    } catch (error) {
        console.error('Erreur lors de l\'analyse:', error);
        showError(`Erreur lors de l'analyse: ${error.message}`);
    }
});

function showLoader() {
    resultsSection.innerHTML = `
        <div class="text-center py-12">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p class="mt-4 text-gray-300">Analyse en cours...</p>
        </div>
    `;
    resultsSection.classList.remove('hidden');
}

function showError(message) {
    resultsSection.innerHTML = `
        <div class="bg-red-600 border border-red-500 rounded-lg p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-300" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-red-300">Erreur</h3>
                    <div class="mt-2 text-sm text-red-200">${message}</div>
                </div>
            </div>
        </div>
    `;
    resultsSection.classList.remove('hidden');
}

function displayResults(result) {
    let html = `
        <h2 class="text-2xl font-semibold mb-6 flex items-center">
            <div class="w-1 h-6 bg-gradient-to-r from-blue-500 to-green-500 rounded mr-3"></div>
            Résultats
        </h2>
    `;
    
    // Section Résultats des tests - Avec plus de détails (EN PREMIER)
    if (result.test_results && result.test_results.length > 0) {
        html += `
            <div class="mb-6">
                <h3 class="text-lg font-medium mb-3">Résultats des tests de chemins</h3>
                <div class="overflow-x-auto">
                    <table class="min-w-full bg-gray-800 rounded-lg">
                        <thead class="bg-gray-700">
                            <tr>
                                <th class="px-4 py-3 text-left text-sm font-medium text-gray-300">Chemin testé</th>
                                <th class="px-4 py-3 text-left text-sm font-medium text-gray-300">User-Agent</th>
                                <th class="px-4 py-3 text-left text-sm font-medium text-gray-300">Résultat</th>
                                <th class="px-4 py-3 text-left text-sm font-medium text-gray-300">Règle appliquée</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-700">
                            ${result.test_results.map(test => `
                                <tr class="${test.allowed ? 'bg-gray-800' : 'bg-red-900/20'}">
                                    <td class="px-4 py-3 text-sm font-mono text-white">${test.path}</td>
                                    <td class="px-4 py-3 text-sm font-mono text-gray-300">${test.user_agent}</td>
                                    <td class="px-4 py-3 text-sm">
                                        <span class="inline-flex px-3 py-1 text-xs font-semibold rounded-full ${
                                            test.allowed ? 'bg-green-600 text-green-100' : 'bg-red-600 text-red-100'
                                        }">
                                            ${test.allowed ? '✓ AUTORISÉ' : '✗ BLOQUÉ'}
                                        </span>
                                    </td>
                                    <td class="px-4 py-3 text-sm">
                                        ${test.matched_rule ? 
                                            `<code class="text-xs bg-gray-700 px-2 py-1 rounded ${test.allowed ? 'text-green-400' : 'text-red-400'}">${test.matched_rule}</code>` : 
                                            '<span class="text-gray-500 text-xs">Aucune règle spécifique</span>'
                                        }
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                <div class="mt-3 text-xs text-gray-400">
                    💡 Les chemins bloqués apparaissent avec un fond rouge. La règle exacte qui s'applique est indiquée.
                </div>
            </div>
        `;
    }
    
    // Section Statut
    html += `
        <div class="mb-6">
            <h3 class="text-lg font-medium mb-3">Statut</h3>
            <div class="bg-gray-800 rounded-lg p-4">
                <div class="flex items-center space-x-3">
                    <div class="w-3 h-3 rounded-full ${getStatusColor(result.status.code)}"></div>
                    <span class="font-medium">Code: ${result.status.code}</span>
                    <span class="text-gray-400">${result.status.message}</span>
                </div>
                ${result.status.size ? `<p class="mt-2 text-sm text-gray-400">Taille: ${result.status.size} caractères</p>` : ''}
            </div>
        </div>
    `;
    
    // Section Groupes - Version simplifiée
    if (result.groups && result.groups.length > 0) {
        html += `
            <div class="mb-6">
                <h3 class="text-lg font-medium mb-3">Groupes User-Agent détectés</h3>
                <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    ${result.groups.map(group => `
                        <div class="bg-gray-800 rounded-lg p-4">
                            <h4 class="font-mono text-blue-400 font-medium mb-2">${group.user_agent}</h4>
                            <div class="text-sm text-gray-300 space-y-1">
                                <div>
                                    <span class="text-green-400">Allow:</span> 
                                    ${group.allow_rules.length > 0 ? `${group.allow_rules.length} règle(s)` : 'Aucune'}
                                </div>
                                <div>
                                    <span class="text-red-400">Disallow:</span> 
                                    ${group.disallow_rules.length > 0 ? `${group.disallow_rules.length} règle(s)` : 'Aucune'}
                                </div>
                                ${group.sitemaps.length > 0 ? `
                                    <div>
                                        <span class="text-blue-400">Sitemaps:</span> ${group.sitemaps.length}
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Section Avertissements
    if (result.warnings && result.warnings.length > 0) {
        html += `
            <div class="mb-6">
                <h3 class="text-lg font-medium mb-3">Avertissements</h3>
                <div class="space-y-2">
                    ${result.warnings.map(warning => `
                        <div class="bg-yellow-600 border border-yellow-500 rounded-lg p-3">
                            <div class="flex">
                                <svg class="h-5 w-5 text-yellow-300 mt-0.5 mr-3" viewBox="0 0 20 20" fill="currentColor">
                                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                                </svg>
                                <span class="text-yellow-100">${warning}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    resultsSection.innerHTML = html;
    resultsSection.classList.remove('hidden');
}

function getStatusColor(code) {
    if (code >= 200 && code < 300) {
        return 'bg-green-500';
    } else if (code >= 400 && code < 500) {
        return 'bg-yellow-500';
    } else if (code >= 500) {
        return 'bg-red-500';
    }
    return 'bg-gray-500';
} 