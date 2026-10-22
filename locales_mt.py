"""
YATB - MASCHINELL ÜBERSETZTE Bot-Texte (Französisch, Spanisch, Italienisch, Russisch, Niederländisch)

Erzeugt am 2026-10-20 (Niederländisch: später am selben Tag) aus locales.py (Englisch) mit Google Gemini (gemini-3.1-flash-lite) über den Gemini-Key des
Betreibers. Platzhalter und Befehle in Backticks wurden automatisch geprüft. NICHT von Muttersprachlern geprüft -
Korrekturen bitte direkt hier eintragen und die Zeile mit "# geprüft" markieren. Fehlende Texte fallen auf Englisch zurück.
Neu erzeugen: siehe Hinweis in locales.py (gleiches Verfahren, nur geänderte Texte übersetzen).
"""

MESSAGES_MT = {'es': {'bad_bridge': 'Por favor, introduce un nombre de Bridge.',
        'bridge_kind_mismatch': '❌ Los foros solo pueden vincularse con foros, y los canales de texto solo con canales '
                                'de texto. El Bridge `{bridge}` ya contiene el otro tipo; por favor, usa un nombre de '
                                'Bridge diferente.',
        'bridges_title': '🌐 Bridges en este servidor',
        'btn_cancel': 'Cancelar',
        'btn_confirm': 'Confirmar',
        'cancelled': 'Cancelado.',
        'channel_added': '✅ Canal {channel} añadido al Bridge `{bridge}` ({lang}).',
        'channel_not_found': '⚠️ El canal {channel} no forma parte de ningún Bridge en este servidor.',
        'channel_removed': '🗑️ Canal {channel} eliminado del Bridge `{bridge}`.',
        'channels_bridges': 'Puentes de YATB',
        'channels_bridges_value': '**{channels}** canales en **{bridges}** puentes. Añadir un idioma más a cada puente '
                                  'requiere **{per_lang}** canales nuevos.',
        'channels_title': '📊 Canales en este servidor',
        'channels_total': '**{total} de {limit}** canales usados ({pct} %) - **{free}** aún libres.\n'
                          'Discord permite 500 canales por servidor; las categorías cuentan, los hilos no.',
        'channels_type_category': '📁 Categorías',
        'channels_type_forum': '📂 Foro',
        'channels_type_media': '🖼️ Multimedia',
        'channels_type_news': '📢 Anuncios',
        'channels_type_stage': '🎙️ Escenario',
        'channels_type_text': '💬 Texto',
        'channels_type_voice': '🔊 Voz',
        'channels_types': 'Por tipo',
        'channels_warn': 'Solo quedan **{free}** canales. Elimina los canales que no uses antes de añadir nuevos '
                         'idiomas.',
        'confirm_reset': '⚠️ Esto eliminará **todos** los Bridge, claves y ajustes de este servidor. ¿Continuar?',
        'confirm_uninstall': '⚠️ Esto eliminará **todos** los datos de este servidor y el bot se irá. ¿Continuar?',
        'default': 'predeterminado',
        'error': '🔴 Error',
        'form_budget': 'Presupuesto mensual (solo [Paid])',
        'form_budget_desc': 'ej. 8.50 EUR o 10 USD. Vacío = predeterminado ({default}).',
        'form_budget_invalid': '❌ Presupuesto no reconocido. Usa ej. `8.50 EUR` o `10 USD` (máx. 1000). No se ha '
                               'cambiado nada.',
        'form_key': 'Clave API',
        'form_key_desc': 'Se almacena cifrada y nunca se volverá a mostrar.',
        'form_label': 'Nombre (opcional)',
        'form_label_desc': 'Para distinguir tus claves, ej. principal',
        'form_limit': 'Límite de uso',
        'form_limit_desc': 'Activado = detener al alcanzar los límites del plan o presupuesto (recomendado)',
        'form_pick_intro': '¿Para qué servicio es la clave? Elígelo a continuación: se abrirá un formulario específico '
                           'para ese servicio. La clave solo se introduce ahí.',
        'form_pick_provider': 'Elige un servicio de traducción',
        'form_region': 'Región de Azure',
        'form_region_desc': 'Ubicación de tu recurso de Translator, ej. westeurope',
        'form_tier': 'Plan',
        'form_tier_desc': '[Free]: se aplican los límites del proveedor. [Paid]: presupuesto mensual.',
        'form_title_add': 'Añadir clave de {provider}',
        'form_title_edit': 'Editar clave de {provider}',
        'forum_tags_hint': 'ℹ️ Para crear las etiquetas que faltan en el propio {channel}, YATB necesita el permiso '
                           '**Gestionar canales** en este foro. Sin él, solo se emparejarán las etiquetas con el mismo '
                           'nombre.',
        'guide_azure': '1. En portal.azure.com crea un recurso **Translator** (nivel de precios **F0** = 2 millones de '
                       'caracteres al mes [Free]).\n'
                       '2. Abre **Keys and Endpoint**: copia **Key 1** y la **Location/Region** (ej. westeurope).\n'
                       '3. Ejecuta `/yatb keys add`, elige **Azure Translator** e introduce la clave y la región.',
        'guide_footer': 'Los nombres de los menús en los proveedores pueden cambiar. Consejo: establece también un '
                        'límite de gasto en tu cuenta de proveedor.',
        'guide_gemini': '1. Abre aistudio.google.com e inicia sesión con tu cuenta de Google.\n'
                        '2. Crea o elige un proyecto de Google Cloud y **activa la facturación**; el nivel [Free] '
                        'puede no estar disponible para usuarios en el EEE, Reino Unido o Suiza.\n'
                        '3. **Get API key** → **Create API key** para este proyecto.\n'
                        '4. Ejecuta `/yatb keys add`, elige **Google Gemini** y pega la clave.',
        'guide_google_translate': '1. Abre console.cloud.google.com y crea un proyecto.\n'
                                  '2. Activa la **Cloud Translation API** (se requiere una cuenta de facturación; los '
                                  'primeros 500.000 caracteres al mes son [Free]).\n'
                                  '3. **APIs & Services → Credentials → Create credentials → API key**, luego '
                                  'restringe la clave a la Cloud Translation API.\n'
                                  '4. Ejecuta `/yatb keys add` y elige **Google Translate**.',
        'guide_groq': '1. Inicia sesión en console.groq.com.\n'
                      '2. Recomendado: activa la retención de datos cero en **Settings → Data Controls**.\n'
                      '3. **API Keys** → **Create API Key**.\n'
                      '4. Ejecuta `/yatb keys add` y elige **Groq**. El plan [Free] tiene límites bajos (unas 30 '
                      'solicitudes por minuto).',
        'guide_mistral': '1. Inicia sesión en console.mistral.ai.\n'
                         '2. En **Billing** elige un plan [Paid] (el plan [Free] Experiment puede usar tus datos para '
                         'entrenamiento).\n'
                         '3. **API Keys** → **Create new key**.\n'
                         '4. Ejecuta `/yatb keys add`, elige **Mistral** y pega la clave.',
        'guide_novita': '1. Inicia sesión en novita.ai y añade crédito (no hay plan [Free]).\n'
                        '2. Crea una clave en **Key Management**.\n'
                        '3. Ejecuta `/yatb keys add` y elige **Novita**.',
        'guide_plan': 'Plan',
        'guide_plan_free_paid': 'Es posible usar claves [Free] y [Paid]. Con una clave [Free] se aplican los límites '
                                'del proveedor; con una clave [Paid] estableces un presupuesto mensual.',
        'guide_plan_paid_only': 'Solo se pueden usar claves [Paid] (proyecto/cuenta con facturación).',
        'guide_privacy': 'Privacidad',
        'guide_steps': 'Pasos',
        'guide_title': '🔑 Cómo obtener una clave API de {provider}',
        'info_desc': 'YATB conecta canales de texto de diferentes idiomas en [Bridge] de traducción: un mensaje en un '
                     'canal aparece traducido en todos los demás, incluyendo respuestas, ediciones, eliminaciones e '
                     'hilos.',
        'info_f1_name': '1. Conectar canales',
        'info_f1_val': '`/yatb bridge add` añade un canal a un Bridge: los canales con el mismo nombre de Bridge se '
                       'traducirán entre sí.\n'
                       '*Ejemplo:* `/yatb bridge add chat #english English` y `/yatb bridge add chat #german German`. '
                       'Resumen: `/yatb bridge list`.\n'
                       'Los canales de foro y multimedia funcionan igual (foro con foro). Para las etiquetas '
                       'automáticas, YATB necesita el permiso *Gestionar canales* allí; lo más fácil es dárselo a la '
                       'categoría de los foros.',
        'info_f2_name': '2. Servicios de traducción',
        'info_f2_val': 'Sin claves, YATB traduce con LibreTranslate (local, [Free], calidad básica). Mejores '
                       'resultados con tus propias claves API: `/yatb keys add` (proveedores IA, Google, Azure). '
                       'Orden: IA → Google → Azure → Libre. Cómo obtener una clave: `/yatb guide`.',
        'info_f3_name': '3. Uso y límites',
        'info_f3_val': '`/yatb keys list` muestra el uso por clave, `/yatb keys edit` cambia el plan, presupuesto y '
                       'límite. Las advertencias al 90/95/100 % se envían al canal de registro (`/yatb log set`).',
        'info_f4_name': '4. Estado',
        'info_f4_val': '`/yatb status` muestra la cadena de traducción de este servidor y el estado de cada servicio.',
        'info_f5_name': '5. Privacidad y restablecimiento',
        'info_f5_val': 'Los miembros pueden elegir `/yatb-user privacy` → *Local only*: sus mensajes solo se '
                       'traducirán localmente y nunca se enviarán a terceros.\n'
                       '• `/yatb reset`: elimina todos los [Bridge], claves y ajustes.\n'
                       '• `/yatb uninstall`: elimina todos los datos y el bot abandona el servidor.',
        'info_title': '🌐 YATB (Yet Another Translation Bot) - Guía',
        'key_rejected': '🔑 {provider} rechazó la clave API de este servidor ({status}). La clave se omitirá durante 1 '
                        'hora y se usará el siguiente motor. Compruébalo con `/yatb keys list` o reemplázala con '
                        '`/yatb keys add`.',
        'keys_bad_format': '❌ Eso no parece una clave API (16-512 caracteres, sin espacios). No se ha guardado nada.',
        'keys_budget': 'presupuesto',
        'keys_confirm_limit_off': '⚠️ **¿Desactivar el límite de uso para {desc}?**\n'
                                  'El bot seguirá usando esta clave más allá de los límites [Free]/plan. Cualquier '
                                  'coste cobrado por el proveedor es **tu responsabilidad**.',
        'keys_confirm_remove': '⚠️ ¿Eliminar la clave {desc}? Las traducciones con esta clave se detendrán '
                               'inmediatamente.',
        'keys_duplicate': 'ℹ️ Esta clave ya está guardada en este servidor: {desc}.',
        'keys_error': '❌ No se pudo procesar la clave. No se ha realizado ningún cambio.',
        'keys_limit': 'límite',
        'keys_limit_off': '⚠️ Límite de uso desactivado para {desc}.',
        'keys_limit_on': '✅ Límite de uso activado para {desc}.',
        'keys_no_crypto': '🔒 El almacenamiento de claves aún no está disponible: el operador del bot no ha configurado '
                          'la clave maestra.',
        'keys_none': 'No hay claves API guardadas en este servidor. Añade una con `/yatb keys add`.',
        'keys_not_found': '⚠️ Esta clave no se encontró en este servidor.',
        'keys_off': 'desactivado',
        'keys_on': 'activado',
        'keys_paid_only': 'ℹ️ {provider} solo se usa con claves de pago (facturación activada), por lo que la clave se '
                          'guardó como **de pago**.',
        'keys_region_needed': '❌ Azure necesita la región de tu recurso de Translator (ej. `westeurope`). No se ha '
                              'guardado nada.',
        'keys_rejected': '❌ {provider} rechazó esta clave ({status}). No se ha guardado.',
        'keys_removed': '🗑️ Clave eliminada: {desc}.',
        'keys_saved': '🔑 Clave guardada: {desc}. Se almacena cifrada y nunca se volverá a mostrar.',
        'keys_shared_tag': ' · 🔗 también usada en otro servidor',
        'keys_shared_warn': '⚠️ Esta clave ya se está usando en otro servidor. El uso y el límite se contabilizan '
                            'conjuntamente.',
        'keys_title': '🔑 Claves API de este servidor',
        'keys_too_many': '❌ Este servidor ya tiene {max} claves. Elimina una primero (`/yatb keys remove`).',
        'keys_unverified': '⚠️ No se pudo contactar con {provider} para verificar la clave ({status}); se ha guardado '
                           'de todos modos.',
        'keys_updated': '✅ Ajustes guardados: {desc}',
        'keys_usage_line': '  ↳ mes: {month} · hoy: {today}',
        'list_field': 'Bridge: {bridge}',
        'list_footer': 'Motores: {engines} | Registro: {log}',
        'model_missing': '⚠️ {provider}: el modelo `{model}` no está disponible (eliminado o renombrado por el '
                         'proveedor). Se omitirá durante 6 horas; el operador del bot debe actualizar la configuración '
                         'del proveedor.',
        'no_bridges': 'Aún no hay Bridges en este servidor. Usa `/yatb bridge add`.',
        'none': 'Ninguno',
        'none_set': 'no configurado',
        'not_yours': 'Solo la persona que ejecutó el comando puede usar estos botones.',
        'offline': '🔴 Desconectado',
        'online': '🟢 En línea ({ms} ms)',
        'perms_missing': '⚠️ Faltan permisos en {channel}: {perms}. Es posible que el Bridge no funcione hasta que se '
                         'concedan.',
        'privacy_btn_local': 'Usar Solo local',
        'privacy_btn_standard': 'Usar Estándar',
        'privacy_local_desc': 'Tus mensajes permanecen en el bot: solo son traducidos por LibreTranslate en su propio '
                              'servidor y nunca se envían a proveedores de IA, Google o Azure, ni siquiera como '
                              'contexto para las traducciones de otras personas. La calidad de la traducción es menor. '
                              'Se aplica en todos los servidores con YATB.',
        'privacy_local_name': 'Solo local',
        'privacy_standard_desc': 'Mejor calidad. Tus mensajes pueden enviarse a los servicios de traducción que los '
                                 'administradores del servidor hayan añadido (p. ej. proveedores de IA, Google, '
                                 'Azure). Los administradores eligen estos servicios.',
        'privacy_standard_name': 'Estándar',
        'privacy_state_local': 'Ajuste actual: **Solo local**.',
        'privacy_state_standard': 'Ajuste actual: **Estándar**.',
        'privacy_title': '🔒 Tu privacidad en las traducciones',
        'provider_quota': '⚠️ {provider} informa que la cuota de la clave de este servidor se ha agotado. La clave '
                          'está pausada hasta las 00:00 UTC; las traducciones usarán el siguiente motor.',
        'rep_added': '➕ **Bridge:** {user} añadió {channel} a `{bridge}` ({lang}).',
        'rep_channel_set': 'ℹ️ {channel} es ahora el canal de registro.',
        'rep_key_added': '🔑 {user} añadió una clave API: {desc}.',
        'rep_key_edited': 'ℹ️ {user} cambió los ajustes de {desc}.',
        'rep_key_limit': 'ℹ️ {user} estableció el límite de uso de {desc} en **{state}**.',
        'rep_key_removed': '🗑️ {user} eliminó una clave API: {desc}.',
        'rep_order_reset': '🔀 {user} ha restablecido el orden de los servicios de traducción al predeterminado: '
                           '{order}.',
        'rep_order_set': '🔀 {user} ha cambiado el orden de los servicios de traducción: {order}.',
        'rep_removed': '🗑️ **Bridge:** {user} eliminó {channel} ({lang}) de `{bridge}`.',
        'rep_tags_full': '⚠️ {channel} ya tiene 20 etiquetas (límite de Discord); no se ha podido crear una etiqueta '
                         'coincidente.',
        'rep_tags_no_permission': '⚠️ YATB no ha podido crear una etiqueta coincidente en {channel}: falta el permiso '
                                  '**Gestionar canales**.',
        'report_channel_cleared': '📢 Canal de registro desactivado.',
        'report_channel_set': '📢 Canal de registro establecido en {channel}.',
        'reset_done': '🔄 Todos los Bridge, enlaces de webhook, claves y ajustes de este servidor han sido eliminados.',
        'send_forbidden': '⚠️ No tengo permisos para enviar mensajes al Bridge en {channel} (Gestionar Webhooks, Crear '
                          'hilos públicos, Enviar mensajes en hilos).',
        'stage_active': 'activo',
        'stage_exhausted': '🚫 Límite alcanzado',
        'stage_paused': '⏸ pausado (errores)',
        'status_chain': '🔗 Cadena de traducción (en este orden)',
        'status_stats': '• Bridges: `{b}`\n• Canales: `{c}`\n• Rastreador de mensajes: `{m}`',
        'status_stats_name': '📊 Estadísticas del servidor',
        'status_title': '🛠️ Estado del sistema YATB',
        'tier_free': '[Free]',
        'tier_paid': '[Paid]',
        'uninstall_done': '👋 Todos los datos han sido eliminados. YATB se va del servidor.',
        'usage_full': '🚫 Clave {desc}: límite mensual alcanzado ({usage}). La clave está pausada hasta el día 1 del '
                      'próximo mes (00:00 UTC) o hasta que se aumente su límite; las traducciones usarán el siguiente '
                      'motor.',
        'usage_full_nolimit': '⚠️ Clave {desc}: límite mensual excedido ({usage}). El límite está desactivado para '
                              'esta clave, por lo que se sigue usando; cualquier coste es responsabilidad del '
                              'administrador.',
        'usage_warn': '⚠️ Clave {desc}: **{pct}%** del límite mensual consumido ({usage}).',
        'user_help_desc': 'Este servidor conecta canales en diferentes idiomas. Cuando escribes en uno de ellos, YATB '
                          'publica una traducción en los demás bajo tu nombre. Las respuestas, ediciones, '
                          'eliminaciones y reacciones se reflejan automáticamente. YATB no guarda el texto de los '
                          'mensajes, solo qué mensaje pertenece a qué traducción (7 días).',
        'user_help_privacy': 'Con `/yatb-user privacy` puedes decidir que tus mensajes solo se traduzcan localmente y '
                             'nunca se envíen a terceros.',
        'user_help_privacy_name': 'Tu elección',
        'user_help_tags': '`[AI]` Proveedor de IA · `[Google]` Google Translate · `[Azure]` Azure Translator · '
                          '`[Libre]` LibreTranslate (local) · `[Raw]` sin traducir (no hay servicio disponible)',
        'user_help_tags_name': 'Qué significa la etiqueta tras el nombre',
        'user_help_title': 'ℹ️ YATB - puentes de traducción',
        'welcome': '¡Hola {name}! Gracias por añadir **YATB** a **{guild}**.\n'
                   '• Empieza con `/yatb info`.\n'
                   '• Añade una clave de traducción con `/yatb keys add` (cómo obtenerla: `/yatb guide`).'},
 'fr': {'bad_bridge': 'Veuillez entrer un nom de bridge.',
        'bridge_kind_mismatch': "❌ Les forums ne peuvent être liés qu'à des forums, et les salons textuels qu'à des "
                                "salons textuels. Le Bridge `{bridge}` contient déjà l'autre type - utilise un nom de "
                                'Bridge différent.',
        'bridges_title': '🌐 Bridges sur ce serveur',
        'btn_cancel': 'Annuler',
        'btn_confirm': 'Confirmer',
        'cancelled': 'Annulé.',
        'channel_added': '✅ Salon {channel} ajouté au bridge `{bridge}` ({lang}).',
        'channel_not_found': "⚠️ Le salon {channel} ne fait partie d'aucun bridge sur ce serveur.",
        'channel_removed': '🗑️ Salon {channel} retiré du bridge `{bridge}`.',
        'channels_bridges': 'Ponts YATB',
        'channels_bridges_value': '**{channels}** salons dans **{bridges}** ponts. Ajouter une langue supplémentaire à '
                                  'chaque pont nécessite **{per_lang}** nouveaux salons.',
        'channels_title': '📊 Salons sur ce serveur',
        'channels_total': '**{total} sur {limit}** salons utilisés ({pct} %) - **{free}** encore libres.\n'
                          'Discord autorise 500 salons par serveur ; les catégories comptent, les fils de discussion '
                          'non.',
        'channels_type_category': '📁 Catégories',
        'channels_type_forum': '📂 Forum',
        'channels_type_media': '🖼️ Média',
        'channels_type_news': '📢 Annonce',
        'channels_type_stage': '🎙️ Scène',
        'channels_type_text': '💬 Texte',
        'channels_type_voice': '🔊 Vocal',
        'channels_types': 'Par type',
        'channels_warn': "Il ne reste que **{free}** salons. Supprime les salons inutilisés avant d'ajouter de "
                         'nouvelles langues.',
        'confirm_reset': '⚠️ Cela supprimera **tous** les [Bridge], clés et paramètres de ce serveur. Continuer ?',
        'confirm_uninstall': '⚠️ Cela supprimera **toutes** les données de ce serveur et le bot quittera le serveur. '
                             'Continuer ?',
        'default': 'par défaut',
        'error': '🔴 Erreur',
        'form_budget': 'Budget mensuel ([Paid] uniquement)',
        'form_budget_desc': 'ex: 8.50 EUR ou 10 USD. Vide = par défaut ({default}).',
        'form_budget_invalid': "❌ Budget non reconnu. Utilise ex: `8.50 EUR` ou `10 USD` (max. 1000). Rien n'a été "
                               'modifié.',
        'form_key': 'Clé API',
        'form_key_desc': 'Stockée de manière chiffrée et jamais affichée à nouveau.',
        'form_label': 'Nom (optionnel)',
        'form_label_desc': 'Pour distinguer tes clés, ex: principal',
        'form_limit': "Limite d'utilisation",
        'form_limit_desc': 'Activé = arrêter aux limites du plan ou du budget (recommandé)',
        'form_pick_intro': 'Pour quel service est cette clé ? Choisis-le ci-dessous - un formulaire spécifique '
                           "s'ouvrira ensuite. La clé ne sera saisie que là.",
        'form_pick_provider': 'Choisis un service de traduction',
        'form_region': 'Région Azure',
        'form_region_desc': 'Emplacement de ta ressource Translator, ex: westeurope',
        'form_tier': 'Plan',
        'form_tier_desc': "[Free] : les limites du fournisseur s'appliquent. [Paid] : budget mensuel.",
        'form_title_add': 'Ajouter une clé {provider}',
        'form_title_edit': 'Modifier la clé {provider}',
        'forum_tags_hint': 'ℹ️ Pour créer les tags manquants dans {channel}, YATB a besoin de la permission **Gérer '
                           'les salons** dans ce forum. Sans cela, seuls les tags portant le même nom seront associés.',
        'guide_azure': '1. Dans portal.azure.com, crée une ressource **Translator** (niveau tarifaire **F0** = 2 '
                       'millions de caractères par mois [Free]).\n'
                       '2. Ouvre **Keys and Endpoint** : copie **Key 1** et la **Location/Region** (ex: westeurope).\n'
                       '3. Utilise `/yatb keys add`, choisis **Azure Translator** et saisis la clé et la région.',
        'guide_footer': 'Les noms des menus chez les fournisseurs peuvent changer. Conseil : définis aussi une limite '
                        'de dépenses dans ton compte fournisseur.',
        'guide_gemini': '1. Ouvre aistudio.google.com et connecte-toi avec ton compte Google.\n'
                        '2. Crée ou choisis un projet Google Cloud et **active la facturation** - le niveau [Free] '
                        "peut ne pas être disponible pour les utilisateurs de l'EEE, du Royaume-Uni ou de Suisse.\n"
                        '3. **Get API key** → **Create API key** pour ce projet.\n'
                        '4. Utilise `/yatb keys add`, choisis **Google Gemini** et colle la clé.',
        'guide_google_translate': '1. Ouvre console.cloud.google.com et crée un projet.\n'
                                  '2. Active la **Cloud Translation API** (un compte de facturation est requis ; les '
                                  '500 000 premiers caractères par mois sont [Free]).\n'
                                  '3. **APIs & Services → Credentials → Create credentials → API key**, puis restreins '
                                  'la clé à la Cloud Translation API.\n'
                                  '4. Utilise `/yatb keys add` et choisis **Google Translate**.',
        'guide_groq': '1. Connecte-toi sur console.groq.com.\n'
                      '2. Recommandé : active la rétention de données zéro dans **Settings → Data Controls**.\n'
                      '3. **API Keys** → **Create API Key**.\n'
                      '4. Utilise `/yatb keys add` et choisis **Groq**. Le forfait [Free] a des limites basses '
                      '(environ 30 requêtes par minute).',
        'guide_mistral': '1. Connecte-toi sur console.mistral.ai.\n'
                         '2. Dans **Billing**, choisis un forfait [Paid] (le forfait [Free] Experiment peut utiliser '
                         "tes données pour l'entraînement).\n"
                         '3. **API Keys** → **Create new key**.\n'
                         '4. Utilise `/yatb keys add`, choisis **Mistral** et colle la clé.',
        'guide_novita': "1. Connecte-toi sur novita.ai et ajoute du crédit (il n'y a pas de forfait [Free]).\n"
                        '2. Crée une clé dans **Key Management**.\n'
                        '3. Utilise `/yatb keys add` et choisis **Novita**.',
        'guide_plan': 'Forfait',
        'guide_plan_free_paid': 'Les clés [Free] et [Paid] sont possibles. Avec une clé [Free], les limites du '
                                "fournisseur s'appliquent ; avec une clé [Paid], tu définis un budget mensuel.",
        'guide_plan_paid_only': 'Seules les clés [Paid] (projet/compte avec facturation) peuvent être utilisées.',
        'guide_privacy': 'Confidentialité',
        'guide_steps': 'Étapes',
        'guide_title': '🔑 Comment obtenir une clé API {provider}',
        'info_desc': 'YATB connecte des salons textuels de différentes langues via des ponts de traduction : un '
                     'message dans un salon apparaît traduit dans tous les autres, incluant les réponses, '
                     'modifications, suppressions et fils de discussion.',
        'info_f1_name': '1. Connecter des salons',
        'info_f1_val': '`/yatb bridge add` ajoute un salon à un Bridge - les salons portant le même nom de Bridge sont '
                       'traduits entre eux.\n'
                       '*Exemple :* `/yatb bridge add chat #anglais Anglais` et `/yatb bridge add chat #allemand '
                       'Allemand`. Aperçu : `/yatb bridge list`.\n'
                       'Les salons forum et média fonctionnent de la même manière (forum avec forum). Pour les tags '
                       'automatiques, YATB a besoin de la permission *Gérer les salons* - le plus simple est de '
                       "l'appliquer à la catégorie des forums.",
        'info_f2_name': '2. Services de traduction',
        'info_f2_val': 'Sans clé, YATB traduit avec LibreTranslate (local, [Free], qualité basique). De meilleurs '
                       'résultats avec tes propres clés API : `/yatb keys add` (fournisseurs IA, Google, Azure). Ordre '
                       ': IA → Google → Azure → Libre. Comment obtenir une clé : `/yatb guide`.',
        'info_f3_name': '3. Utilisation et limites',
        'info_f3_val': "`/yatb keys list` affiche l'utilisation par clé, `/yatb keys edit` modifie le forfait, le "
                       'budget et la limite. Les alertes à 90/95/100 % sont envoyées dans le salon de log (`/yatb log '
                       'set`).',
        'info_f4_name': '4. État',
        'info_f4_val': "`/yatb status` affiche la chaîne de traduction de ce serveur et l'état de chaque service.",
        'info_f5_name': '5. Confidentialité et réinitialisation',
        'info_f5_val': 'Les membres peuvent choisir `/yatb-user privacy` → *Local only* : leurs messages ne sont alors '
                       "traduits qu'en local et jamais envoyés à des tiers.\n"
                       '• `/yatb reset` : supprime tous les ponts, clés et paramètres.\n'
                       '• `/yatb uninstall` : supprime toutes les données et le bot quitte le serveur.',
        'info_title': '🌐 YATB (Yet Another Translation Bot) - Guide',
        'key_rejected': '🔑 {provider} a rejeté la clé API de ce serveur ({status}). La clé est ignorée pendant 1 heure '
                        'et le moteur suivant est utilisé. Vérifie-la avec `/yatb keys list` ou remplace-la avec '
                        '`/yatb keys add`.',
        'keys_bad_format': "❌ Cela ne ressemble pas à une clé API (16-512 caractères, sans espaces). Rien n'a été "
                           'enregistré.',
        'keys_budget': 'budget',
        'keys_confirm_limit_off': "⚠️ **Désactiver la limite d'utilisation pour {desc} ?**\n"
                                  "Le bot continuera d'utiliser cette clé au-delà des limites [Free]/plan. Tous les "
                                  'frais facturés par le fournisseur sont **sous ta responsabilité**.',
        'keys_confirm_remove': "⚠️ Supprimer la clé {desc} ? Les traductions avec cette clé s'arrêteront "
                               'immédiatement.',
        'keys_duplicate': 'ℹ️ Cette clé est déjà enregistrée sur ce serveur : {desc}.',
        'keys_error': "❌ La clé n'a pas pu être traitée. Aucun changement effectué.",
        'keys_limit': 'limite',
        'keys_limit_off': "⚠️ Limite d'utilisation désactivée pour {desc}.",
        'keys_limit_on': "✅ Limite d'utilisation activée pour {desc}.",
        'keys_no_crypto': "🔒 Le stockage des clés n'est pas encore disponible : l'opérateur du bot n'a pas configuré "
                          'la clé maîtresse.',
        'keys_none': "Aucune clé API n'est enregistrée sur ce serveur. Ajoutes-en une avec `/yatb keys add`.",
        'keys_not_found': "⚠️ Cette clé n'a pas été trouvée sur ce serveur.",
        'keys_off': 'désactivé',
        'keys_on': 'activé',
        'keys_paid_only': "ℹ️ {provider} n'est utilisé qu'avec des clés [Paid] (facturation activée), la clé a donc "
                          'été enregistrée comme **[Paid]**.',
        'keys_region_needed': "❌ Azure nécessite la région de ta ressource Translator (ex: `westeurope`). Rien n'a été "
                              'enregistré.',
        'keys_rejected': "❌ {provider} a rejeté cette clé ({status}). Elle n'a pas été enregistrée.",
        'keys_removed': '🗑️ Clé supprimée : {desc}.',
        'keys_saved': '🔑 Clé enregistrée : {desc}. Elle est stockée de manière chiffrée et ne sera jamais affichée à '
                      'nouveau.',
        'keys_shared_tag': ' · 🔗 également utilisée sur un autre serveur',
        'keys_shared_warn': "⚠️ Cette clé est déjà utilisée sur un autre serveur. L'utilisation et la limite sont "
                            'comptabilisées ensemble.',
        'keys_title': '🔑 Clés API de ce serveur',
        'keys_too_many': "❌ Ce serveur possède déjà {max} clés. Supprimes-en une d'abord (`/yatb keys remove`).",
        'keys_unverified': "⚠️ {provider} n'a pas pu être contacté pour vérifier la clé ({status}) ; elle a été "
                           'enregistrée malgré tout.',
        'keys_updated': '✅ Paramètres enregistrés : {desc}',
        'keys_usage_line': "  ↳ mois : {month} · aujourd'hui : {today}",
        'list_field': 'Bridge : {bridge}',
        'list_footer': 'Moteurs : {engines} | Journal : {log}',
        'model_missing': "⚠️ {provider} : le modèle `{model}` n'est pas disponible (supprimé ou renommé par le "
                         "fournisseur). Il est ignoré pendant 6 heures ; l'opérateur du bot doit mettre à jour la "
                         'configuration du fournisseur.',
        'no_bridges': 'Aucun bridge sur ce serveur pour le moment. Utilise `/yatb bridge add`.',
        'none': 'Aucun',
        'none_set': 'non défini',
        'not_yours': 'Seule la personne ayant utilisé la commande peut interagir avec ces boutons.',
        'offline': '🔴 Hors ligne',
        'online': '🟢 En ligne ({ms} ms)',
        'perms_missing': '⚠️ Permissions manquantes dans {channel} : {perms}. Le bridge pourrait ne pas fonctionner '
                         "tant qu'elles ne sont pas accordées.",
        'privacy_btn_local': 'Utiliser Local uniquement',
        'privacy_btn_standard': 'Utiliser Standard',
        'privacy_local_desc': 'Tes messages restent avec le bot : ils sont traduits uniquement par LibreTranslate sur '
                              'son propre serveur et ne sont jamais envoyés aux fournisseurs IA, Google ou Azure - ni '
                              "utilisés comme contexte pour les traductions d'autres personnes. La qualité de "
                              "traduction est inférieure. S'applique sur tous les serveurs avec YATB.",
        'privacy_local_name': 'Local uniquement',
        'privacy_standard_desc': 'Meilleure qualité. Tes messages peuvent être envoyés aux services de traduction '
                                 'ajoutés par les administrateurs du serveur (ex: fournisseurs IA, Google, Azure). Les '
                                 'administrateurs choisissent ces services.',
        'privacy_standard_name': 'Standard',
        'privacy_state_local': 'Paramètre actuel : **Local only**.',
        'privacy_state_standard': 'Paramètre actuel : **Standard**.',
        'privacy_title': '🔒 Confidentialité de tes traductions',
        'provider_quota': '⚠️ {provider} signale que le quota de la clé de ce serveur est épuisé. La clé est suspendue '
                          "jusqu'à 00:00 UTC ; les traductions utilisent le moteur suivant.",
        'rep_added': '➕ **Bridge :** {user} a ajouté {channel} à `{bridge}` ({lang}).',
        'rep_channel_set': 'ℹ️ {channel} est désormais le canal de logs.',
        'rep_key_added': '🔑 {user} a ajouté une clé API : {desc}.',
        'rep_key_edited': 'ℹ️ {user} a modifié les paramètres de {desc}.',
        'rep_key_limit': "ℹ️ {user} a défini la limite d'utilisation de {desc} sur **{state}**.",
        'rep_key_removed': '🗑️ {user} a supprimé une clé API : {desc}.',
        'rep_order_reset': "🔀 {user} a réinitialisé l'ordre des services de traduction par défaut : {order}.",
        'rep_order_set': "🔀 {user} a modifié l'ordre des services de traduction : {order}.",
        'rep_removed': '🗑️ **Bridge :** {user} a retiré {channel} ({lang}) du `{bridge}`.',
        'rep_tags_full': '⚠️ {channel} a déjà 20 tags (limite de Discord) - impossible de créer un tag correspondant.',
        'rep_tags_no_permission': "⚠️ YATB n'a pas pu créer de tag correspondant dans {channel} : la permission "
                                  '**Gérer les salons** est manquante.',
        'report_channel_cleared': '📢 Canal de logs désactivé.',
        'report_channel_set': '📢 Canal de logs défini sur {channel}.',
        'reset_done': '🔄 Tous les [Bridge], liens webhook, clés et paramètres de ce serveur ont été supprimés.',
        'send_forbidden': "⚠️ Je n'ai pas les permissions nécessaires pour transférer des messages dans {channel} "
                          '(Gérer les webhooks, Créer des fils publics, Envoyer des messages dans les fils).',
        'stage_active': 'actif',
        'stage_exhausted': '🚫 Limite atteinte',
        'stage_paused': '⏸ en pause (erreurs)',
        'status_chain': '🔗 Chaîne de traduction (dans cet ordre)',
        'status_stats': '• Bridges : `{b}`\n• Salons : `{c}`\n• Suivi des messages : `{m}`',
        'status_stats_name': '📊 Statistiques du serveur',
        'status_title': '🛠️ État du système YATB',
        'tier_free': '[Free]',
        'tier_paid': '[Paid]',
        'uninstall_done': '👋 Toutes les données ont été supprimées. YATB quitte maintenant le serveur.',
        'usage_full': "🚫 Clé {desc} : limite mensuelle atteinte ({usage}). La clé est suspendue jusqu'au 1er du mois "
                      "prochain (00:00 UTC) ou jusqu'à ce que sa limite soit augmentée ; les traductions utilisent le "
                      'moteur suivant.',
        'usage_full_nolimit': '⚠️ Clé {desc} : limite mensuelle dépassée ({usage}). La limite est désactivée pour '
                              "cette clé, elle continue donc d'être utilisée - tous les frais sont à la charge de "
                              "l'administrateur.",
        'usage_warn': '⚠️ Clé {desc} : **{pct}%** de la limite mensuelle utilisée ({usage}).',
        'user_help_desc': "Ce serveur connecte des salons dans différentes langues. Quand tu écris dans l'un d'eux, "
                          'YATB publie une traduction dans les autres sous ton nom. Les réponses, modifications, '
                          'suppressions et réactions sont synchronisées. YATB ne stocke pas le texte des messages, '
                          'seulement quel message correspond à quelle traduction (7 jours).',
        'user_help_privacy': 'Avec `/yatb-user privacy`, tu peux décider que tes messages soient traduits uniquement '
                             'en local et jamais envoyés à des tiers.',
        'user_help_privacy_name': 'Ton choix',
        'user_help_tags': '`[AI]` fournisseur IA · `[Google]` Google Translate · `[Azure]` Azure Translator · '
                          '`[Libre]` LibreTranslate (local) · `[Raw]` non traduit (aucun service disponible)',
        'user_help_tags_name': 'Ce que signifie le tag après le nom',
        'user_help_title': 'ℹ️ YATB - ponts de traduction',
        'welcome': "Salut {name} ! Merci d'avoir ajouté **YATB** à **{guild}**.\n"
                   '• Commence avec `/yatb info`.\n'
                   '• Ajoute une clé de traduction avec `/yatb keys add` (comment en obtenir une : `/yatb guide`).'},
 'it': {'bad_bridge': 'Inserisci il nome di un bridge.',
        'bridge_kind_mismatch': '❌ I forum possono essere collegati solo con forum, i canali testuali solo con canali '
                                "testuali. Il Bridge `{bridge}` contiene già l'altro tipo: usa un nome di bridge "
                                'diverso.',
        'bridges_title': '🌐 Bridge su questo server',
        'btn_cancel': 'Annulla',
        'btn_confirm': 'Conferma',
        'cancelled': 'Annullato.',
        'channel_added': '✅ Canale {channel} aggiunto al bridge `{bridge}` ({lang}).',
        'channel_not_found': '⚠️ Il canale {channel} non fa parte di alcun bridge su questo server.',
        'channel_removed': '🗑️ Canale {channel} rimosso dal bridge `{bridge}`.',
        'channels_bridges': 'Bridge YATB',
        'channels_bridges_value': "**{channels}** canali in **{bridges}** bridge. Aggiungere un'altra lingua a ogni "
                                  'bridge richiede **{per_lang}** nuovi canali.',
        'channels_title': '📊 Canali su questo server',
        'channels_total': '**{total} di {limit}** canali utilizzati ({pct} %) - **{free}** ancora liberi.\\nDiscord '
                          'consente 500 canali per server; le categorie contano, i thread no.',
        'channels_type_category': '📁 Categorie',
        'channels_type_forum': '🗂️ Forum',
        'channels_type_media': '🖼️ Media',
        'channels_type_news': '📢 Annunci',
        'channels_type_stage': '🎙️ Stage',
        'channels_type_text': '💬 Testo',
        'channels_type_voice': '🔊 Voce',
        'channels_types': 'Per tipo',
        'channels_warn': 'Rimangono solo **{free}** canali. Rimuovi i canali inutilizzati prima di aggiungere nuove '
                         'lingue.',
        'confirm_reset': '⚠️ Questo eliminerà **tutti** i Bridge, le chiavi e le impostazioni di questo server. '
                         'Continuare?',
        'confirm_uninstall': '⚠️ Questo eliminerà **tutti** i dati di questo server e il bot uscirà. Continuare?',
        'default': 'predefinito',
        'error': '🔴 Errore',
        'form_budget': 'Budget mensile (solo [Paid])',
        'form_budget_desc': 'es. 8.50 EUR o 10 USD. Vuoto = predefinito ({default}).',
        'form_budget_invalid': '❌ Budget non riconosciuto. Usa es. `8.50 EUR` o `10 USD` (max. 1000). Non è stato '
                               'modificato nulla.',
        'form_key': 'Chiave API',
        'form_key_desc': 'Archiviata in modo criptato e mai più mostrata.',
        'form_label': 'Nome (opzionale)',
        'form_label_desc': 'Per distinguere le tue chiavi, es. principale',
        'form_limit': 'Limite di utilizzo',
        'form_limit_desc': 'Attivo = interrompi al raggiungimento dei limiti del piano o del budget (consigliato)',
        'form_pick_intro': 'Per quale servizio è la chiave? Sceglilo qui sotto: si aprirà un modulo specifico per quel '
                           'servizio. La chiave verrà inserita solo lì.',
        'form_pick_provider': 'Scegli un servizio di traduzione',
        'form_region': 'Regione Azure',
        'form_region_desc': 'Posizione della tua risorsa Translator, es. westeurope',
        'form_tier': 'Piano',
        'form_tier_desc': '[Free]: si applicano i limiti del provider. [Paid]: budget mensile.',
        'form_title_add': 'Aggiungi chiave {provider}',
        'form_title_edit': 'Modifica chiave {provider}',
        'forum_tags_hint': 'ℹ️ Per creare i tag mancanti in {channel}, YATB ha bisogno del permesso **Gestisci '
                           'canali** in questo forum. Senza di esso, verranno abbinati solo i tag con lo stesso nome.',
        'guide_azure': '1. In portal.azure.com crea una risorsa **Translator** (piano tariffario **F0** = 2 milioni di '
                       'caratteri al mese [Free]).\n'
                       '2. Apri **Keys and Endpoint**: copia **Key 1** e la **Location/Region** (es. westeurope).\n'
                       '3. Esegui `/yatb keys add`, scegli **Azure Translator** e inserisci chiave e regione.',
        'guide_footer': 'I nomi dei menu nei provider possono cambiare. Consiglio: imposta anche un limite di spesa '
                        'nel tuo account provider.',
        'guide_gemini': '1. Apri aistudio.google.com e accedi con il tuo account Google.\n'
                        '2. Crea o scegli un progetto Google Cloud e **abilita la fatturazione** (il piano [Free] '
                        'potrebbe non essere utilizzabile per utenti in SEE, Regno Unito o Svizzera).\n'
                        '3. **Get API key** → **Create API key** per questo progetto.\n'
                        '4. Esegui `/yatb keys add`, scegli **Google Gemini** e incolla la chiave.',
        'guide_google_translate': '1. Apri console.cloud.google.com e crea un progetto.\n'
                                  '2. Abilita la **Cloud Translation API** (è richiesto un account di fatturazione; i '
                                  'primi 500.000 caratteri al mese sono [Free]).\n'
                                  '3. **APIs & Services → Credentials → Create credentials → API key**, quindi limita '
                                  'la chiave alla Cloud Translation API.\n'
                                  '4. Esegui `/yatb keys add` e scegli **Google Translate**.',
        'guide_groq': '1. Accedi su console.groq.com.\n'
                      '2. Consigliato: abilita la conservazione zero dei dati in **Settings → Data Controls**.\n'
                      '3. **API Keys** → **Create API Key**.\n'
                      '4. Esegui `/yatb keys add` e scegli **Groq**. Il piano [Free] ha limiti bassi (circa 30 '
                      'richieste al minuto).',
        'guide_mistral': '1. Accedi su console.mistral.ai.\n'
                         '2. Sotto **Billing** scegli un piano [Paid] (il piano [Free] Experiment potrebbe usare i '
                         "tuoi dati per l'addestramento).\n"
                         '3. **API Keys** → **Create new key**.\n'
                         '4. Esegui `/yatb keys add`, scegli **Mistral** e incolla la chiave.',
        'guide_novita': '1. Accedi su novita.ai e aggiungi credito (non esiste un piano [Free]).\n'
                        '2. Crea una chiave in **Key Management**.\n'
                        '3. Esegui `/yatb keys add` e scegli **Novita**.',
        'guide_plan': 'Piano',
        'guide_plan_free_paid': 'Sono possibili chiavi [Free] e [Paid]. Con una chiave [Free] si applicano i limiti '
                                'del provider; con una chiave [Paid] imposti un budget mensile.',
        'guide_plan_paid_only': 'È possibile utilizzare solo chiavi [Paid] (progetto/account con fatturazione).',
        'guide_privacy': 'Privacy',
        'guide_steps': 'Passaggi',
        'guide_title': '🔑 Come ottenere una chiave API {provider}',
        'info_desc': 'YATB collega canali testuali di lingue diverse in Bridge di traduzione: un messaggio in un '
                     'canale appare tradotto in tutti gli altri, incluse risposte, modifiche, eliminazioni e thread.',
        'info_f1_name': '1. Collega i canali',
        'info_f1_val': '`/yatb bridge add` aggiunge un canale a un bridge: i canali con lo stesso nome bridge vengono '
                       'tradotti tra loro.\n'
                       '*Esempio:* `/yatb bridge add chat #inglese Inglese` e `/yatb bridge add chat #tedesco '
                       'Tedesco`. Panoramica: `/yatb bridge list`.\n'
                       'I canali forum e media funzionano allo stesso modo (forum con forum). Per i tag automatici, '
                       'YATB necessita del permesso *Gestisci canali* lì; il modo più semplice è impostarlo sulla '
                       'categoria dei forum.',
        'info_f2_name': '2. Servizi di traduzione',
        'info_f2_val': 'Senza chiavi, YATB traduce con LibreTranslate (locale, [Free], qualità base). Risultati '
                       'migliori con le tue chiavi API: `/yatb keys add` (provider IA, Google, Azure). Ordine: IA → '
                       'Google → Azure → Libre. Come ottenere una chiave: `/yatb guide`.',
        'info_f3_name': '3. Utilizzo e limiti',
        'info_f3_val': "`/yatb keys list` mostra l'utilizzo per chiave, `/yatb keys edit` modifica piano, budget e "
                       'limite. Gli avvisi al 90/95/100% vengono inviati al canale di log (`/yatb log set`).',
        'info_f4_name': '4. Stato',
        'info_f4_val': '`/yatb status` mostra la catena di traduzione di questo server e lo stato di ogni servizio.',
        'info_f5_name': '5. Privacy e reset',
        'info_f5_val': 'I membri possono scegliere `/yatb-user privacy` → *Solo locale*: i loro messaggi verranno '
                       'tradotti solo localmente e mai inviati a terze parti.\n'
                       '• `/yatb reset`: elimina tutti i bridge, le chiavi e le impostazioni.\n'
                       '• `/yatb uninstall`: elimina tutti i dati e il bot lascia il server.',
        'info_title': '🌐 YATB (Yet Another Translation Bot) - Guida',
        'key_rejected': '🔑 {provider} ha rifiutato la chiave API di questo server ({status}). La chiave viene ignorata '
                        'per 1 ora e viene utilizzato il motore successivo. Controllala con `/yatb keys list` o '
                        'sostituiscila con `/yatb keys add`.',
        'keys_bad_format': '❌ Non sembra una chiave API valida (16-512 caratteri, senza spazi). Non è stato salvato '
                           'nulla.',
        'keys_budget': 'budget',
        'keys_confirm_limit_off': '⚠️ **Disabilitare il limite di utilizzo per {desc}?**\n'
                                  'Il bot continuerà a utilizzare questa chiave oltre i limiti [Free]/piano. Eventuali '
                                  'costi addebitati dal provider sono **tua responsabilità**.',
        'keys_confirm_remove': '⚠️ Rimuovere la chiave {desc}? Le traduzioni con questa chiave si interromperanno '
                               'immediatamente.',
        'keys_duplicate': 'ℹ️ Questa chiave è già memorizzata su questo server: {desc}.',
        'keys_error': '❌ La chiave non può essere elaborata. Non è stato modificato nulla.',
        'keys_limit': 'limite',
        'keys_limit_off': '⚠️ Limite di utilizzo disabilitato per {desc}.',
        'keys_limit_on': '✅ Limite di utilizzo abilitato per {desc}.',
        'keys_no_crypto': "🔒 Archiviazione chiavi non ancora disponibile: l'operatore del bot non ha configurato la "
                          'chiave master.',
        'keys_none': 'Nessuna chiave API memorizzata su questo server. Aggiungine una con `/yatb keys add`.',
        'keys_not_found': '⚠️ Questa chiave non è stata trovata su questo server.',
        'keys_off': 'disattivo',
        'keys_on': 'attivo',
        'keys_paid_only': 'ℹ️ {provider} viene utilizzato solo con chiavi [Paid] (fatturazione abilitata), quindi la '
                          'chiave è stata salvata come **[Paid]**.',
        'keys_region_needed': '❌ Azure richiede la regione della tua risorsa Translator (es. `westeurope`). Non è '
                              'stato salvato nulla.',
        'keys_rejected': '❌ {provider} ha rifiutato questa chiave ({status}). Non è stata salvata.',
        'keys_removed': '🗑️ Chiave rimossa: {desc}.',
        'keys_saved': '🔑 Chiave salvata: {desc}. È archiviata in modo criptato e non verrà mai più mostrata.',
        'keys_shared_tag': ' · 🔗 utilizzata anche su un altro server',
        'keys_shared_warn': "⚠️ Questa chiave è già utilizzata su un altro server. L'utilizzo e il limite vengono "
                            'conteggiati insieme.',
        'keys_title': '🔑 Chiavi API di questo server',
        'keys_too_many': '❌ Questo server ha già {max} chiavi. Rimuovine prima una (`/yatb keys remove`).',
        'keys_unverified': '⚠️ Impossibile contattare {provider} per verificare la chiave ({status}); è stata comunque '
                           'salvata.',
        'keys_updated': '✅ Impostazioni salvate: {desc}',
        'keys_usage_line': '  ↳ mese: {month} · oggi: {today}',
        'list_field': 'Bridge: {bridge}',
        'list_footer': 'Motori: {engines} | Log: {log}',
        'model_missing': '⚠️ {provider}: il modello `{model}` non è disponibile (rimosso o rinominato dal provider). '
                         "Viene ignorato per 6 ore; l'operatore del bot deve aggiornare la configurazione del "
                         'provider.',
        'no_bridges': 'Non ci sono ancora bridge su questo server. Usa `/yatb bridge add`.',
        'none': 'Nessuno',
        'none_set': 'non impostato',
        'not_yours': 'Solo chi ha eseguito il comando può usare questi pulsanti.',
        'offline': '🔴 Offline',
        'online': '🟢 Online ({ms} ms)',
        'perms_missing': '⚠️ Permessi mancanti in {channel}: {perms}. Il bridge potrebbe non funzionare finché non '
                         'verranno concessi.',
        'privacy_btn_local': 'Usa Solo locale',
        'privacy_btn_standard': 'Usa Standard',
        'privacy_local_desc': 'I tuoi messaggi restano nel bot: vengono tradotti solo da LibreTranslate sul suo server '
                              'e non vengono mai inviati a provider IA, Google o Azure, nemmeno come contesto per le '
                              'traduzioni di altre persone. La qualità della traduzione è inferiore. Si applica a '
                              'tutti i server con YATB.',
        'privacy_local_name': 'Solo locale',
        'privacy_standard_desc': 'Qualità migliore. I tuoi messaggi potrebbero essere inviati ai servizi di traduzione '
                                 'aggiunti dagli amministratori del server (es. provider IA, Google, Azure). Gli '
                                 'amministratori scelgono questi servizi.',
        'privacy_standard_name': 'Standard',
        'privacy_state_local': 'Impostazione attuale: **Solo locale**.',
        'privacy_state_standard': 'Impostazione attuale: **Standard**.',
        'privacy_title': '🔒 La tua privacy nelle traduzioni',
        'provider_quota': '⚠️ {provider} segnala che la quota della chiave di questo server è esaurita. La chiave è in '
                          'pausa fino alle 00:00 UTC; le traduzioni useranno il motore successivo.',
        'rep_added': '➕ **Bridge:** {user} ha aggiunto {channel} a `{bridge}` ({lang}).',
        'rep_channel_set': 'ℹ️ {channel} è ora il canale log.',
        'rep_key_added': '🔑 {user} ha aggiunto una chiave API: {desc}.',
        'rep_key_edited': 'ℹ️ {user} ha modificato le impostazioni di {desc}.',
        'rep_key_limit': 'ℹ️ {user} ha impostato il limite di utilizzo di {desc} su **{state}**.',
        'rep_key_removed': '🗑️ {user} ha rimosso una chiave API: {desc}.',
        'rep_order_reset': "🔀 {user} ha ripristinato l'ordine predefinito dei servizi di traduzione: {order}.",
        'rep_order_set': "🔀 {user} ha modificato l'ordine dei servizi di traduzione: {order}.",
        'rep_removed': '🗑️ **Bridge:** {user} ha rimosso {channel} ({lang}) da `{bridge}`.',
        'rep_tags_full': '⚠️ {channel} ha già 20 tag (limite di Discord): non è stato possibile creare un tag '
                         'corrispondente.',
        'rep_tags_no_permission': '⚠️ YATB non è riuscito a creare un tag corrispondente in {channel}: manca il '
                                  'permesso **Gestisci canali**.',
        'report_channel_cleared': '📢 Canale log disattivato.',
        'report_channel_set': '📢 Canale log impostato su {channel}.',
        'reset_done': '🔄 Tutti i Bridge, i collegamenti webhook, le chiavi e le impostazioni di questo server sono '
                      'stati eliminati.',
        'send_forbidden': '⚠️ Non ho i permessi per inviare messaggi nel bridge in {channel} (Gestisci Webhook, Crea '
                          'thread pubblici, Invia messaggi nei thread).',
        'stage_active': 'attivo',
        'stage_exhausted': '🚫 Limite raggiunto',
        'stage_paused': '⏸ in pausa (errori)',
        'status_chain': '🔗 Catena di traduzione (in questo ordine)',
        'status_stats': '• Bridge: `{b}`\n• Canali: `{c}`\n• Tracker messaggi: `{m}`',
        'status_stats_name': '📊 Statistiche del server',
        'status_title': '🛠️ Stato del sistema YATB',
        'tier_free': '[Free]',
        'tier_paid': '[Paid]',
        'uninstall_done': '👋 Tutti i dati sono stati eliminati. YATB sta lasciando il server.',
        'usage_full': '🚫 Chiave {desc}: limite mensile raggiunto ({usage}). La chiave è in pausa fino al 1° del mese '
                      'prossimo (00:00 UTC) o finché il limite non viene aumentato; le traduzioni useranno il motore '
                      'successivo.',
        'usage_full_nolimit': '⚠️ Chiave {desc}: limite mensile superato ({usage}). Il limite è disattivato per questa '
                              'chiave, quindi continuerà a essere utilizzata - eventuali costi sono responsabilità '
                              "dell'amministratore.",
        'usage_warn': '⚠️ Chiave {desc}: **{pct}%** del limite mensile utilizzato ({usage}).',
        'user_help_desc': 'Questo server collega canali in lingue diverse. Quando scrivi in uno di essi, YATB pubblica '
                          'una traduzione negli altri a tuo nome. Risposte, modifiche, eliminazioni e reazioni vengono '
                          'replicate. YATB non memorizza i testi dei messaggi, ma solo a quale traduzione appartiene '
                          'ogni messaggio (7 giorni).',
        'user_help_privacy': 'Con `/yatb-user privacy` puoi decidere che i tuoi messaggi vengano tradotti solo '
                             'localmente e mai inviati a terze parti.',
        'user_help_privacy_name': 'La tua scelta',
        'user_help_tags': '`[AI]` provider IA · `[Google]` Google Translate · `[Azure]` Azure Translator · `[Libre]` '
                          'LibreTranslate (locale) · `[Raw]` non tradotto (nessun servizio disponibile)',
        'user_help_tags_name': 'Cosa significa il tag dopo il nome',
        'user_help_title': 'ℹ️ YATB - [Bridge] di traduzione',
        'welcome': 'Ciao {name}! Grazie per aver aggiunto **YATB** a **{guild}**.\n'
                   '• Inizia con `/yatb info`.\n'
                   '• Aggiungi una chiave di traduzione con `/yatb keys add` (come ottenerla: `/yatb guide`).'},
 'nl': {'bad_bridge': 'Voer een bridge-naam in.',
        'bridge_kind_mismatch': '❌ Forums kunnen alleen met forums worden gekoppeld, tekstkanalen alleen met '
                                'tekstkanalen. Bridge `{bridge}` bevat al het andere type - gebruik een andere '
                                'bridge-naam.',
        'bridges_title': '🌐 Bridges op deze server',
        'btn_cancel': 'Annuleren',
        'btn_confirm': 'Bevestigen',
        'cancelled': 'Geannuleerd.',
        'channel_added': '✅ Kanaal {channel} toegevoegd aan bridge `{bridge}` ({lang}).',
        'channel_not_found': '⚠️ Kanaal {channel} maakt op deze server geen deel uit van een bridge.',
        'channel_removed': '🗑️ Kanaal {channel} verwijderd uit bridge `{bridge}`.',
        'channels_bridges': 'YATB bridges',
        'channels_bridges_value': '**{channels}** kanalen in **{bridges}** bridges. Voor elke extra taal per bridge '
                                  'zijn **{per_lang}** nieuwe kanalen nodig.',
        'channels_title': '📊 Kanalen op deze server',
        'channels_total': '**{total} van {limit}** kanalen gebruikt ({pct} %) - **{free}** nog vrij.\\nDiscord staat '
                          '500 kanalen per server toe; categorieën tellen mee, threads niet.',
        'channels_type_category': '📁 Categorieën',
        'channels_type_forum': '🗂️ Forum',
        'channels_type_media': '🖼️ Media',
        'channels_type_news': '📢 Aankondiging',
        'channels_type_stage': '🎙️ Podium',
        'channels_type_text': '💬 Tekst',
        'channels_type_voice': '🔊 Spraak',
        'channels_types': 'Per type',
        'channels_warn': 'Nog maar **{free}** kanalen over. Verwijder ongebruikte kanalen voordat je nieuwe talen '
                         'toevoegt.',
        'confirm_reset': '⚠️ Dit verwijdert **alle** bridges, sleutels en instellingen van deze server. Doorgaan?',
        'confirm_uninstall': '⚠️ Dit verwijdert **alle** gegevens van deze server en de bot zal de server verlaten. '
                             'Doorgaan?',
        'default': 'standaard',
        'error': '🔴 Fout',
        'form_budget': 'Maandelijks budget (alleen Paid)',
        'form_budget_desc': 'bijv. 8.50 EUR of 10 USD. Leeg = standaard ({default}).',
        'form_budget_invalid': '❌ Budget niet begrepen. Gebruik bijv. `8.50 EUR` of `10 USD` (max. 1000). Er is niets '
                               'gewijzigd.',
        'form_key': 'API-sleutel',
        'form_key_desc': 'Wordt versleuteld opgeslagen en nooit meer getoond.',
        'form_label': 'Naam (optioneel)',
        'form_label_desc': 'Om je sleutels uit elkaar te houden, bijv. main',
        'form_limit': 'Gebruikslimiet',
        'form_limit_desc': 'Aan = stoppen bij de planlimieten of het budget (aanbevolen)',
        'form_pick_intro': 'Voor welke service is de sleutel? Kies hieronder - er opent daarna een formulier specifiek '
                           'voor deze service. De sleutel wordt alleen daar ingevoerd.',
        'form_pick_provider': 'Kies een vertaalservice',
        'form_region': 'Azure-regio',
        'form_region_desc': 'Locatie van je Translator-resource, bijv. westeurope',
        'form_tier': 'Plan',
        'form_tier_desc': 'Free: de limieten van de provider gelden. Paid: maandelijks budget.',
        'form_title_add': '{provider}-sleutel toevoegen',
        'form_title_edit': '{provider}-sleutel bewerken',
        'forum_tags_hint': 'ℹ️ Om ontbrekende tags in {channel} zelf aan te maken, heeft YATB de toestemming **Kanalen '
                           'beheren** nodig in dit forum. Zonder deze toestemming worden alleen tags met dezelfde naam '
                           'gekoppeld.',
        'guide_azure': '1. Maak in portal.azure.com een **Translator**-resource aan (prijsniveau **F0** = 2 miljoen '
                       'tekens per maand gratis).\n'
                       '2. Open **Keys and Endpoint**: kopieer **Key 1** en de **Location/Region** (bijv. '
                       'westeurope).\n'
                       '3. Voer `/yatb keys add` uit, kies **Azure Translator** en voer de sleutel en regio in.',
        'guide_footer': 'Menunamen bij de providers kunnen veranderen. Tip: stel ook een bestedingslimiet in je '
                        'provider-account in.',
        'guide_gemini': '1. Open aistudio.google.com en log in met je Google-account.\n'
                        '2. Maak of kies een Google Cloud-project en **schakel facturering in** - de Free tier mag '
                        'niet worden gebruikt voor gebruikers in de EER, het VK of Zwitserland.\n'
                        '3. **Get API key** → **Create API key** voor dit project.\n'
                        '4. Voer `/yatb keys add` uit, kies **Google Gemini** en plak de sleutel.',
        'guide_google_translate': '1. Open console.cloud.google.com en maak een project aan.\n'
                                  '2. Schakel de **Cloud Translation API** in (een factureringsaccount is vereist; de '
                                  'eerste 500.000 tekens per maand zijn gratis).\n'
                                  '3. **APIs & Services → Credentials → Create credentials → API key**, beperk de '
                                  'sleutel vervolgens tot de Cloud Translation API.\n'
                                  '4. Voer `/yatb keys add` uit en kies **Google Translate**.',
        'guide_groq': '1. Log in op console.groq.com.\n'
                      '2. Aanbevolen: schakel zero data retention in onder **Settings → Data Controls**.\n'
                      '3. **API Keys** → **Create API Key**.\n'
                      '4. Voer `/yatb keys add` uit en kies **Groq**. Het Free plan heeft lage limieten (ongeveer 30 '
                      'verzoeken per minuut).',
        'guide_mistral': '1. Log in op console.mistral.ai.\n'
                         '2. Kies onder **Billing** een Paid plan (het gratis Experiment-plan kan je gegevens '
                         'gebruiken voor training).\n'
                         '3. **API Keys** → **Create new key**.\n'
                         '4. Voer `/yatb keys add` uit, kies **Mistral** en plak de sleutel.',
        'guide_novita': '1. Log in op novita.ai en voeg tegoed toe (er is geen Free plan).\n'
                        '2. Maak een sleutel aan onder **Key Management**.\n'
                        '3. Voer `/yatb keys add` uit en kies **Novita**.',
        'guide_plan': 'Plan',
        'guide_plan_free_paid': 'Free en Paid sleutels zijn mogelijk. Bij een Free sleutel gelden de limieten van de '
                                'provider; bij een Paid sleutel stel je een maandelijks budget in.',
        'guide_plan_paid_only': 'Alleen Paid sleutels (project/account met facturering) kunnen worden gebruikt.',
        'guide_privacy': 'Privacy',
        'guide_steps': 'Stappen',
        'guide_title': '🔑 Hoe krijg je een {provider} API-sleutel',
        'info_desc': 'YATB verbindt tekstkanalen van verschillende talen in vertaal-Bridge: een bericht in het ene '
                     'kanaal verschijnt vertaald in alle andere, inclusief antwoorden, bewerkingen, verwijderingen en '
                     'threads.',
        'info_f1_name': '1. Kanalen verbinden',
        'info_f1_val': '`/yatb bridge add` voegt een kanaal toe aan een bridge - kanalen met dezelfde bridgenaam '
                       'worden naar elkaar vertaald.\n'
                       '*Voorbeeld:* `/yatb bridge add chat #engels Engels` en `/yatb bridge add chat #duits Duits`. '
                       'Overzicht: `/yatb bridge list`.\n'
                       'Forum- en mediakanalen werken op dezelfde manier (forum met forum). Voor automatische tags '
                       'heeft YATB daar *Kanalen beheren* nodig - dit gaat het makkelijkst via de categorie van de '
                       'forums.',
        'info_f2_name': '2. Vertaaldiensten',
        'info_f2_val': 'Zonder sleutels vertaalt YATB met LibreTranslate (lokaal, Free, basiskwaliteit). Betere '
                       'resultaten met je eigen API-sleutels: `/yatb keys add` (AI-providers, Google, Azure). '
                       'Volgorde: AI → Google → Azure → Libre. Hoe je een sleutel krijgt: `/yatb guide`.',
        'info_f3_name': '3. Gebruik & limieten',
        'info_f3_val': '`/yatb keys list` toont het verbruik per sleutel, `/yatb keys edit` wijzigt plan, budget en '
                       'limiet. Waarschuwingen bij 90/95/100 % gaan naar het logkanaal (`/yatb log set`).',
        'info_f4_name': '4. Status',
        'info_f4_val': '`/yatb status` toont de vertaalketen van deze server en de status van elke dienst.',
        'info_f5_name': '5. Privacy & reset',
        'info_f5_val': 'Leden kunnen kiezen voor `/yatb-user privacy` → *Lokaal alleen*: hun berichten worden dan '
                       'alleen lokaal vertaald en nooit naar derden verzonden.\n'
                       '• `/yatb reset`: verwijdert alle Bridges, sleutels en instellingen.\n'
                       '• `/yatb uninstall`: verwijdert alle gegevens en de bot verlaat de server.',
        'info_title': '🌐 YATB (Yet Another Translation Bot) - Handleiding',
        'key_rejected': '🔑 {provider} heeft de API-sleutel van deze server geweigerd ({status}). De sleutel wordt 1 '
                        'uur overgeslagen en de volgende engine wordt gebruikt. Controleer dit met `/yatb keys list` '
                        'of vervang de sleutel met `/yatb keys add`.',
        'keys_bad_format': '❌ Dat ziet er niet uit als een API-sleutel (16-512 tekens, geen spaties). Er is niets '
                           'opgeslagen.',
        'keys_budget': 'budget',
        'keys_confirm_limit_off': '⚠️ **De gebruikslimiet voor {desc} uitschakelen?**\n'
                                  'De bot zal deze sleutel dan blijven gebruiken voorbij de Free/planlimieten. '
                                  'Eventuele kosten van de provider zijn **jouw verantwoordelijkheid**.',
        'keys_confirm_remove': '⚠️ De sleutel {desc} verwijderen? Vertalingen met deze sleutel stoppen direct.',
        'keys_duplicate': 'ℹ️ Deze sleutel is al opgeslagen op deze server: {desc}.',
        'keys_error': '❌ De sleutel kon niet worden verwerkt. Er is niets gewijzigd.',
        'keys_limit': 'limiet',
        'keys_limit_off': '⚠️ Gebruikslimiet uitgeschakeld voor {desc}.',
        'keys_limit_on': '✅ Gebruikslimiet ingeschakeld voor {desc}.',
        'keys_no_crypto': '🔒 Sleutelopslag is nog niet beschikbaar: de bot-beheerder heeft de hoofdsleutel niet '
                          'geconfigureerd.',
        'keys_none': 'Er zijn geen API-sleutels opgeslagen op deze server. Voeg er een toe met `/yatb keys add`.',
        'keys_not_found': '⚠️ Deze sleutel is niet gevonden op deze server.',
        'keys_off': 'uit',
        'keys_on': 'aan',
        'keys_paid_only': 'ℹ️ {provider} wordt alleen gebruikt met Paid-sleutels (facturering ingeschakeld), dus de '
                          'sleutel is opgeslagen als **Paid**.',
        'keys_region_needed': '❌ Azure heeft de regio van je Translator-resource nodig (bijv. `westeurope`). Er is '
                              'niets opgeslagen.',
        'keys_rejected': '❌ {provider} heeft deze sleutel geweigerd ({status}). Hij is niet opgeslagen.',
        'keys_removed': '🗑️ Sleutel verwijderd: {desc}.',
        'keys_saved': '🔑 Sleutel opgeslagen: {desc}. Deze wordt versleuteld bewaard en zal nooit meer worden getoond.',
        'keys_shared_tag': ' · 🔗 ook gebruikt op een andere server',
        'keys_shared_warn': '⚠️ Deze sleutel wordt al op een andere server gebruikt. Gebruik en limieten worden samen '
                            'geteld.',
        'keys_title': '🔑 API-sleutels van deze server',
        'keys_too_many': '❌ Deze server heeft al {max} sleutels. Verwijder er eerst een (`/yatb keys remove`).',
        'keys_unverified': '⚠️ {provider} kon niet worden bereikt om de sleutel te verifiëren ({status}); hij is toch '
                           'opgeslagen.',
        'keys_updated': '✅ Instellingen opgeslagen: {desc}',
        'keys_usage_line': '  ↳ maand: {month} · vandaag: {today}',
        'list_field': 'Bridge: {bridge}',
        'list_footer': 'Engines: {engines} | Log: {log}',
        'model_missing': '⚠️ {provider}: het model `{model}` is niet beschikbaar (verwijderd of hernoemd door de '
                         'provider). Het wordt 6 uur overgeslagen; de bot-operator moet de providerconfiguratie '
                         'bijwerken.',
        'no_bridges': 'Nog geen bridges op deze server. Gebruik `/yatb bridge add`.',
        'none': 'Geen',
        'none_set': 'niet ingesteld',
        'not_yours': 'Alleen de persoon die het commando heeft uitgevoerd kan deze knoppen gebruiken.',
        'offline': '🔴 Offline',
        'online': '🟢 Online ({ms} ms)',
        'perms_missing': '⚠️ Ontbrekende rechten in {channel}: {perms}. De bridge werkt mogelijk niet totdat deze zijn '
                         'verleend.',
        'privacy_btn_local': 'Gebruik Alleen lokaal',
        'privacy_btn_standard': 'Gebruik Standaard',
        'privacy_local_desc': 'Je berichten blijven bij de bot: ze worden alleen vertaald door LibreTranslate op zijn '
                              'eigen server en nooit verzonden naar AI-providers, Google of Azure - ook niet als '
                              'context voor vertalingen van anderen. De vertaalkwaliteit is lager. Geldt voor alle '
                              'servers met YATB.',
        'privacy_local_name': 'Alleen lokaal',
        'privacy_standard_desc': 'Beste kwaliteit. Je berichten kunnen worden verzonden naar de vertaaldiensten die de '
                                 'beheerders van de server hebben toegevoegd (bijv. AI-providers, Google, Azure). De '
                                 'beheerders kiezen deze diensten.',
        'privacy_standard_name': 'Standaard',
        'privacy_state_local': 'Huidige instelling: **Alleen lokaal**.',
        'privacy_state_standard': 'Huidige instelling: **Standaard**.',
        'privacy_title': '🔒 Jouw vertaalprivacy',
        'provider_quota': '⚠️ {provider} meldt dat het quotum van de sleutel van deze server is verbruikt. De sleutel '
                          'is gepauzeerd tot 00:00 UTC; vertalingen gebruiken de volgende engine.',
        'rep_added': '➕ **Bridge:** {user} heeft {channel} toegevoegd aan `{bridge}` ({lang}).',
        'rep_channel_set': 'ℹ️ {channel} is nu het logkanaal.',
        'rep_key_added': '🔑 {user} heeft een API-sleutel toegevoegd: {desc}.',
        'rep_key_edited': 'ℹ️ {user} heeft de instellingen van {desc} gewijzigd.',
        'rep_key_limit': 'ℹ️ {user} heeft de gebruikslimiet van {desc} ingesteld op **{state}**.',
        'rep_key_removed': '🗑️ {user} heeft een API-sleutel verwijderd: {desc}.',
        'rep_order_reset': '🔀 {user} heeft de volgorde van de vertaaldiensten gereset naar de standaard: {order}.',
        'rep_order_set': '🔀 {user} heeft de volgorde van de vertaaldiensten gewijzigd: {order}.',
        'rep_removed': '🗑️ **Bridge:** {user} heeft {channel} ({lang}) verwijderd uit `{bridge}`.',
        'rep_tags_full': '⚠️ {channel} heeft al 20 tags (Discord-limiet) - er kon geen overeenkomende tag worden '
                         'aangemaakt.',
        'rep_tags_no_permission': '⚠️ YATB kon geen overeenkomende tag aanmaken in {channel}: de toestemming **Kanalen '
                                  'beheren** ontbreekt daar.',
        'report_channel_cleared': '📢 Logkanaal uitgeschakeld.',
        'report_channel_set': '📢 Logkanaal ingesteld op {channel}.',
        'reset_done': '🔄 Alle bridges, webhook-links, sleutels en instellingen van deze server zijn verwijderd.',
        'send_forbidden': '⚠️ Ik heb onvoldoende rechten om berichten te bridgen naar {channel} (Webhooks beheren, '
                          'Openbare threads aanmaken, Berichten verzenden in threads).',
        'stage_active': 'actief',
        'stage_exhausted': '🚫 limiet bereikt',
        'stage_paused': '⏸ gepauzeerd (fouten)',
        'status_chain': '🔗 Vertaalketen (in deze volgorde)',
        'status_stats': '• Bridges: `{b}`\n• Kanalen: `{c}`\n• Berichten-tracker: `{m}`',
        'status_stats_name': '📊 Serverstatistieken',
        'status_title': '🛠️ YATB systeemstatus',
        'tier_free': 'Free',
        'tier_paid': 'Paid',
        'uninstall_done': '👋 Alle gegevens zijn verwijderd. YATB verlaat nu de server.',
        'usage_full': '🚫 Sleutel {desc}: maandelijkse limiet bereikt ({usage}). De sleutel is gepauzeerd tot de 1e van '
                      'de volgende maand (00:00 UTC) of totdat de limiet is verhoogd; vertalingen gebruiken de '
                      'volgende engine.',
        'usage_full_nolimit': '⚠️ Sleutel {desc}: maandelijkse limiet overschreden ({usage}). De limiet is '
                              'uitgeschakeld voor deze sleutel, dus hij blijft in gebruik - eventuele kosten zijn de '
                              'verantwoordelijkheid van de beheerder.',
        'usage_warn': '⚠️ Sleutel {desc}: **{pct}%** van de maandelijkse limiet verbruikt ({usage}).',
        'user_help_desc': 'Deze server verbindt kanalen in verschillende talen. Wanneer je in een van deze kanalen '
                          'schrijft, plaatst YATB een vertaling in de andere kanalen onder jouw naam. Antwoorden, '
                          'bewerkingen, verwijderingen en reacties worden gespiegeld. YATB slaat geen berichtteksten '
                          'op - alleen welk bericht bij welke vertaling hoort (7 dagen).',
        'user_help_privacy': 'Met `/yatb-user privacy` kun je beslissen dat je berichten alleen lokaal worden vertaald '
                             'en nooit naar derden worden verzonden.',
        'user_help_privacy_name': 'Jouw keuze',
        'user_help_tags': '`[AI]` AI-provider · `[Google]` Google Translate · `[Azure]` Azure Translator · `[Libre]` '
                          'LibreTranslate (lokaal) · `[Raw]` niet vertaald (geen dienst beschikbaar)',
        'user_help_tags_name': 'Wat de tag achter de naam betekent',
        'user_help_title': 'ℹ️ YATB - vertaalbridges',
        'welcome': 'Hallo {name}! Bedankt voor het toevoegen van **YATB** aan **{guild}**.\n'
                   '• Begin met `/yatb info`.\n'
                   '• Voeg een vertaalsleutel toe met `/yatb keys add` (hoe je er een krijgt: `/yatb guide`).'},
 'ru': {'bad_bridge': 'Пожалуйста, введи название моста.',
        'bridge_kind_mismatch': '❌ Форумы можно связывать только с форумами, текстовые каналы — только с текстовыми. В '
                                'Bridge `{bridge}` уже используется другой тип канала, выбери другое имя для Bridge.',
        'bridges_title': '🌐 Мосты на этом сервере',
        'btn_cancel': 'Отмена',
        'btn_confirm': 'Подтвердить',
        'cancelled': 'Отменено.',
        'channel_added': '✅ Канал {channel} добавлен в мост `{bridge}` ({lang}).',
        'channel_not_found': '⚠️ Канал {channel} не является частью ни одного моста на этом сервере.',
        'channel_removed': '🗑️ Канал {channel} удален из моста `{bridge}`.',
        'channels_bridges': 'Мосты YATB',
        'channels_bridges_value': '**{channels}** каналов в **{bridges}** мостах. Добавление еще одного языка в каждый '
                                  'мост потребует **{per_lang}** новых каналов.',
        'channels_title': '📊 Каналы на этом сервере',
        'channels_total': '**{total} из {limit}** каналов занято ({pct} %) — **{free}** еще свободно.\n'
                          'Discord позволяет иметь до 500 каналов на сервере; категории учитываются, ветки — нет.',
        'channels_type_category': '📁 Категории',
        'channels_type_forum': '🗂️ Форумы',
        'channels_type_media': '🖼️ Медиа',
        'channels_type_news': '📢 Новостные',
        'channels_type_stage': '🎙️ Сцена',
        'channels_type_text': '💬 Текстовые',
        'channels_type_voice': '🔊 Голосовые',
        'channels_types': 'По типам',
        'channels_warn': 'Осталось всего **{free}** каналов. Удали неиспользуемые каналы перед добавлением новых '
                         'языков.',
        'confirm_reset': '⚠️ Это удалит **все** [Bridge], ключи и настройки этого сервера. Продолжить?',
        'confirm_uninstall': '⚠️ Это удалит **все** данные этого сервера, и бот покинет его. Продолжить?',
        'default': 'по умолчанию',
        'error': '🔴 Ошибка',
        'form_budget': 'Ежемесячный бюджет (только для [Paid])',
        'form_budget_desc': 'Например: 8.50 EUR или 10 USD. Пусто = по умолчанию ({default}).',
        'form_budget_invalid': '❌ Бюджет не распознан. Используй, например, `8.50 EUR` или `10 USD` (макс. 1000). '
                               'Ничего не изменено.',
        'form_key': 'API-ключ',
        'form_key_desc': 'Хранится в зашифрованном виде и больше никогда не будет показан.',
        'form_label': 'Название (опционально)',
        'form_label_desc': 'Чтобы различать ключи, например: основной',
        'form_limit': 'Лимит использования',
        'form_limit_desc': 'Вкл = остановка при достижении лимитов тарифа или бюджета (рекомендуется)',
        'form_pick_intro': 'Для какого сервиса этот ключ? Выбери ниже — откроется форма именно для этого сервиса. Ключ '
                           'вводится только там.',
        'form_pick_provider': 'Выберите сервис перевода',
        'form_region': 'Регион Azure',
        'form_region_desc': 'Расположение твоего ресурса Translator, например: westeurope',
        'form_tier': 'Тариф',
        'form_tier_desc': '[Free]: действуют лимиты провайдера. [Paid]: ежемесячный бюджет.',
        'form_title_add': 'Добавить ключ {provider}',
        'form_title_edit': 'Изменить ключ {provider}',
        'forum_tags_hint': 'ℹ️ Чтобы создать недостающие теги в самом {channel}, боту YATB нужно разрешение '
                           '**Управление каналами** в этом форуме. Без него будут сопоставляться только теги с '
                           'одинаковыми названиями.',
        'guide_azure': '1. В portal.azure.com создай ресурс **Translator** (ценовой уровень **F0** = 2 млн символов в '
                       'месяц [Free]).\n'
                       '2. Открой **Keys and Endpoint**: скопируй **Key 1** и **Location/Region** (например, '
                       'westeurope).\n'
                       '3. Выполни `/yatb keys add`, выбери **Azure Translator** и введи ключ и регион.',
        'guide_footer': 'Названия меню у провайдеров могут меняться. Совет: также установи лимит расходов в аккаунте '
                        'провайдера.',
        'guide_gemini': '1. Открой aistudio.google.com и войди через Google-аккаунт.\n'
                        '2. Создай или выбери проект Google Cloud и **включи биллинг** — [Free]-тариф может быть '
                        'недоступен для пользователей из ЕЭЗ, Великобритании или Швейцарии.\n'
                        '3. **Get API key** → **Create API key** для этого проекта.\n'
                        '4. Выполни `/yatb keys add`, выбери **Google Gemini** и вставь ключ.',
        'guide_google_translate': '1. Открой console.cloud.google.com и создай проект.\n'
                                  '2. Включи **Cloud Translation API** (требуется аккаунт с биллингом; первые 500 000 '
                                  'символов в месяц — [Free]).\n'
                                  '3. **APIs & Services → Credentials → Create credentials → API key**, затем ограничь '
                                  'ключ до Cloud Translation API.\n'
                                  '4. Выполни `/yatb keys add` и выбери **Google Translate**.',
        'guide_groq': '1. Войди на console.groq.com.\n'
                      '2. Рекомендуется: включи нулевое хранение данных в **Settings → Data Controls**.\n'
                      '3. **API Keys** → **Create API Key**.\n'
                      '4. Выполни `/yatb keys add` и выбери **Groq**. [Free]-план имеет низкие лимиты (около 30 '
                      'запросов в минуту).',
        'guide_mistral': '1. Войди на console.mistral.ai.\n'
                         '2. В разделе **Billing** выбери платный план ([Free] план Experiment может использовать твои '
                         'данные для обучения).\n'
                         '3. **API Keys** → **Create new key**.\n'
                         '4. Выполни `/yatb keys add`, выбери **Mistral** и вставь ключ.',
        'guide_novita': '1. Войди на novita.ai и пополни баланс ([Free]-плана нет).\n'
                        '2. Создай ключ в **Key Management**.\n'
                        '3. Выполни `/yatb keys add` и выбери **Novita**.',
        'guide_plan': 'План',
        'guide_plan_free_paid': 'Возможны [Free] и платные ключи. С [Free]-ключом действуют лимиты провайдера; с '
                                'платным ты задаешь ежемесячный бюджет.',
        'guide_plan_paid_only': 'Можно использовать только платные ключи (проект/аккаунт с привязанной оплатой).',
        'guide_privacy': 'Приватность',
        'guide_steps': 'Шаги',
        'guide_title': '🔑 Как получить API-ключ {provider}',
        'info_desc': 'YATB объединяет текстовые каналы разных языков в мосты перевода: сообщение в одном канале '
                     'появляется переведенным во всех остальных, включая ответы, правки, удаления и ветки.',
        'info_f1_name': '1. Подключение каналов',
        'info_f1_val': '`/yatb bridge add` добавляет канал в Bridge — сообщения в каналах с одинаковым названием '
                       'Bridge будут переводиться друг в друга.\n'
                       '*Пример:* `/yatb bridge add chat #english English` и `/yatb bridge add chat #german German`. '
                       'Список всех мостов: `/yatb bridge list`.\n'
                       'Форумы и медиаканалы работают так же (форум с форумом). Для автоматических тегов YATB нужны '
                       'права *Управление каналами* — проще всего выдать их на категорию с форумами.',
        'info_f2_name': '2. Сервисы перевода',
        'info_f2_val': 'Без ключей YATB переводит через LibreTranslate (локально, [Free], базовое качество). Лучшие '
                       'результаты — с твоими API-ключами: `/yatb keys add` (ИИ-провайдеры, Google, Azure). Порядок: '
                       'ИИ → Google → Azure → Libre. Как получить ключ: `/yatb guide`.',
        'info_f3_name': '3. Использование и лимиты',
        'info_f3_val': '`/yatb keys list` показывает использование по ключу, `/yatb keys edit` меняет план, бюджет и '
                       'лимит. Предупреждения при 90/95/100% приходят в канал логов (`/yatb log set`).',
        'info_f4_name': '4. Статус',
        'info_f4_val': '`/yatb status` показывает цепочку перевода на этом сервере и состояние каждого сервиса.',
        'info_f5_name': '5. Приватность и сброс',
        'info_f5_val': 'Участники могут выбрать `/yatb-user privacy` → *Local only*: их сообщения будут переводиться '
                       'только локально и никогда не отправятся третьим лицам.\n'
                       '• `/yatb reset`: удаляет все мосты, ключи и настройки.\n'
                       '• `/yatb uninstall`: удаляет все данные, и бот покидает сервер.',
        'info_title': '🌐 YATB (Yet Another Translation Bot) — Руководство',
        'key_rejected': '🔑 {provider} отклонил API-ключ этого сервера ({status}). Ключ пропускается на 1 час, '
                        'используется следующий движок. Проверь его через `/yatb keys list` или замени через `/yatb '
                        'keys add`.',
        'keys_bad_format': '❌ Это не похоже на API-ключ (16-512 символов, без пробелов). Ничего не сохранено.',
        'keys_budget': 'бюджет',
        'keys_confirm_limit_off': '⚠️ **Выключить лимит использования для {desc}?**\n'
                                  'Бот продолжит использовать этот ключ сверх лимитов [Free]/плана. Любые расходы, '
                                  'начисленные провайдером, **на твоей ответственности**.',
        'keys_confirm_remove': '⚠️ Удалить ключ {desc}? Переводы с этим ключом немедленно прекратятся.',
        'keys_duplicate': 'ℹ️ Этот ключ уже сохранен на этом сервере: {desc}.',
        'keys_error': '❌ Не удалось обработать ключ. Ничего не изменилось.',
        'keys_limit': 'лимит',
        'keys_limit_off': '⚠️ Лимит использования выключен для {desc}.',
        'keys_limit_on': '✅ Лимит использования включен для {desc}.',
        'keys_no_crypto': '🔒 Хранилище ключей пока недоступно: оператор бота не настроил мастер-ключ.',
        'keys_none': 'На этом сервере нет сохраненных API-ключей. Добавь один с помощью `/yatb keys add`.',
        'keys_not_found': '⚠️ Ключ не найден на этом сервере.',
        'keys_off': 'выкл',
        'keys_on': 'вкл',
        'keys_paid_only': 'ℹ️ {provider} работает только с [Paid] ключами (биллинг включен), поэтому ключ был сохранен '
                          'как **[Paid]**.',
        'keys_region_needed': '❌ Для Azure нужен регион твоего ресурса Translator (например, `westeurope`). Ничего не '
                              'сохранено.',
        'keys_rejected': '❌ {provider} отклонил этот ключ ({status}). Он не был сохранен.',
        'keys_removed': '🗑️ Ключ удален: {desc}.',
        'keys_saved': '🔑 Ключ сохранен: {desc}. Он хранится в зашифрованном виде и больше никогда не будет показан.',
        'keys_shared_tag': ' · 🔗 используется также на другом сервере',
        'keys_shared_warn': '⚠️ Этот ключ уже используется на другом сервере. Использование и лимиты суммируются.',
        'keys_title': '🔑 API-ключи этого сервера',
        'keys_too_many': '❌ На этом сервере уже {max} ключей. Сначала удали один (`/yatb keys remove`).',
        'keys_unverified': '⚠️ Не удалось связаться с {provider} для проверки ключа ({status}); он был сохранен в '
                           'любом случае.',
        'keys_updated': '✅ Настройки сохранены: {desc}',
        'keys_usage_line': '  ↳ месяц: {month} · сегодня: {today}',
        'list_field': 'Мост: {bridge}',
        'list_footer': 'Движки: {engines} | Лог: {log}',
        'model_missing': '⚠️ {provider}: модель `{model}` недоступна (удалена или переименована провайдером). Она '
                         'пропускается на 6 часов; оператору бота нужно обновить конфигурацию провайдера.',
        'no_bridges': 'На этом сервере еще нет мостов. Используй `/yatb bridge add`.',
        'none': 'Нет',
        'none_set': 'не задано',
        'not_yours': 'Эти кнопки может использовать только тот, кто вызвал команду.',
        'offline': '🔴 Офлайн',
        'online': '🟢 Онлайн ({ms} мс)',
        'perms_missing': '⚠️ Недостаточно прав в {channel}: {perms}. Мост может не работать, пока они не будут '
                         'предоставлены.',
        'privacy_btn_local': 'Использовать Только локально',
        'privacy_btn_standard': 'Использовать Стандартный',
        'privacy_local_desc': 'Твои сообщения остаются у бота: они переводятся только через LibreTranslate на его '
                              'собственном сервере и никогда не отправляются ИИ провайдерам, Google или Azure — даже в '
                              'качестве контекста для переводов других людей. Качество перевода ниже. Применяется на '
                              'всех серверах с YATB.',
        'privacy_local_name': 'Только локально',
        'privacy_standard_desc': 'Лучшее качество. Твои сообщения могут отправляться в сервисы перевода, добавленные '
                                 'администраторами сервера (например, ИИ провайдеры, Google, Azure). Администраторы '
                                 'сами выбирают эти сервисы.',
        'privacy_standard_name': 'Стандартный',
        'privacy_state_local': 'Текущая настройка: **Только локально**.',
        'privacy_state_standard': 'Текущая настройка: **Стандартная**.',
        'privacy_title': '🔒 Конфиденциальность твоих переводов',
        'provider_quota': '⚠️ {provider} сообщает, что квота ключа этого сервера исчерпана. Ключ приостановлен до '
                          '00:00 UTC; переводы используют следующий движок.',
        'rep_added': '➕ **Мост:** {user} добавил {channel} в `{bridge}` ({lang}).',
        'rep_channel_set': 'ℹ️ {channel} теперь является каналом для логов.',
        'rep_key_added': '🔑 {user} добавил API-ключ: {desc}.',
        'rep_key_edited': 'ℹ️ {user} изменил настройки {desc}.',
        'rep_key_limit': 'ℹ️ {user} установил лимит использования {desc} на **{state}**.',
        'rep_key_removed': '🗑️ {user} удалил API-ключ: {desc}.',
        'rep_order_reset': '🔀 {user} сбросил(а) порядок сервисов перевода до стандартного: {order}.',
        'rep_order_set': '🔀 {user} изменил(а) порядок сервисов перевода: {order}.',
        'rep_removed': '🗑️ **Мост:** {user} удалил {channel} ({lang}) из `{bridge}`.',
        'rep_tags_full': '⚠️ В {channel} уже 20 тегов (лимит Discord) — создать подходящий тег не удалось.',
        'rep_tags_no_permission': '⚠️ YATB не смог создать подходящий тег в {channel}: отсутствует разрешение '
                                  '**Управление каналами**.',
        'report_channel_cleared': '📢 Канал логов отключен.',
        'report_channel_set': '📢 Канал логов установлен на {channel}.',
        'reset_done': '🔄 Все [Bridge], вебхуки, ключи и настройки этого сервера были удалены.',
        'send_forbidden': '⚠️ У меня нет прав для пересылки сообщений в {channel} (Управление вебхуками, Создание '
                          'публичных веток, Отправка сообщений в ветках).',
        'stage_active': 'активно',
        'stage_exhausted': '🚫 Лимит исчерпан',
        'stage_paused': '⏸ приостановлено (ошибки)',
        'status_chain': '🔗 Цепочка перевода (в этом порядке)',
        'status_stats': '• Мостов: `{b}`\n• Каналов: `{c}`\n• Трекер сообщений: `{m}`',
        'status_stats_name': '📊 Статистика сервера',
        'status_title': '🛠️ Системный статус YATB',
        'tier_free': '[Free]',
        'tier_paid': '[Paid]',
        'uninstall_done': '👋 Все данные удалены. YATB покидает сервер.',
        'usage_full': '🚫 Ключ {desc}: месячный лимит исчерпан ({usage}). Ключ приостановлен до 1-го числа следующего '
                      'месяца (00:00 UTC) или до повышения лимита; переводы используют следующий движок.',
        'usage_full_nolimit': '⚠️ Ключ {desc}: месячный лимит превышен ({usage}). Лимит для этого ключа выключен, '
                              'поэтому он продолжает использоваться — любые расходы на ответственности администратора.',
        'usage_warn': '⚠️ Ключ {desc}: использовано **{pct}%** месячного лимита ({usage}).',
        'user_help_desc': 'Этот сервер объединяет каналы на разных языках. Когда ты пишешь в одном из них, YATB '
                          'публикует перевод в остальных от твоего имени. Ответы, правки, удаления и реакции '
                          'дублируются. YATB не хранит текст сообщений — только связь между ними (7 дней).',
        'user_help_privacy': 'С помощью `/yatb-user privacy` ты можешь выбрать, чтобы твои сообщения переводились '
                             'только локально и никогда не отправлялись третьим лицам.',
        'user_help_privacy_name': 'Твой выбор',
        'user_help_tags': '`[AI]` ИИ провайдер · `[Google]` Google Translate · `[Azure]` Azure Translator · `[Libre]` '
                          'LibreTranslate (локально) · `[Raw]` без перевода (сервис недоступен)',
        'user_help_tags_name': 'Что означает тег после имени',
        'user_help_title': 'ℹ️ YATB — мосты перевода',
        'welcome': 'Привет {name}! Спасибо, что добавил **YATB** на сервер **{guild}**.\n'
                   '• Начни с `/yatb info`.\n'
                   '• Добавь ключ перевода через `/yatb keys add` (как получить: `/yatb guide`).'}}

COMMANDS_MT = {'es': {'Add a channel to a translation bridge': 'Añadir un canal a un puente de traducción',
        'Add an API key (entered in a private form, stored encrypted)': 'Añadir una clave API (se introduce en un '
                                                                        'formulario privado y se guarda cifrada)',
        'Change the settings of a key (the key itself is never shown)': 'Cambiar la configuración de una clave (la '
                                                                        'clave nunca se muestra)',
        'Choose who may translate your messages (applies on all servers)': 'Elegir quién puede traducir tus mensajes '
                                                                           '(se aplica en todos los servidores)',
        'Delete all bridges, keys and settings of this server': 'Eliminar todos los puentes, claves y ajustes de este '
                                                                'servidor',
        'Delete all data of this server and make the bot leave': 'Eliminar todos los datos de este servidor y hacer '
                                                                 'que el bot se vaya',
        'How many channels this server uses (Discord limit: 500)': 'Cuántos canales usa este servidor (límite de '
                                                                   'Discord: 500)',
        'How to get an API key for a translation service': 'Cómo obtener una clave API para un servicio de traducción',
        'Key to change': 'Clave a cambiar',
        'Key to remove': 'Clave a eliminar',
        'Language of this channel': 'Idioma de este canal',
        'List all bridges of this server': 'Listar todos los puentes de este servidor',
        'Log channel for notifications': 'Canal de registro para notificaciones',
        "Manage this server's API keys (stored encrypted)": 'Gestionar las claves API de este servidor (guardadas '
                                                            'cifradas)',
        'Manage translation bridges': 'Gestionar puentes de traducción',
        'Name of the bridge (channels with the same name are connected)': 'Nombre del puente (los canales con el mismo '
                                                                          'nombre se conectan)',
        'Remove a channel from its bridge': 'Eliminar un canal de su puente',
        'Remove an API key from this server': 'Eliminar una clave API de este servidor',
        'Set the channel for notifications (usage warnings, key problems, changes)': 'Establecer el canal para '
                                                                                     'notificaciones (avisos de uso, '
                                                                                     'problemas con claves, cambios)',
        'Setup guide and overview of all commands': 'Guía de configuración y resumen de todos los comandos',
        "Show this server's API keys and their usage (never the keys themselves)": 'Mostrar las claves API de este '
                                                                                   'servidor y su uso (nunca las '
                                                                                   'claves en sí)',
        'Text channel': 'Canal de texto',
        'Text, forum or media channel': 'Canal de texto, foro o multimedia',
        'Translation chain, usage and service health of this server': 'Cadena de traducción, uso y estado del servicio '
                                                                      'de este servidor',
        'Translation service': 'Servicio de traducción',
        'Turn off the notification channel': 'Desactivar el canal de notificaciones',
        'What this bot does with your messages': 'Qué hace este bot con tus mensajes',
        'YATB settings for your own messages': 'Ajustes de YATB para tus propios mensajes',
        'YATB translation bridges (admin settings)': 'Puentes de traducción de YATB (ajustes de administrador)'},
 'fr': {'Add a channel to a translation bridge': 'Ajouter un salon à un pont de traduction',
        'Add an API key (entered in a private form, stored encrypted)': 'Ajouter une clé API (saisie dans un '
                                                                        'formulaire privé, stockée chiffrée)',
        'Change the settings of a key (the key itself is never shown)': "Modifier les paramètres d'une clé (la clé "
                                                                        "elle-même n'est jamais affichée)",
        'Choose who may translate your messages (applies on all servers)': 'Choisir qui peut traduire tes messages '
                                                                           "(s'applique sur tous les serveurs)",
        'Delete all bridges, keys and settings of this server': 'Supprimer tous les ponts, clés et paramètres de ce '
                                                                'serveur',
        'Delete all data of this server and make the bot leave': 'Supprimer toutes les données de ce serveur et faire '
                                                                 'quitter le bot',
        'How many channels this server uses (Discord limit: 500)': 'Nombre de salons utilisés sur ce serveur (limite '
                                                                   'Discord : 500)',
        'How to get an API key for a translation service': 'Comment obtenir une clé API pour un service de traduction',
        'Key to change': 'Clé à modifier',
        'Key to remove': 'Clé à supprimer',
        'Language of this channel': 'Langue de ce salon',
        'List all bridges of this server': 'Lister tous les ponts de ce serveur',
        'Log channel for notifications': 'Salon de journalisation pour les notifications',
        "Manage this server's API keys (stored encrypted)": 'Gérer les clés API de ce serveur (stockées chiffrées)',
        'Manage translation bridges': 'Gérer les ponts de traduction',
        'Name of the bridge (channels with the same name are connected)': 'Nom du pont (les salons portant le même nom '
                                                                          'sont connectés)',
        'Remove a channel from its bridge': 'Supprimer un salon de son pont',
        'Remove an API key from this server': 'Supprimer une clé API de ce serveur',
        'Set the channel for notifications (usage warnings, key problems, changes)': 'Définir le salon pour les '
                                                                                     'notifications (avertissements '
                                                                                     "d'utilisation, problèmes de clé, "
                                                                                     'changements',
        'Setup guide and overview of all commands': 'Guide de configuration et aperçu de toutes les commandes',
        "Show this server's API keys and their usage (never the keys themselves)": 'Afficher les clés API de ce '
                                                                                   'serveur et leur utilisation '
                                                                                   '(jamais les clés elles-mêmes)',
        'Text channel': 'Salon textuel',
        'Text, forum or media channel': 'Salon textuel, forum ou média',
        'Translation chain, usage and service health of this server': 'Chaîne de traduction, utilisation et état du '
                                                                      'service de ce serveur',
        'Translation service': 'Service de traduction',
        'Turn off the notification channel': 'Désactiver le salon de notification',
        'What this bot does with your messages': 'Ce que ce bot fait de tes messages',
        'YATB settings for your own messages': 'Paramètres YATB pour tes propres messages',
        'YATB translation bridges (admin settings)': 'Ponts de traduction YATB (paramètres administrateur)'},
 'it': {'Add a channel to a translation bridge': 'Aggiungi un canale a un Bridge di traduzione',
        'Add an API key (entered in a private form, stored encrypted)': 'Aggiungi una chiave API (inserita in un '
                                                                        'modulo privato, salvata criptata)',
        'Change the settings of a key (the key itself is never shown)': 'Modifica le impostazioni di una chiave (la '
                                                                        'chiave stessa non viene mai mostrata)',
        'Choose who may translate your messages (applies on all servers)': 'Scegli chi può tradurre i tuoi messaggi '
                                                                           '(si applica a tutti i server)',
        'Delete all bridges, keys and settings of this server': 'Elimina tutti i Bridge, le chiavi e le impostazioni '
                                                                'di questo server',
        'Delete all data of this server and make the bot leave': 'Elimina tutti i dati di questo server e fai uscire '
                                                                 'il bot',
        'How many channels this server uses (Discord limit: 500)': 'Quanti canali utilizza questo server (limite '
                                                                   'Discord: 500)',
        'How to get an API key for a translation service': 'Come ottenere una chiave API per un servizio di traduzione',
        'Key to change': 'Chiave da modificare',
        'Key to remove': 'Chiave da rimuovere',
        'Language of this channel': 'Lingua di questo canale',
        'List all bridges of this server': 'Elenca tutti i Bridge di questo server',
        'Log channel for notifications': 'Canale log per le notifiche',
        "Manage this server's API keys (stored encrypted)": 'Gestisci le chiavi API di questo server (salvate '
                                                            'criptate)',
        'Manage translation bridges': 'Gestisci i Bridge di traduzione',
        'Name of the bridge (channels with the same name are connected)': 'Nome del Bridge (i canali con lo stesso '
                                                                          'nome sono collegati)',
        'Remove a channel from its bridge': 'Rimuovi un canale dal suo Bridge',
        'Remove an API key from this server': 'Rimuovi una chiave API da questo server',
        'Set the channel for notifications (usage warnings, key problems, changes)': 'Imposta il canale per le '
                                                                                     'notifiche (avvisi di utilizzo, '
                                                                                     'problemi con le chiavi, '
                                                                                     'modifiche)',
        'Setup guide and overview of all commands': 'Guida alla configurazione e panoramica di tutti i comandi',
        "Show this server's API keys and their usage (never the keys themselves)": 'Mostra le chiavi API di questo '
                                                                                   'server e il loro utilizzo (mai le '
                                                                                   'chiavi stesse)',
        'Text channel': 'Canale testuale',
        'Text, forum or media channel': 'Canale testuale, forum o media',
        'Translation chain, usage and service health of this server': 'Catena di traduzione, utilizzo e stato del '
                                                                      'servizio di questo server',
        'Translation service': 'Servizio di traduzione',
        'Turn off the notification channel': 'Disattiva il canale delle notifiche',
        'What this bot does with your messages': 'Cosa fa questo bot con i tuoi messaggi',
        'YATB settings for your own messages': 'Impostazioni YATB per i tuoi messaggi',
        'YATB translation bridges (admin settings)': 'Bridge di traduzione YATB (impostazioni amministratore)'},
 'nl': {'Add a channel to a translation bridge': 'Voeg een kanaal toe aan een vertaal-Bridge',
        'Add an API key (entered in a private form, stored encrypted)': 'Voeg een API-sleutel toe (ingevoerd in een '
                                                                        'privéformulier, versleuteld opgeslagen)',
        'Change the settings of a key (the key itself is never shown)': 'Wijzig de instellingen van een sleutel (de '
                                                                        'sleutel zelf wordt nooit getoond)',
        'Choose who may translate your messages (applies on all servers)': 'Kies wie je berichten mag vertalen (geldt '
                                                                           'voor alle servers)',
        'Delete all bridges, keys and settings of this server': 'Verwijder alle Bridges, sleutels en instellingen van '
                                                                'deze server',
        'Delete all data of this server and make the bot leave': 'Verwijder alle gegevens van deze server en laat de '
                                                                 'bot vertrekken',
        'How many channels this server uses (Discord limit: 500)': 'Hoeveel kanalen deze server gebruikt (Discord '
                                                                   'limiet: 500)',
        'How to get an API key for a translation service': 'Hoe krijg je een API-sleutel voor een vertaaldienst',
        'Key to change': 'Sleutel om te wijzigen',
        'Key to remove': 'Sleutel om te verwijderen',
        'Language of this channel': 'Taal van dit kanaal',
        'List all bridges of this server': 'Toon alle Bridges van deze server',
        'Log channel for notifications': 'Logkanaal voor meldingen',
        "Manage this server's API keys (stored encrypted)": 'Beheer de API-sleutels van deze server (versleuteld '
                                                            'opgeslagen)',
        'Manage translation bridges': 'Beheer vertaal-Bridges',
        'Name of the bridge (channels with the same name are connected)': 'Naam van de Bridge (kanalen met dezelfde '
                                                                          'naam zijn verbonden)',
        'Remove a channel from its bridge': 'Verwijder een kanaal uit zijn Bridge',
        'Remove an API key from this server': 'Verwijder een API-sleutel van deze server',
        'Set the channel for notifications (usage warnings, key problems, changes)': 'Stel het kanaal in voor '
                                                                                     'meldingen '
                                                                                     '(gebruikswaarschuwingen, '
                                                                                     'sleutelproblemen, wijzigingen)',
        'Setup guide and overview of all commands': "Installatiehandleiding en overzicht van alle commando's",
        "Show this server's API keys and their usage (never the keys themselves)": 'Toon de API-sleutels van deze '
                                                                                   'server en hun gebruik (nooit de '
                                                                                   'sleutels zelf)',
        'Text channel': 'Tekstkanaal',
        'Text, forum or media channel': 'Tekst-, forum- of mediakanaal',
        'Translation chain, usage and service health of this server': 'Vertaalketen, gebruik en status van de '
                                                                      'vertaaldienst van deze server',
        'Translation service': 'Vertaaldienst',
        'Turn off the notification channel': 'Schakel het meldingskanaal uit',
        'What this bot does with your messages': 'Wat deze bot met je berichten doet',
        'YATB settings for your own messages': 'YATB-instellingen voor je eigen berichten',
        'YATB translation bridges (admin settings)': 'YATB vertaal-Bridges (beheerdersinstellingen)'},
 'ru': {'Add a channel to a translation bridge': 'Добавить канал в мост перевода',
        'Add an API key (entered in a private form, stored encrypted)': 'Добавить API-ключ (вводится в приватной '
                                                                        'форме, хранится в зашифрованном виде)',
        'Change the settings of a key (the key itself is never shown)': 'Изменить настройки ключа (сам ключ никогда не '
                                                                        'отображается)',
        'Choose who may translate your messages (applies on all servers)': 'Выбрать, кто может переводить твои '
                                                                           'сообщения (применяется на всех серверах)',
        'Delete all bridges, keys and settings of this server': 'Удалить все мосты, ключи и настройки этого сервера',
        'Delete all data of this server and make the bot leave': 'Удалить все данные этого сервера и заставить бота '
                                                                 'покинуть его',
        'How many channels this server uses (Discord limit: 500)': 'Сколько каналов используется на этом сервере '
                                                                   '(лимит Discord: 500)',
        'How to get an API key for a translation service': 'Как получить API-ключ для сервиса перевода',
        'Key to change': 'Ключ для изменения',
        'Key to remove': 'Ключ для удаления',
        'Language of this channel': 'Язык этого канала',
        'List all bridges of this server': 'Список всех мостов этого сервера',
        'Log channel for notifications': 'Канал логов для уведомлений',
        "Manage this server's API keys (stored encrypted)": 'Управление API-ключами этого сервера (хранятся в '
                                                            'зашифрованном виде)',
        'Manage translation bridges': 'Управление мостами перевода',
        'Name of the bridge (channels with the same name are connected)': 'Название моста (каналы с одинаковым '
                                                                          'названием соединяются)',
        'Remove a channel from its bridge': 'Удалить канал из его моста',
        'Remove an API key from this server': 'Удалить API-ключ с этого сервера',
        'Set the channel for notifications (usage warnings, key problems, changes)': 'Установить канал для уведомлений '
                                                                                     '(предупреждения об '
                                                                                     'использовании, проблемы с '
                                                                                     'ключами, изменения)',
        'Setup guide and overview of all commands': 'Руководство по настройке и обзор всех команд',
        "Show this server's API keys and their usage (never the keys themselves)": 'Показать API-ключи этого сервера и '
                                                                                   'их использование (сами ключи не '
                                                                                   'отображаются)',
        'Text channel': 'Текстовый канал',
        'Text, forum or media channel': 'Текстовый, форумный или медиа-канал',
        'Translation chain, usage and service health of this server': 'Цепочка перевода, использование и состояние '
                                                                      'сервисов этого сервера',
        'Translation service': 'Сервис перевода',
        'Turn off the notification channel': 'Отключить канал уведомлений',
        'What this bot does with your messages': 'Что этот бот делает с твоими сообщениями',
        'YATB settings for your own messages': 'Настройки YATB для твоих сообщений',
        'YATB translation bridges (admin settings)': 'Мосты перевода YATB (настройки администратора)'}}
