// Attendre que le DOM soit chargé
document.addEventListener('DOMContentLoaded', async function() {
    appLog.log('DOM chargé, initialisation...');
    
    // Vérifier si nous sommes sur la page du dashboard
    const isDashboard = document.getElementById('borrowForm') !== null;
    if (!isDashboard) {
        appLog.log('Page autre que le dashboard, pas d\'initialisation nécessaire');
        return;
    }
    
    appLog.log('Page dashboard détectée, initialisation...');
    
    // Variables globales pour stocker les articles
    let allItems = [];
    let tempItems = [];
    
    // Initialiser le datepicker avec la localisation française
    if (flatpickr) {
        try {
            flatpickr.localize(flatpickr.l10ns.fr);
            flatpickr("#return_date", {
                dateFormat: "d/m/Y",
                minDate: "today"
            });
        } catch (e) {
            appLog.error("Erreur d'initialisation de flatpickr:", e);
        }
    }
    
    // Charger la liste complète des articles conventionnels
    async function loadItems() {
        try {
            const response = await fetch('/api/items');
            if (!response.ok) throw new Error('Erreur lors du chargement des articles conventionnels');
            
            const data = await response.json();
            allItems = Array.isArray(data) ? data : data.items || [];
            appLog.log('Articles disponibles:', allItems);
            
            return allItems;
        } catch (error) {
            appLog.error('Erreur lors du chargement des articles:', error);
            return [];
        }
    }
    
    // Charger la liste des articles temporaires
    async function loadTempItems() {
        try {
            const response = await fetch('/api/items?is_temporary=true');
            if (!response.ok) throw new Error('Erreur lors du chargement des articles temporaires');
            
            const data = await response.json();
            tempItems = Array.isArray(data) ? data : data.items || [];
            appLog.log('Articles temporaires disponibles:', tempItems);
            
            return tempItems;
        } catch (error) {
            appLog.error('Erreur lors du chargement des articles temporaires:', error);
            return [];
        }
    }
    
    // Initialisation des gestionnaires d'événements une fois que tout est chargé
    async function init() {
        // Charger les articles
        await loadItems();
        await loadTempItems();
        
        // Charger les zones, meubles et tiroirs
        await loadZones();
        
        // Initialiser les sélecteurs de localisation
        initLocationSelectors();
        
        // Initialiser l'état de l'interrupteur
        if ($('#isTemporary').is(':checked')) {
            $('#locationFields').hide();
            $('#itemZone, #itemFurniture, #itemDrawer').prop('required', false);
        } else {
            $('#locationFields').show();
            $('#itemZone, #itemFurniture, #itemDrawer').prop('required', true);
        }
        
        // Gérer l'affichage des champs de localisation selon si l'article est temporaire ou non
        $('#isTemporary').on('change', function() {
            if ($(this).is(':checked')) {
                $('#locationFields').hide();
                $('#itemZone, #itemFurniture, #itemDrawer').prop('required', false);
            } else {
                $('#locationFields').show();
                $('#itemZone, #itemFurniture, #itemDrawer').prop('required', true);
            }
        });
        
        // Autocomplete pour le nom de l'article
        $('#itemName').on('input', function() {
            const inputValue = $(this).val().trim().toLowerCase();
            const suggestionsContainer = $(this).closest('.item-search-container').find('.suggestions-list');
            
            if (inputValue.length < 2) {
                suggestionsContainer.addClass('d-none').empty();
                return;
            }
            
            // Filtrer les articles correspondants
            const filteredItems = allItems.filter(item => !item.is_temporary && item.name.toLowerCase().includes(inputValue));
            
            if (filteredItems.length > 0) {
                suggestionsContainer.removeClass('d-none').empty();
                
                filteredItems.forEach(item => {
                    const suggestionItem = $('<div class="suggestion-item"></div>');
                    
                    const regex = new RegExp(`(${inputValue.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')})`, 'gi');
                    const highlightedName = item.name.replace(regex, '<strong>$1</strong>');
                    
                    let locationText = '';
                    if (item.is_temporary) {
                        locationText = '<small class="text-muted d-block">Article temporaire</small>';
                    } else if (item.location && (item.location.zone_name || item.location.furniture_name || item.location.drawer_name)) {
                        const parts = [];
                        if (item.location.zone_name) parts.push(`Zone: ${item.location.zone_name}`);
                        if (item.location.furniture_name) parts.push(`Meuble: ${item.location.furniture_name}`);
                        if (item.location.drawer_name) parts.push(`Tiroir: ${item.location.drawer_name}`);
                        locationText = `<small class="text-muted d-block">${parts.join(' | ')}</small>`;
                    } else if (item.zone_name || item.furniture_name || item.drawer_name) { // Fallback if not nested
                        const parts = [];
                        if (item.zone_name) parts.push(`Zone: ${item.zone_name}`);
                        if (item.furniture_name) parts.push(`Meuble: ${item.furniture_name}`);
                        if (item.drawer_name) parts.push(`Tiroir: ${item.drawer_name}`);
                        locationText = `<small class="text-muted d-block">${parts.join(' | ')}</small>`;
                    }

                    suggestionItem.html(`
                        <div class="suggestion-item-name">${highlightedName}</div>
                        ${locationText}
                    `);

                    suggestionItem.on('click', function() {
                        $('#itemName').val(item.name);
                        suggestionsContainer.addClass('d-none').empty();
                        
                        $('#isTemporary').prop('checked', item.is_temporary === true).trigger('change');

                        if (!item.is_temporary && item.zone_id) {
                            $('#itemZone').val(item.zone_id);
                            $('#itemZone').prop('disabled', true);
                            $('#itemFurniture').prop('disabled', true);
                            $('#itemDrawer').prop('disabled', true);
                            
                            $.ajax({
                                url: `/api/location/furniture?zone_id=${item.zone_id}`,
                                method: 'GET',
                                success: function(furniture) {
                                    const furnitureSelect = $('#itemFurniture');
                                    furnitureSelect.empty().append('<option value="">Sélectionnez un meuble</option>');
                                    $.each(furniture, function(i, f) {
                                        furnitureSelect.append(`<option value="${f.id}" ${f.id == item.furniture_id ? 'selected' : ''}>${f.name}</option>`);
                                    });
                                    if (item.furniture_id) {
                                        $.ajax({
                                            url: `/api/location/drawers?furniture_id=${item.furniture_id}`,
                                            method: 'GET',
                                            success: function(drawers) {
                                                const drawerSelect = $('#itemDrawer');
                                                drawerSelect.empty().append('<option value="">Sélectionnez un tiroir/niveau</option>');
                                                $.each(drawers, function(i, d) {
                                                    drawerSelect.append(`<option value="${d.id}" ${d.id == item.drawer_id ? 'selected' : ''}>${d.name}</option>`);
                                                });
                                            },
                                            error: function(error) { appLog.error('Erreur chargement tiroirs:', error); }
                                        });
                                    }
                                },
                                error: function(error) { appLog.error('Erreur chargement meubles:', error); }
                            });
                        }
                    });
                    suggestionsContainer.append(suggestionItem);
                });
            } else {
                suggestionsContainer.addClass('d-none').empty();
            }
        });
        
        // Cacher les suggestions quand on clique ailleurs
        $(document).on('click', function(e) {
            if (!$(e.target).closest('.item-search-container').length) {
                $('.suggestions-list').addClass('d-none').empty();
            }
        });
        
        // Ajouter un article à la liste des articles à emprunter
        $('#saveItem').on('click', function() {
            const $saveButton = $(this);
            $saveButton.prop('disabled', true); // Désactiver le bouton

            const name = $('#itemName').val().trim();
            appLog.log('Tentative d\'ajout d\'article conventionnel via addItemModal:', { name });

            if (!name) {
                notificationManager.warning('Le nom de l\'article est requis');
                $saveButton.prop('disabled', false); // Réactiver le bouton
                return;
            }

            const zoneId = $('#itemZone').val();
            const furnitureId = $('#itemFurniture').val();
            const drawerId = $('#itemDrawer').val();

            appLog.log('Informations de localisation pour nouvel article conventionnel:', {
                zoneId, furnitureId, drawerId
            });

            if (!zoneId || !furnitureId || !drawerId) {
                notificationManager.warning('Les informations de localisation (zone, mobilier, tiroir) sont obligatoires pour un article conventionnel.');
                $saveButton.prop('disabled', false); // Réactiver le bouton
                return;
            }

            const selectedItemsInQueue = document.querySelectorAll('#itemsQueue .item-name');
            let isDuplicateInQueue = false;
            selectedItemsInQueue.forEach(itemElement => {
                if (itemElement.textContent.toLowerCase() === name.toLowerCase()) {
                    isDuplicateInQueue = true;
                }
            });

            if (isDuplicateInQueue) {
                notificationManager.warning(`L'article "${name}" est déjà dans votre liste d'emprunt.`);
                $saveButton.prop('disabled', false); // Réactiver le bouton
                return;
            }

            const existingItemInAllItems = allItems.find(item =>
                item.name.toLowerCase() === name.toLowerCase() &&
                !item.is_temporary
            );

            // Fonction helper pour l'appel AJAX de création/utilisation d'article conventionnel
            function createOrUseConventionalItemAPI(itemName, itemZoneId, itemFurnitureId, itemDrawerId) {
                $.ajax({
                    url: '/api/items/add',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        name: itemName,
                        zone_id: itemZoneId,
                        furniture_id: itemFurnitureId,
                        drawer_id: itemDrawerId,
                        is_temporary: false
                    }),
                    success: function(data) {
                        if (data.item) {
                            appLog.log('Réponse API succès pour ajout/utilisation article conventionnel:', data.item);
                            if (!allItems.find(i => i.id === data.item.id)) {
                                allItems.push(data.item);
                            }
                            processAddItem(data.item, itemName);
                            $('#addItemModal').modal('hide');
                        } else if (data.error && data.item) { // Cas spécifique du 409 où le backend renvoie l'item existant
                            notificationManager.warning(data.error);
                            appLog.warn('Conflit détecté par le backend (409 avec item):', data.error, data.item);
                            processAddItem(data.item, itemName);
                            $('#addItemModal').modal('hide');
                        } else {
                            notificationManager.error(data.error || 'Erreur lors de la création/utilisation de l\'article.');
                            appLog.error('Erreur API (sans item dans succès):', data);
                        }
                    },
                    error: function(jqXHR) {
                        const response = jqXHR.responseJSON || {};
                        const errorMsg = response.error || 'Impossible de créer ou d\'utiliser l\'article.';
                        const conflictItem = response.item;

                        notificationManager.error('Erreur: ' + errorMsg);
                        appLog.error('Erreur AJAX pour création/utilisation article:', errorMsg, conflictItem, jqXHR);

                        if (jqXHR.status === 409 && conflictItem) {
                            appLog.log('Conflit 409 du backend, utilisation de l\'article existant fourni:', conflictItem);
                            processAddItem(conflictItem, conflictItem.name);
                            $('#addItemModal').modal('hide');
                        }
                    },
                    complete: function() {
                        $saveButton.prop('disabled', false); // Réactiver le bouton dans tous les cas
                    }
                });
            }

            if (existingItemInAllItems) {
                let useThisExistingItem = false;
                if (parseInt(zoneId) === existingItemInAllItems.zone_id &&
                    parseInt(furnitureId) === existingItemInAllItems.furniture_id &&
                    parseInt(drawerId) === existingItemInAllItems.drawer_id) {
                    useThisExistingItem = true;
                }

                if (useThisExistingItem) {
                    appLog.log('Article conventionnel existant (même nom et emplacement) trouvé dans allItems, ajout à la liste d\'emprunt:', existingItemInAllItems);
                    processAddItem(existingItemInAllItems, name);
                    $('#addItemModal').modal('hide');
                    $saveButton.prop('disabled', false); // Réactiver le bouton
                } else {
                    appLog.log('Nom d\'article existant dans allItems mais emplacement différent ou entré manuellement. Tentative de création/utilisation via API.');
                    createOrUseConventionalItemAPI(name, zoneId, furnitureId, drawerId);
                }
            } else {
                appLog.log('Article conventionnel non trouvé dans allItems. Tentative de création via API.');
                createOrUseConventionalItemAPI(name, zoneId, furnitureId, drawerId);
            }
        });
    }
    
    // Fonction pour ajouter un article temporaire via la reconnaissance vocale
    window.addTemporaryItem = function(itemName) {
        if (!itemName || typeof itemName !== 'string' || itemName.trim() === '') {
            appLog.error('Nom d\'article invalide pour addTemporaryItem:', itemName);
            return false;
        }
        
        // Mettre une majuscule à la première lettre
        itemName = itemName.trim();
        itemName = itemName.charAt(0).toUpperCase() + itemName.slice(1);
        appLog.log('Ajout d\'un article temporaire via reconnaissance vocale:', itemName);
        
        // Appel API pour créer l'article temporaire via la route unifiée
        $.ajax({
            url: '/api/items/add',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ name: itemName, is_temporary: true }),
            success: function(data) {
                processAddItem(data.item, itemName);
            },
            error: function(error) {
                appLog.error('Erreur lors de l\'ajout de l\'article temporaire:', error);
                notificationManager.show('Erreur: ' + (error.responseJSON?.error || `Impossible d'ajouter l'article temporaire "${itemName}"`), 'danger');
            }
        });
        
        return true;
    };
    
    // Fonction pour ajouter un article conventionnel via la reconnaissance vocale
    window.addConventionalItem = function(itemData) {
        if (!itemData || !itemData.name || typeof itemData.name !== 'string' || itemData.name.trim() === '') {
            appLog.error('Données d\'article invalides pour addConventionalItem:', itemData);
            return false;
        }
        
        // Mettre une majuscule à la première lettre
        const itemName = itemData.name.trim();
        itemData.name = itemName.charAt(0).toUpperCase() + itemName.slice(1);
        appLog.log('Ajout d\'un article conventionnel via reconnaissance vocale:', itemData);
        
        // Si l'article a un ID de base de données, on l'utilise directement
        if (itemData.db_id) {
            // Récupérer les détails de l'article depuis la base de données
            $.ajax({
                url: `/api/items/${itemData.db_id}`,
                method: 'GET',
                success: function(data) {
                    // Utiliser les données complètes de l'article pour l'ajouter à la liste
                    processAddItem(data.item, itemData.name);
                },
                error: function(error) {
                    appLog.error('Erreur lors de la récupération de l\'article conventionnel:', error);
                    // En cas d'erreur, utiliser les données partielles que nous avons
                    const partialItemData = {
                        id: itemData.db_id,
                        name: itemData.name,
                        is_temporary: false
                    };
                    
                    // Ajouter les informations d'emplacement si disponibles
                    if (itemData.zone_id) partialItemData.zone_id = itemData.zone_id;
                    if (itemData.furniture_id) partialItemData.furniture_id = itemData.furniture_id;
                    if (itemData.drawer_id) partialItemData.drawer_id = itemData.drawer_id;
                    if (itemData.location_info) partialItemData.location_info = itemData.location_info;
                    
                    processAddItem(partialItemData, itemData.name);
                    notificationManager.warning(`Informations partielles pour l'article "${itemData.name}"`);
                }
            });
        } else {
            // Si nous n'avons pas d'ID, traiter comme un article temporaire
            appLog.log('Article conventionnel sans ID, traitement comme article temporaire:', itemData.name);
            addTemporaryItem(itemData.name);
        }
        
        return true;
    };
    
    // Initialisation
    appLog.log('Initialisation des gestionnaires d\'événements...');
    init();
    
    appLog.log('Initialisation terminée');
});
