/**
 * item-locations.js
 * Gestion des sélecteurs de localisation dans les formulaires d'articles
 * Utilise location-core.js comme bibliothèque de base
 */

document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si nous sommes sur la page d'ajout ou d'édition d'article
    const isAddEditPage = document.getElementById('itemZone') !== null || 
                      document.getElementById('editItemZone') !== null;
   
    
    if (!isAddEditPage) {
        return;
    }
    
    appLog.log('Formulaire d\'article détecté, initialisation des sélecteurs de localisation...');
    
    // Détecter si nous sommes sur le formulaire d'ajout ou d'édition
    const isEditForm = document.getElementById('editItemZone') !== null;
    const prefix = isEditForm ? 'edit' : '';
    
    // Initialiser les sélecteurs
    initLocationSelectors(prefix);
    
    // Si nous sommes sur la page d'édition, pré-sélectionner les valeurs
    if (isEditForm) {
        preSelectLocationValues();
    }
});

/**
 * Initialiser les sélecteurs de localisation
 * @param {string} prefix - Préfixe pour les sélecteurs ('' pour ajout, 'edit' pour édition)
 */
function initLocationSelectors(prefix) {
    const zoneSelector = document.getElementById(`${prefix}itemZone`);
    const furnitureSelector = document.getElementById(`${prefix}itemFurniture`);
    const drawerSelector = document.getElementById(`${prefix}itemDrawer`);
    
    if (!zoneSelector) return;
    
    // Charger les zones
    loadZones(prefix);
    
    // Configurer les écouteurs de changement
    setupSelectionListeners(prefix);
    
    // Configurer les liens d'ajout rapide
    setupAddLinks(prefix);
}

/**
 * Charger les zones dans le sélecteur
 * @param {string} prefix - Préfixe pour les sélecteurs
 */
async function loadZones(prefix) {
    const zoneSelector = document.getElementById(`${prefix}itemZone`);
    if (!zoneSelector) return;
    
    try {
        const zones = await LocationCore.fetchZones();
        LocationCore.updateSelectOptions(
            zoneSelector, 
            zones, 
            'id', 
            'name', 
            'Sélectionnez une zone'
        );
        
        // Si une zone est sélectionnée, charger les meubles correspondants
        if (zoneSelector.value) {
            loadFurniture(prefix, zoneSelector.value);
        }
    } catch (error) {
        appLog.error('Erreur lors du chargement des zones:', error);
    }
}

/**
 * Charger les meubles pour une zone spécifique
 * @param {string} prefix - Préfixe pour les sélecteurs
 * @param {number} zoneId - ID de la zone
 */
async function loadFurniture(prefix, zoneId) {
    const furnitureSelector = document.getElementById(`${prefix}itemFurniture`);
    if (!furnitureSelector) return;
    
    try {
        // Activer le sélecteur de meuble
        furnitureSelector.disabled = false;
        
        const furniture = await LocationCore.fetchFurniture(zoneId);
        LocationCore.updateSelectOptions(
            furnitureSelector, 
            furniture, 
            'id', 
            'name', 
            'Sélectionnez un meuble'
        );
        
        // Si un meuble est sélectionné, charger les tiroirs correspondants
        if (furnitureSelector.value) {
            loadDrawers(prefix, furnitureSelector.value);
        }
    } catch (error) {
        appLog.error('Erreur lors du chargement des meubles:', error);
    }
}

/**
 * Charger les tiroirs pour un meuble spécifique
 * @param {string} prefix - Préfixe pour les sélecteurs
 * @param {number} furnitureId - ID du meuble
 */
async function loadDrawers(prefix, furnitureId) {
    const drawerSelector = document.getElementById(`${prefix}itemDrawer`);
    if (!drawerSelector) return;
    
    try {
        // Activer le sélecteur de tiroir
        drawerSelector.disabled = false;
        
        const drawers = await LocationCore.fetchDrawers(furnitureId);
        LocationCore.updateSelectOptions(
            drawerSelector, 
            drawers, 
            'id', 
            'name', 
            'Sélectionnez un tiroir/niveau'
        );
    } catch (error) {
        appLog.error('Erreur lors du chargement des tiroirs:', error);
    }
}

/**
 * Configurer les écouteurs de changement pour les sélecteurs
 * @param {string} prefix - Préfixe pour les sélecteurs
 */
function setupSelectionListeners(prefix) {
    const zoneSelector = document.getElementById(`${prefix}itemZone`);
    const furnitureSelector = document.getElementById(`${prefix}itemFurniture`);
    
    if (zoneSelector) {
        zoneSelector.addEventListener('change', function() {
            const zoneId = this.value;
            
            // Réinitialiser les sélecteurs dépendants
            const furnitureSelector = document.getElementById(`${prefix}itemFurniture`);
            const drawerSelector = document.getElementById(`${prefix}itemDrawer`);
            
            if (furnitureSelector) {
                furnitureSelector.innerHTML = '<option value="">Sélectionnez un meuble</option>';
            }
            
            if (drawerSelector) {
                drawerSelector.innerHTML = '<option value="">Sélectionnez un tiroir/niveau</option>';
            }
            
            // Si une zone est sélectionnée, charger les meubles correspondants
            if (zoneId) {
                loadFurniture(prefix, zoneId);
            }
        });
    }
    
    if (furnitureSelector) {
        furnitureSelector.addEventListener('change', function() {
            const furnitureId = this.value;
            
            // Réinitialiser le sélecteur de tiroirs
            const drawerSelector = document.getElementById(`${prefix}itemDrawer`);
            if (drawerSelector) {
                drawerSelector.innerHTML = '<option value="">Sélectionnez un tiroir/niveau</option>';
            }
            
            // Si un meuble est sélectionné, charger les tiroirs correspondants
            if (furnitureId) {
                loadDrawers(prefix, furnitureId);
            }
        });
    }
}

/**
 * Configurer les liens d'ajout rapide
 * @param {string} prefix - Préfixe pour les sélecteurs
 */
function setupAddLinks(prefix) {
    // Liens d'ajout rapide
    const addZoneLink = document.getElementById(`${prefix}addZoneLink`);
    const addFurnitureLink = document.getElementById(`${prefix}addFurnitureLink`);
    const addDrawerLink = document.getElementById(`${prefix}addDrawerLink`);
    
    if (addZoneLink) {
        addZoneLink.addEventListener('click', function(e) {
            e.preventDefault();
            showAddModal('zone', prefix);
        });
    }
    
    if (addFurnitureLink) {
        addFurnitureLink.addEventListener('click', function(e) {
            e.preventDefault();
            
            const zoneId = document.getElementById(`${prefix}itemZone`).value;
            if (!zoneId) {
                notificationManager.show('Veuillez d\'abord sélectionner une zone', 'warning');
                return;
            }
            
            showAddModal('furniture', prefix, zoneId);
        });
    }
    
    if (addDrawerLink) {
        addDrawerLink.addEventListener('click', function(e) {
            e.preventDefault();
            
            const furnitureId = document.getElementById(`${prefix}itemFurniture`).value;
            if (!furnitureId) {
                notificationManager.show('Veuillez d\'abord sélectionner un meuble', 'warning');
                return;
            }
            
            showAddModal('drawer', prefix, null, furnitureId);
        });
    }
}

/**
 * Afficher le modal d'ajout
 * @param {string} type - Type d'élément (zone, furniture, drawer)
 * @param {string} prefix - Préfixe pour les sélecteurs
 * @param {number} zoneId - ID de la zone (pour les meubles)
 * @param {number} furnitureId - ID du meuble (pour les tiroirs)
 */
function showAddModal(type, prefix, zoneId = null, furnitureId = null) {
    // Construire le modal dynamiquement s'il n'existe pas
    let modal = document.getElementById('addLocationModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'addLocationModal';
        modal.className = 'modal fade';
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('aria-hidden', 'true');
        
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="addLocationModalTitle">Ajouter</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fermer"></button>
                    </div>
                    <div class="modal-body">
                        <form id="addLocationForm">
                            <input type="hidden" id="addLocationType">
                            <input type="hidden" id="addLocationZoneId">
                            <input type="hidden" id="addLocationFurnitureId">
                            <input type="hidden" id="addLocationPrefix">
                            <div class="mb-3">
                                <label for="addLocationName" class="form-label">Nom</label>
                                <input type="text" class="form-control" id="addLocationName" required>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                        <button type="button" class="btn btn-success" id="saveAddLocation">Ajouter</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Ajouter l'écouteur pour le bouton de sauvegarde
        document.getElementById('saveAddLocation').addEventListener('click', function() {
            saveAddLocation();
        });
    }
    
    // Mettre à jour les champs cachés
    document.getElementById('addLocationType').value = type;
    document.getElementById('addLocationPrefix').value = prefix;
    document.getElementById('addLocationName').value = '';
    
    if (zoneId) {
        document.getElementById('addLocationZoneId').value = zoneId;
    }
    
    if (furnitureId) {
        document.getElementById('addLocationFurnitureId').value = furnitureId;
    }
    
    // Mettre à jour le titre
    let title = '';
    switch (type) {
        case 'zone': title = 'Ajouter une zone'; break;
        case 'furniture': title = 'Ajouter un meuble'; break;
        case 'drawer': title = 'Ajouter un tiroir/niveau'; break;
    }
    
    document.getElementById('addLocationModalTitle').textContent = title;
    
    // Afficher le modal
    const bsModal = new bootstrap.Modal(document.getElementById('addLocationModal'));
    bsModal.show();
}

/**
 * Sauvegarder l'ajout d'un nouvel élément
 */
async function saveAddLocation() {
    const type = document.getElementById('addLocationType').value;
    const name = document.getElementById('addLocationName').value;
    const prefix = document.getElementById('addLocationPrefix').value;
    
    if (!name.trim()) {
        notificationManager.warning('Le nom ne peut pas être vide');
        return;
    }
    
    try {
        let result;
        
        if (type === 'zone') {
            result = await LocationCore.createZone(name);
            
            // Recharger les zones et sélectionner la nouvelle
            const zones = await LocationCore.fetchZones();
            const zoneSelector = document.getElementById(`${prefix}itemZone`);
            
            LocationCore.updateSelectOptions(
                zoneSelector, 
                zones, 
                'id', 
                'name', 
                'Sélectionnez une zone', 
                result.id
            );
            
            // Déclencher l'événement de changement pour charger les meubles
            zoneSelector.dispatchEvent(new Event('change'));
            
        } else if (type === 'furniture') {
            const zoneId = document.getElementById('addLocationZoneId').value;
            result = await LocationCore.createFurniture(zoneId, name);
            
            // Recharger les meubles et sélectionner le nouveau
            const furniture = await LocationCore.fetchFurniture(zoneId);
            const furnitureSelector = document.getElementById(`${prefix}itemFurniture`);
            
            LocationCore.updateSelectOptions(
                furnitureSelector, 
                furniture, 
                'id', 
                'name', 
                'Sélectionnez un meuble', 
                result.id
            );
            
            // Déclencher l'événement de changement pour charger les tiroirs
            furnitureSelector.dispatchEvent(new Event('change'));
            
        } else if (type === 'drawer') {
            const furnitureId = document.getElementById('addLocationFurnitureId').value;
            result = await LocationCore.createDrawer(furnitureId, name);
            
            // Recharger les tiroirs et sélectionner le nouveau
            const drawers = await LocationCore.fetchDrawers(furnitureId);
            const drawerSelector = document.getElementById(`${prefix}itemDrawer`);
            
            LocationCore.updateSelectOptions(
                drawerSelector, 
                drawers, 
                'id', 
                'name', 
                'Sélectionnez un tiroir/niveau', 
                result.id
            );
        }
        
        notificationManager.show(`${getTypeName(type)} ajouté avec succès`, 'success');
        
        // Fermer le modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('addLocationModal'));
        modal.hide();
    } catch (error) {
        notificationManager.show(`Erreur lors de l'ajout: ${error.message}`, 'danger');
    }
}

/**
 * Pré-sélectionner les valeurs dans un formulaire d'édition
 */
function preSelectLocationValues() {
    // Cette fonction n'est utile que si les valeurs sont présentes sous forme de data-attributes
    // sur les sélecteurs ou sous une autre forme
    // Sinon, la sélection se fait au chargement des données
    
    const zoneSelector = document.getElementById('editItemZone');
    const furnitureSelector = document.getElementById('editItemFurniture');
    const drawerSelector = document.getElementById('editItemDrawer');
    
    if (!zoneSelector) return;
    
    // Si les valeurs sont stockées dans des attributs data
    const zoneId = zoneSelector.getAttribute('data-selected');
    const furnitureId = furnitureSelector?.getAttribute('data-selected');
    const drawerId = drawerSelector?.getAttribute('data-selected');
    
    if (zoneId) {
        // Attendre que les zones soient chargées
        const checkZones = setInterval(() => {
            if (zoneSelector.options.length > 1) {
                clearInterval(checkZones);
                
                // Sélectionner la zone
                zoneSelector.value = zoneId;
                zoneSelector.dispatchEvent(new Event('change'));
                
                // Si un meuble est également sélectionné
                if (furnitureId) {
                    // Attendre que les meubles soient chargés
                    const checkFurniture = setInterval(() => {
                        if (furnitureSelector.options.length > 1) {
                            clearInterval(checkFurniture);
                            
                            furnitureSelector.value = furnitureId;
                            furnitureSelector.dispatchEvent(new Event('change'));
                            
                            // Si un tiroir est également sélectionné
                            if (drawerId) {
                                // Attendre que les tiroirs soient chargés
                                const checkDrawers = setInterval(() => {
                                    if (drawerSelector.options.length > 1) {
                                        clearInterval(checkDrawers);
                                        drawerSelector.value = drawerId;
                                    }
                                }, 100);
                                
                                // Sécurité pour éviter une boucle infinie
                                setTimeout(() => clearInterval(checkDrawers), 5000);
                            }
                        }
                    }, 100);
                    
                    // Sécurité pour éviter une boucle infinie
                    setTimeout(() => clearInterval(checkFurniture), 5000);
                }
            }
        }, 100);
        
        // Sécurité pour éviter une boucle infinie
        setTimeout(() => clearInterval(checkZones), 5000);
    }
}

/**
 * Obtenir le nom lisible d'un type d'élément
 * @param {string} type - Type d'élément (zone, furniture, drawer)
 * @returns {string} Nom lisible
 */
function getTypeName(type) {
    switch (type) {
        case 'zone': return 'la zone';
        case 'furniture': return 'le meuble';
        case 'drawer': return 'le tiroir/niveau';
        default: return type;
    }
}

// La fonction showFlash a été supprimée car non utilisée et pour uniformiser avec notificationManager
