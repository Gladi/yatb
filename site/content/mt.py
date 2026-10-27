"""
YATB - MASCHINELL ÜBERSETZTE Texte (fr, es, it, ru), erzeugt mit site/translate.py aus en.py
(Google Gemini). NICHT von Muttersprachlern geprüft. Nicht von Hand ändern - sonst beim nächsten Lauf
überschrieben; Korrekturen in en.py bzw. per Neuübersetzung. SOURCE_HASH = Stand des englischen Textes.
"""

TEXTS_MT = {'es': {'admins_chain_intro': 'Para cada mensaje, YATB prueba los servicios en este orden y toma el primer resultado '
                              'válido:',
        'admins_chain_note': 'Cada respuesta se verifica (menciones, enlaces, formato). Una respuesta incorrecta, un '
                             'error o un límite agotado pasan al siguiente servicio; un servicio que falla se omite '
                             'durante un tiempo. Los miembros con <em>Solo local</em> siempre obtienen LibreTranslate.',
        'admins_chain_title': 'La cadena de traducción',
        'admins_col_command': 'Comando',
        'admins_col_desc': 'Descripción',
        'admins_commands_title': 'Todos los comandos',
        'admins_dashboard': '<p>En el <a href="{url}">panel de control</a> inicias sesión con Discord y ves todos los '
                            'servidores con YATB en los que eres administrador.</p><ul><li>Uso por clave de API: hoy y '
                            'este mes, frente a los límites gratuitos o tu presupuesto; se actualiza '
                            'solo.</li><li>Cambia la etiqueta, el plan, el presupuesto y el límite de una clave, o '
                            'elimínala. La clave en sí nunca se muestra ni se introduce en la web: añadir una clave '
                            'sigue siendo un formulario en Discord.</li><li>Cambia el orden de la cadena de '
                            'traducción.</li><li>Estadísticas de 7, 30 y 90 días: llamadas, éxitos y volumen por '
                            'servicio.</li><li>Cada cambio se notifica en el canal de registro del servidor con tu '
                            'nombre.</li></ul>',
        'admins_dashboard_title': 'Panel de control',
        'admins_forum': '<ul><li>Vincula foros como canales de texto, p. ej. <code>/yatb bridge add forum #forum-en '
                        'English</code>. Un Bridge contiene foros o canales de texto, nunca ambos. Los canales '
                        'multimedia funcionan de la misma manera.</li><li>Una nueva publicación aparece en todos los '
                        'demás foros del Bridge: título y texto traducidos, etiquetas coincidentes, bajo el nombre del '
                        'autor. Las respuestas, ediciones, eliminaciones y reacciones dentro de la publicación se '
                        'replican.</li><li>El cambio de nombre, el cambio de etiquetas, el cierre o el bloqueo de la '
                        'publicación original se aplican a las copias.</li><li>Las etiquetas se emparejan 1:1. YATB '
                        'crea las etiquetas faltantes por sí mismo (nombre traducido, mismo emoji) si tiene el permiso '
                        '<em>Gestionar canales</em>; de lo contrario, solo se emparejan las etiquetas con el mismo '
                        'nombre. Discord permite 20 etiquetas por foro.</li></ul>',
        'admins_forum_perms': '<p>Dónde conceder <em>Gestionar canales</em>:</p><ul><li><strong>En la categoría de los '
                              'foros</strong> (recomendado): todos los foros dentro de ella quedan cubiertos, '
                              'incluidos los nuevos, y el resto del servidor permanece protegido.</li><li><strong>En '
                              'cada foro</strong>: la opción más restrictiva, pero cada foro nuevo necesita el permiso '
                              'de nuevo.</li><li><strong>A nivel de servidor</strong> (rol del bot o enlace de '
                              'invitación): la opción más cómoda, pero el bot podría editar o eliminar cualquier '
                              'canal; si su token fuera robado, el daño sería mucho mayor.</li></ul>',
        'admins_forum_title': 'Canales de foro y multimedia',
        'admins_lead': 'YATB es un bot privado. Si está en tu servidor, así es como debes configurarlo. Todos los '
                       'comandos están bajo <code>/yatb</code> y solo son visibles para los administradores.',
        'admins_limits': '<ul><li><strong>Claves gratuitas:</strong> YATB contabiliza el uso según los límites '
                         'gratuitos del proveedor por minuto, día y mes.</li><li><strong>Claves de pago:</strong> tú '
                         'estableces un presupuesto mensual en USD o EUR. YATB estima el coste a partir de los precios '
                         'listados; configura también un límite de gasto en el proveedor.</li><li>Los límites diarios '
                         'se reinician a las 00:00 UTC, y los mensuales el día 1 a las 00:00 UTC.</li><li>Las '
                         'advertencias al 90, 95 y 100 % se envían al canal de registro. Cuando una clave se agota, el '
                         'siguiente servicio toma el relevo.</li><li>Si la misma clave se usa en varios servidores, el '
                         'uso se contabiliza en conjunto. Nunca se nombran otros servidores.</li><li><code>/yatb keys '
                         'list</code> y el panel de control muestran el uso por clave; <code>/yatb keys edit</code> '
                         'permite cambiar el plan, el presupuesto y el límite.</li></ul>',
        'admins_limits_title': 'Uso, límites y presupuesto',
        'admins_remove': '<code>/yatb reset</code> elimina todos los Bridge, claves y ajustes de tu servidor. '
                         '<code>/yatb uninstall</code> elimina todos los datos de tu servidor y el bot se marcha.',
        'admins_remove_title': 'Eliminar YATB',
        'admins_security': 'Las claves se introducen en un formulario privado de Discord, nunca como una opción de '
                           'comando. Se almacenan cifradas (AES-256-GCM, por separado para cada servidor) y nunca se '
                           'vuelven a mostrar, solo los últimos 4 caracteres. Este sitio web nunca muestra ni acepta '
                           'claves.',
        'admins_security_title': 'Cómo se protegen las claves',
        'admins_setup_title': 'Configuración en 5 pasos',
        'admins_title': 'Para administradores de servidores',
        'chain_1': '<strong>Proveedores de IA</strong> con tus claves: primero el grupo de mejor calidad, claves '
                   'gratuitas antes que claves de pago',
        'chain_2': '<strong>Google Translate</strong>',
        'chain_3': '<strong>Azure Translator</strong>',
        'chain_4': '<strong>LibreTranslate</strong> en nuestro propio servidor: siempre disponible',
        'chain_5': '<strong>[Raw]</strong> - el texto original, si nada más ha funcionado',
        'faq_dm_a': 'No. YATB solo procesa mensajes en los canales que los administradores han vinculado a un Bridge.',
        'faq_dm_q': '¿YATB lee mis mensajes directos u otros canales?',
        'faq_off_a': 'Los mensajes en los canales vinculados siempre se traducen para que todos puedan seguir la '
                     'conversación. Con la opción <em>Solo local</em>, los mensajes permanecen en nuestro propio '
                     'servidor. Los canales no vinculados nunca se ven afectados.',
        'faq_off_q': '¿Puedo desactivar la traducción por completo?',
        'faq_wrong_a': 'Edita tu mensaje: la traducción también se actualizará. Si un término se traduce siempre mal, '
                       'avisa a los administradores de tu servidor.',
        'faq_wrong_q': '¿La traducción es incorrecta. ¿Qué puedo hacer?',
        'feat_fallback_text': 'Sin ninguna clave, YATB traduce con LibreTranslate en nuestro propio servidor: es '
                              'gratis y nada sale del servidor.',
        'feat_fallback_title': 'Siempre una traducción',
        'feat_format_text': 'Las negritas, listas, citas, spoilers, emojis, menciones y enlaces permanecen intactos. '
                            'El código real se deja sin traducir.',
        'feat_format_title': 'Mantiene el formato de Discord',
        'feat_keys_text': 'Los administradores del servidor añaden sus propias claves API en un formulario privado. '
                          'Las claves se almacenan cifradas y nunca se vuelven a mostrar. Incluye límites y avisos de '
                          'presupuesto.',
        'feat_keys_title': 'Tus claves, tu presupuesto',
        'feat_mirror_text': 'Las respuestas, ediciones, eliminaciones, reacciones e hilos se reflejan en todos los '
                            'canales vinculados. Los anuncios de los canales seguidos también se traducen.',
        'feat_mirror_title': 'Refleja la conversación',
        'feat_natural_text': 'Traducción mediante IA que entiende la conversación: la jerga, los términos de juego y '
                             'las respuestas cortas se traducen correctamente. Si un servicio falla, el siguiente toma '
                             'el relevo.',
        'feat_natural_title': 'Traducciones naturales',
        'feat_privacy_text': 'No se almacena el texto de los mensajes. Cada miembro puede elegir que sus mensajes solo '
                             'se traduzcan en nuestro propio servidor.',
        'feat_privacy_title': 'Privacidad desde el diseño',
        'footer_note': 'YATB es un proyecto privado y no comercial, y no está afiliado a Discord.',
        'home_badge_langs': '7 idiomas',
        'home_badge_private': 'Bot privado',
        'home_badge_storage': 'No se almacenan textos de mensajes',
        'home_example_note': 'Ejemplo de un par de canales conectados. La etiqueta tras el nombre indica qué servicio '
                             'realizó la traducción.',
        'home_example_src': '¿Alguien se apunta a una incursión esta noche? Nos vemos a las 20:00 en <span '
                            'class="mention">#voice</span> 🎮',
        'home_example_tgt': '¿Alguien se apunta a una incursión esta noche? Nos vemos a las 20:00 en <span '
                            'class="mention">#voice</span> 🎮',
        'home_example_tgt_channel': 'español',
        'home_example_title': 'Ejemplo',
        'home_features_title': 'Qué hace YATB',
        'home_how_title': 'Cómo funciona',
        'home_lead': 'YATB - <em>Yet Another Translation Bot</em> - conecta canales en diferentes idiomas. Cada uno '
                     'escribe en su propio idioma y YATB publica la traducción en los otros canales, bajo el nombre y '
                     'avatar del autor.',
        'home_private_text': 'Por el momento no. YATB es un bot privado y solo funciona en servidores seleccionados. '
                             'Si YATB ya está en tu servidor, consulta las guías <a href="members">para miembros</a> y '
                             '<a href="admins">para administradores</a>.',
        'home_private_title': '¿Puedo añadir YATB a mi servidor?',
        'home_support_text': 'YATB es gratuito y no tiene anuncios. Si quieres ayudar con los costes de mantenimiento, '
                             'puedes apoyarlo en Ko-fi.',
        'home_support_title': '¿Te gusta YATB?',
        'home_title': 'Habla en diferentes idiomas en Discord',
        'how_1': '<strong>Los administradores vinculan canales</strong> - por ejemplo <code>#english</code> y '
                 '<code>#deutsch</code> - en un Bridge.',
        'how_2': '<strong>Los miembros simplemente escriben</strong> en su idioma. No se necesitan comandos.',
        'how_3': '<strong>YATB publica la traducción</strong> en los otros canales en pocos segundos.',
        'imprint_title': 'Aviso legal',
        'keys_kind_ai': 'Proveedor de IA',
        'keys_kind_mt': 'Servicio de traducción',
        'keys_lead': 'Las claves API mejoran las traducciones respecto al LibreTranslate gratuito. Cada clave te '
                     'pertenece a ti o a tu servidor; YATB solo la utiliza para tu servidor y la almacena cifrada.',
        'keys_menu_note': 'Los nombres de los menús en los proveedores pueden cambiar. Estado de la información de '
                          'privacidad: {date}.',
        'keys_open': 'Abrir consola',
        'keys_plan': 'Plan',
        'keys_privacy': 'Privacidad',
        'keys_source': 'Información de privacidad del proveedor',
        'keys_steps': 'Pasos',
        'keys_tips': '<ul><li>Establece un <strong>límite de gasto</strong> en la cuenta de tu proveedor además del '
                     'presupuesto en YATB.</li><li>Donde esté disponible, activa la <strong>retención de datos '
                     'cero</strong> o desactiva el entrenamiento con tus datos.</li><li>Añade claves con <code>/yatb '
                     'keys add</code>: elige el proveedor y pega la clave en el formulario privado.</li></ul>',
        'keys_title': 'Obtención de claves API',
        'kofi': 'Apoya a YATB en Ko-fi',
        'lang_name': 'Español',
        'legal_binding': 'Este texto está disponible en varios idiomas. En caso de discrepancia, prevalecerá la '
                         'versión alemana.',
        'legal_updated': 'Última actualización: {date}',
        'members_choice_local': '<strong>Solo local</strong>: tus mensajes solo son traducidos por LibreTranslate en '
                                'nuestro propio servidor y nunca se envían a proveedores de IA, Google o Azure, ni '
                                'siquiera como contexto para las traducciones de otras personas. La calidad es '
                                'inferior.',
        'members_choice_note': 'Este ajuste solo es visible para ti y se aplica en todos los servidores con YATB. '
                               '<code>/yatb-user help</code> muestra un breve resumen en Discord.',
        'members_choice_standard': '<strong>Estándar</strong>: mejor calidad. Tus mensajes pueden enviarse a los '
                                   'servicios que hayan añadido los administradores.',
        'members_choice_title': 'Tu elección: <code>/yatb-user privacy</code>',
        'members_dashboard': 'También puedes consultar y cambiar tu elección en el <a href="{url}">panel de '
                             'control</a> (inicia sesión con Discord).',
        'members_data': '<ul><li>YATB <strong>no almacena el texto de los mensajes</strong>. Solo recuerda qué mensaje '
                        'pertenece a qué traducción durante {map_days} días, para que las ediciones y eliminaciones '
                        'puedan reflejarse.</li><li>Para traducir, tu mensaje se envía a los servicios de traducción '
                        'elegidos por los administradores de tu servidor (consulta la <a href="privacy">política de '
                        'privacidad</a>).</li><li>Los proveedores de IA también reciben hasta {context_lines} mensajes '
                        'anteriores de la misma conversación como contexto, para que las respuestas cortas se '
                        'traduzcan correctamente.</li></ul>',
        'members_data_title': 'Tus datos',
        'members_faq_title': 'Preguntas frecuentes',
        'members_how': '<ul><li>Escribe en tu idioma en un canal vinculado. YATB publica una traducción en los otros '
                       'canales vinculados, bajo tu nombre y avatar.</li><li>Las respuestas, ediciones, eliminaciones '
                       'e hilos se reflejan. También las reacciones: aparecen en los otros canales como una reacción '
                       'de YATB.</li><li>El formato, los emojis, las menciones y los enlaces se mantienen.</li><li>La '
                       'traducción aparece en los otros canales; las personas que no pueden ver tu canal aún pueden '
                       'leerla allí.</li></ul>',
        'members_how_title': 'Cómo funciona',
        'members_lead': 'Algunos canales de tu servidor están vinculados por YATB. Esto es lo que significa para ti.',
        'members_tags_intro': 'Cada traducción indica qué servicio la ha realizado:',
        'members_tags_title': 'La etiqueta después del nombre',
        'members_title': 'Para miembros',
        'nav_admins': 'Para administradores',
        'nav_dashboard': 'Panel de control',
        'nav_home': 'Inicio',
        'nav_imprint': 'Aviso legal',
        'nav_keys': 'Claves API',
        'nav_language': 'Idioma',
        'nav_members': 'Para miembros',
        'nav_menu': 'Menú',
        'nav_more': 'Más proyectos de Gladi',
        'nav_privacy': 'Privacidad',
        'nav_terms': 'Términos',
        'not_found_text': 'Esta página no existe. Vuelve a la <a href="/">página de inicio</a>.',
        'not_found_title': 'Página no encontrada',
        'pd_backup_how_long': '14 días en el servidor, 30 días en Oracle Object Storage (Frankfurt)',
        'pd_backup_what': 'Copias de seguridad cifradas de los datos anteriores (nunca textos de mensajes)',
        'pd_backup_why': 'Recuperación tras errores',
        'pd_choice_how_long': 'Hasta que solicites su eliminación',
        'pd_choice_what': 'Tu ID de usuario y tu elección de privacidad',
        'pd_choice_why': 'Respetar <code>/yatb-user privacy</code> en cada servidor',
        'pd_config_how_long': 'Hasta que se elimine, <code>/yatb reset</code> o <code>/yatb uninstall</code>',
        'pd_config_what': 'Configuración del servidor: Bridge, canal de registro, claves API cifradas, ID del '
                          'administrador que añadió una clave',
        'pd_config_why': 'Ejecutar el bot en el servidor',
        'pd_map_how_long': '{map_days} días',
        'pd_map_what': 'IDs de mensajes y una suma de comprobación del texto',
        'pd_map_why': 'Reflejar respuestas, ediciones y eliminaciones en las traducciones',
        'pd_stats_how_long': '{raw_days} días, después solo totales diarios por servidor',
        'pd_stats_what': 'Estadísticas de uso: servidor, servicio, idiomas, número de caracteres, duración, resultado; '
                         'sin texto ni IDs de usuario',
        'pd_stats_why': 'Límites, costes y fiabilidad de los servicios',
        'pd_text_how_long': 'No se almacena. Se mantiene en memoria solo durante la traducción; el contexto de los '
                            'mensajes recientes se pierde en cada reinicio.',
        'pd_text_what': 'Texto del mensaje y nombre de usuario',
        'pd_text_why': 'Traducción; enviada a los servicios de traducción del servidor (consulta el apartado 4). Los '
                       'proveedores de IA también reciben hasta {context_lines} de tus propios mensajes anteriores en '
                       'el mismo Bridge como contexto, nunca los mensajes de otras personas.',
        'privacy_basis': 'Art. 6(1)(f) del RGPD: nuestro interés legítimo, y el interés de las comunidades de los '
                         'servidores, en la comunicación multilingüe y en un servicio seguro y fiable. Tu elección de '
                         '<em>Solo local</em> limita el procesamiento a nuestro propio servidor.',
        'privacy_basis_title': '6. Base jurídica',
        'privacy_bot_intro': 'YATB solo procesa mensajes en canales que los administradores de un servidor han '
                             'vinculado a un Bridge.',
        'privacy_bot_title': '3. El bot de Discord',
        'privacy_col_how_long': 'Periodo de conservación',
        'privacy_col_note': 'Lo que dice el proveedor',
        'privacy_col_service': 'Servicio',
        'privacy_col_what': 'Datos',
        'privacy_col_why': 'Propósito',
        'privacy_controller_missing': 'Los datos de contacto del operador se añadirán aquí.',
        'privacy_controller_title': '1. Quién es el responsable',
        'privacy_dash': '<ul><li>En <code>/app</code> puedes iniciar sesión con Discord. YATB solo recibe tu ID de '
                        'usuario de Discord y tu nombre (ámbito <code>identify</code>). El token de acceso de Discord '
                        'se revoca justo después de iniciar sesión y nunca se almacena.</li><li>Una cookie de sesión '
                        '(<code>yatb_session</code>, válida por 7 días) te mantiene conectado; durante el inicio de '
                        'sesión, una segunda cookie protege contra inicios de sesión falsificados durante un máximo de '
                        '10 minutos. Ambas son técnicamente necesarias y no se utilizan para ningún otro '
                        'fin.</li><li>Almacenado en nuestro servidor: un hash del token de sesión, tu ID de Discord, '
                        'nombre de usuario, idioma y la fecha de caducidad; se eliminan al cerrar sesión o después de '
                        '7 días.</li><li>El bot comprueba directamente con Discord en cada solicitud si puedes '
                        'gestionar un servidor. Los cambios que realices se informan en el canal de registro de ese '
                        'servidor con tu nombre.</li></ul>',
        'privacy_dash_title': 'Panel de control (iniciar sesión con Discord)',
        'privacy_discord': 'Los mensajes se escriben y muestran en Discord. Discord los procesa bajo su propia <a '
                           'href="https://discord.com/privacy" rel="noopener">política de privacidad</a>.',
        'privacy_discord_title': '5. Discord',
        'privacy_lead': 'Esta página explica qué datos procesan el sitio web de YATB y el bot de Discord YATB, por qué '
                        'y durante cuánto tiempo.',
        'privacy_rights': 'Tienes derecho a acceder, rectificar, suprimir, limitar el tratamiento, a la portabilidad '
                          'de los datos y a oponerte, además de poder presentar una reclamación ante una autoridad de '
                          'control de protección de datos. Para ejercer tus derechos, contacta con el operador '
                          '(sección 1). En Discord, <code>/yatb-user privacy</code> te permite elegir <em>Solo '
                          'local</em> en cualquier momento.',
        'privacy_rights_title': '7. Tus derechos',
        'privacy_services_intro': 'Los administradores de cada servidor deciden qué servicios traducen sus mensajes. '
                                  'Los mensajes de los miembros con <em>Solo local</em> solo son traducidos por '
                                  'LibreTranslate en nuestro propio servidor. En los servidores gestionados por el '
                                  'operador, se utilizan las cuentas de pago propias del operador.',
        'privacy_services_title': '4. Servicios de traducción',
        'privacy_title': 'Política de privacidad',
        'privacy_web': '<ul><li>Las páginas informativas no utilizan cookies, ni seguimiento, ni analíticas, ni '
                       'fuentes o scripts externos.</li><li>Para mostrar las páginas, la dirección IP de tu navegador '
                       'y la solicitud son procesadas brevemente por el servidor web. El servidor web no guarda '
                       'registros de acceso.</li><li>El sitio web se ejecuta en un servidor de Oracle Cloud en '
                       "Fráncfort (Alemania). Los certificados HTTPS provienen de Let's Encrypt; no se comparten datos "
                       'de visitantes para esto.</li><li>Los enlaces a otros sitios (Discord, Ko-fi, proveedores) son '
                       'enlaces normales; allí se aplican sus propias políticas de privacidad.</li></ul>',
        'privacy_web_title': '2. Este sitio web',
        'prov_azure': 'La traducción de texto no almacena el texto ("sin rastro"). YATB utiliza el punto de conexión '
                      'global, por lo que las solicitudes pueden procesarse en cualquier centro de datos de Microsoft, '
                      'generalmente el más cercano.',
        'prov_gemini': 'Solo claves con facturación activada: el nivel gratuito no puede utilizarse para usuarios en '
                       'el EEE, el Reino Unido o Suiza. Nivel de pago: Google no utiliza el contenido para mejorar sus '
                       'productos; las solicitudes se registran durante un tiempo limitado para detectar abusos. '
                       'Procesado por Google a nivel mundial.',
        'prov_google_translate': 'El texto solo se mantiene en la memoria para la traducción y no se utiliza para '
                                 'entrenar o mejorar la traducción de Google. Procesado por Google a nivel mundial.',
        'prov_groq': 'Por defecto, Groq no conserva datos de inferencia; los registros para resolución de problemas o '
                     'abusos se conservan hasta 30 días. La retención de datos cero puede activarse para todos en '
                     '<strong>Data Controls</strong>. Los datos se almacenan en EE. UU.',
        'prov_libre': 'Se ejecuta en nuestro propio servidor en Fráncfort (Alemania). No se envía nada a terceros.',
        'prov_mistral': 'Mistral AI (Francia). Sin entrenamiento con tu contenido, excepto cuando la configuración del '
                        'producto lo permita: en la consola de Mistral, bajo <strong>Privacy</strong>, desactiva el '
                        'uso de datos de la API para mejoras. El plan gratuito puede utilizar datos para entrenamiento '
                        'a menos que lo desactives. Existe un DPA disponible y retención de datos cero bajo petición.',
        'prov_novita': 'Según sus términos: retención de datos cero y sin entrenamiento con tu contenido por defecto. '
                       'Los metadatos de uso se conservan hasta 2 años; los datos pueden procesarse en EE. UU. (SCC). '
                       'Un DPA solo para clientes empresariales. Regido por la ley de Delaware, EE. UU.',
        'setup_1': '<strong>Comprueba los permisos.</strong> En cada canal vinculado, YATB necesita: {perms}.',
        'setup_2': '<strong>Vincula canales.</strong> Los canales con el mismo nombre de Bridge se traducen entre '
                   'sí:<br><code>/yatb bridge add chat #english English</code><br><code>/yatb bridge add chat #deutsch '
                   'German</code><br>Los canales de foro y multimedia funcionan de la misma manera: siempre foro con '
                   'foro. YATB crea las etiquetas faltantes por sí mismo si tiene permiso para <em>Gestionar '
                   'canales</em> en el foro.',
        'setup_3': '<strong>Añade claves API (opcional).</strong> Sin claves, YATB utiliza LibreTranslate. Para '
                   'obtener una mejor calidad, añade claves con <code>/yatb keys add</code>; consulta <a '
                   'href="keys">claves API</a>.',
        'setup_4': '<strong>Configura un canal de registro.</strong> <code>/yatb log set</code> - YATB informa ahí de '
                   'advertencias de uso, problemas con las claves y cambios.',
        'setup_5': '<strong>Informa a tus miembros.</strong> Enlaza a la <a href="members">guía para miembros</a> o '
                   'añade una norma breve, por ejemplo:',
        'setup_check': '<code>/yatb status</code> muestra la cadena de traducción de tu servidor y el estado de cada '
                       'servicio.',
        'setup_rule': 'Traducción (YATB): En los canales enlazados, el bot YATB traduce los mensajes automáticamente y '
                      'los vuelve a publicar bajo tu nombre. Para ello, pueden enviarse a servicios externos (p. ej., '
                      'proveedores de IA, Google). Los textos de los mensajes no se almacenan. Traducción Solo local: '
                      '/yatb-user privacy',
        'site_desc': 'YATB conecta canales de Discord en diferentes idiomas y traduce cada mensaje bajo el nombre del '
                     'autor.',
        'tag_ai': 'Proveedor de IA (por ejemplo, Mistral o Google Gemini): suele ofrecer la mejor calidad',
        'tag_azure': 'Azure Translator (Microsoft)',
        'tag_google': 'Google Translate',
        'tag_libre': 'LibreTranslate: se ejecuta en nuestro propio servidor',
        'tag_raw': 'No traducido: no había ningún servicio disponible en ese momento',
        'terms_1': 'YATB es un proyecto privado y no comercial. Es gratuito, actualmente solo funciona en servidores '
                   'seleccionados y se ofrece sin garantía de disponibilidad. Las funciones pueden cambiar o finalizar '
                   'en cualquier momento.',
        'terms_1_title': '1. El servicio',
        'terms_2': 'Las traducciones son realizadas por máquinas y pueden ser erróneas o incompletas. No confíes en '
                   'ellas para asuntos importantes, legales, médicos o financieros.',
        'terms_2_title': '2. Traducciones',
        'terms_3': '<ul><li>Eres responsable de las claves API que añadas, de los términos de sus proveedores y de los '
                   'costes. El recuento de uso de YATB es una estimación; establece límites de gasto en el '
                   'proveedor.</li><li>Informa a tus miembros de que los mensajes en los canales vinculados (Bridge) '
                   'se traducen y pueden enviarse a servicios externos.</li><li>Utiliza YATB solo de acuerdo con la '
                   'ley y las condiciones de Discord: nada de spam ni abusos.</li></ul>',
        'terms_3_title': '3. Administradores de servidor',
        'terms_4': 'YATB se proporciona de forma gratuita y tal cual es. La responsabilidad se limita al dolo y a la '
                   'negligencia grave, en la medida en que la ley lo permita.',
        'terms_4_title': '4. Responsabilidad',
        'terms_5': 'Las donaciones (por ejemplo, a través de Ko-fi) son voluntarias y no generan ningún derecho a '
                   'funciones, soporte o disponibilidad.',
        'terms_5_title': '5. Donaciones',
        'terms_6': 'Se aplica la legislación alemana.',
        'terms_6_title': '6. Disposiciones finales',
        'terms_lead': 'Breve y sencillo: YATB es un proyecto personal gratuito. Al usar YATB en un servidor, aceptas '
                      'estas condiciones.',
        'terms_title': 'Condiciones de uso'},
 'fr': {'admins_chain_intro': 'Pour chaque message, YATB essaie les services dans cet ordre et retient le premier '
                              'résultat valide :',
        'admins_chain_note': 'Chaque réponse est vérifiée (mentions, liens, formatage). Une mauvaise réponse, une '
                             'erreur ou une limite atteinte passe au service suivant ; un service défaillant est '
                             'ignoré pendant un certain temps. Les membres en <em>Local uniquement</em> utilisent '
                             'toujours LibreTranslate.',
        'admins_chain_title': 'La chaîne de traduction',
        'admins_col_command': 'Commande',
        'admins_col_desc': 'Description',
        'admins_commands_title': 'Toutes les commandes',
        'admins_dashboard': '<p>Dans le <a href="{url}">tableau de bord</a>, connecte-toi avec Discord et vois tous '
                            'les serveurs avec YATB sur lesquels tu es administrateur·rice.</p><ul><li>Utilisation par '
                            "clé API : aujourd'hui et ce mois-ci, par rapport aux limites gratuites ou à ton budget — "
                            "les données se mettent à jour automatiquement.</li><li>Modifie l'étiquette, le plan, le "
                            "budget et la limite d'une clé, ou supprime une clé. La clé elle-même n'est jamais "
                            "affichée ni saisie sur le site — l'ajout d'une clé reste un formulaire sur "
                            "Discord.</li><li>Change l'ordre de la chaîne de traduction.</li><li>Statistiques sur 7, "
                            '30 et 90 jours : appels, succès et volume par service.</li><li>Toute modification est '
                            'signalée dans le canal de log du serveur avec ton nom.</li></ul>',
        'admins_dashboard_title': 'Tableau de bord',
        'admins_forum': '<ul><li>Relie des forums comme des salons textuels, par ex. <code>/yatb bridge add forum '
                        '#forum-en English</code>. Un Bridge contient soit des forums, soit des salons textuels, '
                        'jamais les deux. Les salons médias fonctionnent de la même manière.</li><li>Une nouvelle '
                        'publication apparaît dans tous les autres forums du Bridge - titre et texte traduits, tags '
                        "correspondants, sous le nom de l'auteur. Les réponses, modifications, suppressions et "
                        'réactions au sein de la publication sont répliquées.</li><li>Le renommage, le changement de '
                        'tags, la fermeture ou le verrouillage de la publication originale sont appliqués aux '
                        'copies.</li><li>Les tags sont mis en correspondance 1:1. YATB crée lui-même les tags '
                        "manquants (nom traduit, même émoji) s'il dispose de la permission <em>Gérer les salons</em> - "
                        'sinon, seuls les tags portant le même nom sont mis en correspondance. Discord autorise 20 '
                        'tags par forum.</li></ul>',
        'admins_forum_perms': '<p>Où accorder la permission <em>Gérer les salons</em> :</p><ul><li><strong>Sur la '
                              "catégorie des forums</strong> (recommandé) : tous les forums qu'elle contient sont "
                              'couverts, y compris les nouveaux, et le reste du serveur reste '
                              "protégé.</li><li><strong>Sur chaque forum</strong> : l'option la plus restrictive, mais "
                              "chaque nouveau forum nécessite de la configurer à nouveau.</li><li><strong>À l'échelle "
                              "du serveur</strong> (rôle du bot ou lien d'invitation) : le plus pratique, mais le bot "
                              "pourrait alors modifier ou supprimer n'importe quel salon - si son jeton était volé, "
                              'les dégâts seraient beaucoup plus importants.</li></ul>',
        'admins_forum_title': 'Forums et salons médias',
        'admins_lead': "YATB est un bot privé. S'il est présent sur ton serveur, voici comment le configurer. Toutes "
                       'les commandes se trouvent sous <code>/yatb</code> et ne sont visibles que par les '
                       'administrateurs.',
        'admins_limits': "<ul><li><strong>Clés gratuites :</strong> YATB compte l'utilisation par rapport aux limites "
                         'gratuites du fournisseur par minute, jour et mois.</li><li><strong>Clés payantes :</strong> '
                         'tu définis un budget mensuel en USD ou EUR. YATB estime le coût à partir des tarifs publics '
                         '— définis aussi une limite de dépenses chez le fournisseur.</li><li>Les limites quotidiennes '
                         'se réinitialisent à 00:00 UTC, les limites mensuelles le 1er à 00:00 UTC.</li><li>Des '
                         'avertissements à 90, 95 et 100 % sont envoyés dans le canal de log. Quand une clé est '
                         'épuisée, le service suivant prend le relais.</li><li>Si la même clé est utilisée sur '
                         "plusieurs serveurs, l'utilisation est comptabilisée ensemble. Les autres serveurs ne sont "
                         'jamais nommés.</li><li><code>/yatb keys list</code> et le tableau de bord affichent '
                         "l'utilisation par clé, <code>/yatb keys edit</code> permet de modifier le plan, le budget et "
                         'la limite.</li></ul>',
        'admins_limits_title': 'Utilisation, limites et budget',
        'admins_remove': '<code>/yatb reset</code> supprime tous les Bridge, clés et paramètres de ton serveur. '
                         '<code>/yatb uninstall</code> supprime toutes les données de ton serveur et le bot quitte le '
                         'serveur.',
        'admins_remove_title': 'Supprimer YATB',
        'admins_security': "Les clés sont saisies dans un formulaire Discord privé, jamais en tant qu'option de "
                           'commande. Elles sont stockées de manière chiffrée (AES-256-GCM, séparées par serveur) et '
                           'ne sont plus jamais affichées - seuls les 4 derniers caractères le sont. Ce site web '
                           "n'affiche ni n'accepte jamais de clés.",
        'admins_security_title': 'Comment les clés sont protégées',
        'admins_setup_title': 'Configuration en 5 étapes',
        'admins_title': 'Pour les administrateurs de serveur',
        'chain_1': "<strong>Fournisseurs d'IA</strong> avec tes clés - groupe de meilleure qualité d'abord, clés "
                   'gratuites avant les clés payantes',
        'chain_2': '<strong>Google Translate</strong>',
        'chain_3': '<strong>Azure Translator</strong>',
        'chain_4': '<strong>LibreTranslate</strong> sur notre propre serveur - toujours disponible',
        'chain_5': "<strong>[Raw]</strong> - le texte original, si rien d'autre n'a fonctionné",
        'faq_dm_a': 'Non. YATB traite uniquement les messages dans les canaux que les administrateurs ont reliés à un '
                    'Bridge.',
        'faq_dm_q': "YATB lit-il mes messages privés ou d'autres canaux ?",
        'faq_off_a': 'Les messages dans les canaux liés sont toujours traduits, afin que tout le monde puisse suivre '
                     'la conversation. Avec <em>Local uniquement</em>, ils restent sur notre propre serveur. Les '
                     'canaux non liés ne sont jamais touchés.',
        'faq_off_q': 'Puis-je désactiver complètement la traduction ?',
        'faq_wrong_a': 'Modifie ton message - la traduction sera mise à jour automatiquement. Si un terme est toujours '
                       'mal traduit, signale-le aux administrateurs de ton serveur.',
        'faq_wrong_q': 'La traduction est incorrecte. Que puis-je faire ?',
        'feat_fallback_text': 'Sans aucune clé, YATB traduit avec LibreTranslate sur notre propre serveur - '
                              'gratuitement, et rien ne quitte le serveur.',
        'feat_fallback_title': 'Toujours une traduction',
        'feat_format_text': 'Le gras, les listes, les citations, les spoilers, les emojis, les mentions et les liens '
                            "restent intacts. Le vrai code n'est pas traduit.",
        'feat_format_title': 'Préserve le formatage Discord',
        'feat_keys_text': 'Les administrateurs de serveur ajoutent leurs propres clés API dans un formulaire privé. '
                          'Les clés sont stockées de manière chiffrée et ne sont plus jamais affichées. Limites et '
                          'alertes budgétaires incluses.',
        'feat_keys_title': 'Tes clés, ton budget',
        'feat_mirror_text': 'Les réponses, modifications, suppressions, réactions et fils de discussion sont répliqués '
                            'dans tous les canaux liés. Les annonces des canaux suivis sont également traduites.',
        'feat_mirror_title': 'Reflète la conversation',
        'feat_natural_text': "Une traduction par IA qui comprend la conversation : l'argot, le jargon de jeu et les "
                             'réponses courtes sont traduits correctement. Si un service échoue, le suivant prend le '
                             'relais.',
        'feat_natural_title': 'Traductions naturelles',
        'feat_privacy_text': "Aucun texte de message n'est stocké. Chaque membre peut choisir que ses messages ne "
                             'soient traduits que sur notre propre serveur.',
        'feat_privacy_title': 'Confidentialité dès la conception',
        'footer_note': "YATB est un projet privé à but non lucratif et n'est pas affilié à Discord.",
        'home_badge_langs': '7 langues',
        'home_badge_private': 'Bot privé',
        'home_badge_storage': 'Aucun texte de message stocké',
        'home_example_note': "Exemple d'une paire de salons liés. L'étiquette après le nom indique quel service a "
                             'effectué la traduction.',
        'home_example_src': 'Anyone up for a raid tonight? Meet at 8 pm in <span class="mention">#voice</span> 🎮',
        'home_example_tgt': "Quelqu'un est partant pour un raid ce soir ? On se retrouve à 20 h dans <span "
                            'class="mention">#voice</span> 🎮',
        'home_example_tgt_channel': 'français',
        'home_example_title': 'Exemple',
        'home_features_title': 'Ce que fait YATB',
        'home_how_title': 'Comment ça marche',
        'home_lead': 'YATB - <em>Yet Another Translation Bot</em> - relie des salons dans différentes langues. Chacun '
                     'écrit dans sa propre langue, YATB publie la traduction dans les autres salons, sous le nom et '
                     "l'avatar de l'auteur.",
        'home_private_text': 'Pas pour le moment. YATB est un bot privé qui ne fonctionne que sur des serveurs '
                             'sélectionnés. Si YATB est déjà sur ton serveur, consulte les guides <a '
                             'href="members">pour les membres</a> et <a href="admins">pour les admins</a>.',
        'home_private_title': 'Puis-je ajouter YATB à mon serveur ?',
        'home_support_text': 'YATB est gratuit et sans publicité. Si tu souhaites aider à couvrir les frais de '
                             'fonctionnement, tu peux nous soutenir sur Ko-fi.',
        'home_support_title': 'Tu aimes YATB ?',
        'home_title': 'Communique au-delà des langues sur Discord',
        'how_1': '<strong>Les admins lient des canaux</strong> - par exemple <code>#english</code> et '
                 '<code>#deutsch</code> - dans un Bridge.',
        'how_2': "<strong>Les membres écrivent simplement</strong> dans leur langue. Aucune commande n'est nécessaire.",
        'how_3': '<strong>YATB publie la traduction</strong> dans les autres canaux en quelques secondes.',
        'imprint_title': 'Mentions légales',
        'keys_kind_ai': "Fournisseur d'IA",
        'keys_kind_mt': 'Service de traduction',
        'keys_lead': "Les clés API permettent d'obtenir de meilleures traductions que le service gratuit "
                     "LibreTranslate. Chaque clé t'appartient ou appartient à ton serveur - YATB ne l'utilise que pour "
                     'ton serveur et la stocke de manière chiffrée.',
        'keys_menu_note': 'Les noms des menus chez les fournisseurs peuvent changer. État des informations de '
                          'confidentialité : {date}.',
        'keys_open': 'Ouvrir la console',
        'keys_plan': 'Forfait',
        'keys_privacy': 'Confidentialité',
        'keys_source': 'Informations de confidentialité du fournisseur',
        'keys_steps': 'Étapes',
        'keys_tips': '<ul><li>Définis une <strong>limite de dépenses</strong> dans ton compte fournisseur en plus du '
                     'budget dans YATB.</li><li>Si disponible, active la <strong>non-rétention des données</strong> ou '
                     "désactive l'entraînement sur tes données.</li><li>Ajoute des clés avec <code>/yatb keys "
                     'add</code> : choisis le fournisseur, puis colle la clé dans le formulaire privé.</li></ul>',
        'keys_title': 'Obtenir des clés API',
        'kofi': 'Soutiens YATB sur Ko-fi',
        'lang_name': 'Français',
        'legal_binding': 'Ce texte est disponible en plusieurs langues. En cas de divergence, la version allemande '
                         'prévaut.',
        'legal_updated': 'Dernière mise à jour : {date}',
        'members_choice_local': '<strong>Local uniquement</strong> - tes messages sont traduits uniquement par '
                                'LibreTranslate sur notre propre serveur et ne sont jamais envoyés aux fournisseurs '
                                "d'IA, Google ou Azure - même pas en tant que contexte pour les traductions des "
                                'autres. La qualité est moindre.',
        'members_choice_note': "Ce paramètre n'est visible que par toi et s'applique sur chaque serveur utilisant "
                               'YATB. <code>/yatb-user help</code> affiche un court résumé dans Discord.',
        'members_choice_standard': '<strong>Standard</strong> - meilleure qualité. Tes messages peuvent être envoyés '
                                   'aux services ajoutés par les administrateurs.',
        'members_choice_title': 'Ton choix : <code>/yatb-user privacy</code>',
        'members_dashboard': 'Tu peux aussi vérifier et modifier ton choix dans le <a href="{url}">tableau de bord</a> '
                             '(connecte-toi avec Discord).',
        'members_data': '<ul><li>YATB ne <strong>stocke pas le texte des messages</strong>. Il mémorise uniquement '
                        'quel message correspond à quelle traduction, pendant {map_days} jours, afin que les '
                        'modifications et les suppressions puissent être répercutées.</li><li>Pour traduire, ton '
                        'message est envoyé aux services de traduction choisis par les administrateurs de ton serveur '
                        '(voir <a href="privacy">confidentialité</a>).</li><li>Les fournisseurs d\'IA reçoivent '
                        "également jusqu'à {context_lines} messages précédents de la même conversation en guise de "
                        'contexte, afin que les réponses courtes soient traduites correctement.</li></ul>',
        'members_data_title': 'Tes données',
        'members_faq_title': 'Questions',
        'members_how': '<ul><li>Écris dans ta langue dans un canal lié. YATB publie une traduction dans les autres '
                       'canaux liés, sous ton nom et ton avatar.</li><li>Les réponses, modifications, suppressions et '
                       'fils de discussion sont répliqués. Les réactions aussi : elles apparaissent dans les autres '
                       'canaux en tant que réaction de YATB.</li><li>La mise en forme, les émojis, les mentions et les '
                       'liens sont conservés.</li><li>La traduction apparaît dans les autres canaux - les personnes '
                       'qui ne peuvent pas voir ton canal peuvent tout de même la lire là-bas.</li></ul>',
        'members_how_title': 'Comment ça marche',
        'members_lead': 'Certains canaux de ton serveur sont liés par YATB. Voici ce que cela signifie pour toi.',
        'members_tags_intro': "Chaque traduction indique quel service l'a effectuée :",
        'members_tags_title': "L'étiquette après le nom",
        'members_title': 'Pour les membres',
        'nav_admins': 'Pour les administrateurs',
        'nav_dashboard': 'Tableau de bord',
        'nav_home': 'Accueil',
        'nav_imprint': 'Mentions légales',
        'nav_keys': 'Clés API',
        'nav_language': 'Langue',
        'nav_members': 'Pour les membres',
        'nav_menu': 'Menu',
        'nav_more': 'Plus de projets par Gladi',
        'nav_privacy': 'Confidentialité',
        'nav_terms': "Conditions d'utilisation",
        'not_found_text': 'Cette page n\'existe pas. Retourne à la <a href="/">page d\'accueil</a>.',
        'not_found_title': 'Page introuvable',
        'pd_backup_how_long': '14 jours sur le serveur, 30 jours dans Oracle Object Storage (Francfort)',
        'pd_backup_what': 'Sauvegardes chiffrées des données ci-dessus (jamais les textes des messages)',
        'pd_backup_why': 'Récupération après des erreurs',
        'pd_choice_how_long': "Jusqu'à ta demande de suppression",
        'pd_choice_what': 'Ton ID utilisateur et ton choix de confidentialité',
        'pd_choice_why': 'Respecter <code>/yatb-user privacy</code> sur chaque serveur',
        'pd_config_how_long': "Jusqu'à la suppression, <code>/yatb reset</code> ou <code>/yatb uninstall</code>",
        'pd_config_what': "Paramètres du serveur : Bridge, canal de logs, clés API chiffrées, ID de l'administrateur "
                          'ayant ajouté une clé',
        'pd_config_why': 'Faire fonctionner le bot sur le serveur',
        'pd_map_how_long': '{map_days} jours',
        'pd_map_what': 'ID des messages et somme de contrôle du texte',
        'pd_map_why': 'Répercuter les réponses, modifications et suppressions sur les traductions',
        'pd_stats_how_long': '{raw_days} jours, après quoi seuls les totaux quotidiens par serveur sont conservés',
        'pd_stats_what': "Statistiques d'utilisation : serveur, service, langues, nombre de caractères, durée, "
                         'résultat - aucun texte, aucun ID utilisateur',
        'pd_stats_why': 'Limites, coûts, fiabilité des services',
        'pd_text_how_long': 'Non stocké. Conservé en mémoire uniquement pendant la traduction ; le contexte des '
                            'messages récents est perdu à chaque redémarrage.',
        'pd_text_what': "Texte du message et nom d'affichage",
        'pd_text_why': "Traduction ; envoyée aux services de traduction du serveur (voir 4). Les fournisseurs d'IA "
                       "reçoivent jusqu'à {context_lines} de tes propres messages précédents dans le même Bridge en "
                       'guise de contexte — jamais ceux des autres.',
        'privacy_basis': 'Art. 6(1)(f) du RGPD - notre intérêt légitime, ainsi que celui des communautés de serveurs, '
                         'à une communication multilingue et à un service sécurisé et fiable. Ton choix de <em>Local '
                         'uniquement</em> limite le traitement à notre propre serveur.',
        'privacy_basis_title': '6. Base juridique',
        'privacy_bot_intro': "YATB traite uniquement les messages dans les canaux que les administrateurs d'un serveur "
                             'ont liés à un Bridge.',
        'privacy_bot_title': '3. Le bot Discord',
        'privacy_col_how_long': 'Durée de conservation',
        'privacy_col_note': 'Ce que dit le fournisseur',
        'privacy_col_service': 'Service',
        'privacy_col_what': 'Données',
        'privacy_col_why': 'Objectif',
        'privacy_controller_missing': "Les coordonnées de l'opérateur seront ajoutées ici.",
        'privacy_controller_title': '1. Qui est responsable',
        'privacy_dash': '<ul><li>Sur <code>/app</code>, tu peux te connecter avec Discord. YATB reçoit uniquement ton '
                        "identifiant utilisateur Discord et ton nom (scope <code>identify</code>). Le jeton d'accès de "
                        "Discord est révoqué juste après la connexion et n'est jamais stocké.</li><li>Un cookie de "
                        'session (<code>yatb_session</code>, valide 7 jours) te maintient connecté ; lors de la '
                        'connexion, un second cookie protège contre les connexions frauduleuses pendant au plus 10 '
                        'minutes. Les deux sont techniquement nécessaires et ne sont utilisés à aucune autre '
                        'fin.</li><li>Stocké sur notre serveur : un hash du jeton de session, ton identifiant Discord, '
                        "ton nom d'affichage, ta langue et la date d'expiration - supprimés lorsque tu te déconnectes "
                        'ou après 7 jours.</li><li>La possibilité de gérer un serveur est vérifiée par le bot '
                        'directement auprès de Discord à chaque requête. Les modifications que tu effectues sont '
                        'signalées dans le canal de journalisation de ce serveur avec ton nom.</li></ul>',
        'privacy_dash_title': 'Tableau de bord (connexion avec Discord)',
        'privacy_discord': 'Les messages sont rédigés et affichés sur Discord. Discord les traite selon sa propre <a '
                           'href="https://discord.com/privacy" rel="noopener">politique de confidentialité</a>.',
        'privacy_discord_title': '5. Discord',
        'privacy_lead': 'Cette page explique quelles données le site web de YATB et le bot Discord YATB traitent, '
                        'pourquoi et pendant combien de temps.',
        'privacy_rights': "Tu disposes d'un droit d'accès, de rectification, d'effacement, de limitation du "
                          "traitement, de portabilité des données et d'opposition, et tu peux déposer une plainte "
                          "auprès d'une autorité de contrôle de la protection des données. Pour exercer tes droits, "
                          "contacte l'opérateur (section 1). Sur Discord, <code>/yatb-user privacy</code> te permet de "
                          'choisir <em>Local uniquement</em> à tout moment.',
        'privacy_rights_title': '7. Tes droits',
        'privacy_services_intro': 'Les administrateurs de chaque serveur décident quels services traduisent leurs '
                                  'messages. Les messages des membres ayant choisi <em>Local uniquement</em> sont '
                                  'uniquement traduits par LibreTranslate sur notre propre serveur. Sur les serveurs '
                                  "gérés par l'opérateur, les comptes payants de l'opérateur sont utilisés.",
        'privacy_services_title': '4. Services de traduction',
        'privacy_title': 'Politique de confidentialité',
        'privacy_web': "<ul><li>Les pages d'information n'utilisent aucun cookie, aucun suivi, aucune analyse et "
                       "aucune police ou script externe.</li><li>Pour afficher les pages, l'adresse IP et la requête "
                       'de ton navigateur sont brièvement traitées par le serveur web. Le serveur web ne conserve pas '
                       "de journaux d'accès.</li><li>Le site web fonctionne sur un serveur d'Oracle Cloud à Francfort "
                       "(Allemagne). Les certificats HTTPS proviennent de Let's Encrypt ; aucune donnée de visiteur "
                       "n'est partagée pour cela.</li><li>Les liens vers d'autres sites (Discord, Ko-fi, fournisseurs) "
                       "sont des liens normaux - leurs politiques de confidentialité s'y appliquent.</li></ul>",
        'privacy_web_title': '2. Ce site web',
        'prov_azure': 'La traduction de texte ne stocke pas le texte (« no trace »). YATB utilise le point de '
                      "terminaison global, les requêtes peuvent donc être traitées dans n'importe quel centre de "
                      'données Microsoft, généralement le plus proche.',
        'prov_gemini': 'Uniquement pour les clés avec facturation activée - le niveau gratuit ne peut pas être utilisé '
                       "pour les utilisateurs de l'EEE, du Royaume-Uni ou de Suisse. Niveau payant : Google n'utilise "
                       'pas le contenu pour améliorer ses produits ; les requêtes sont enregistrées pendant une durée '
                       'limitée pour détecter les abus. Traité par Google dans le monde entier.',
        'prov_google_translate': "Le texte est uniquement conservé en mémoire pour la traduction et n'est pas utilisé "
                                 'pour entraîner ou améliorer la traduction de Google. Traité par Google dans le monde '
                                 'entier.',
        'prov_groq': "Par défaut, Groq ne conserve pas les données d'inférence ; les journaux pour le dépannage ou les "
                     "abus sont conservés jusqu'à 30 jours. La conservation zéro des données peut être activée pour "
                     'tout le monde sous <strong>Data Controls</strong>. Les données sont stockées aux États-Unis.',
        'prov_libre': "Fonctionne sur notre propre serveur à Francfort (Allemagne). Rien n'est envoyé à des tiers.",
        'prov_mistral': 'Mistral AI (France). Aucun entraînement sur ton contenu - sauf si un paramètre du produit le '
                        "permet : dans la console Mistral sous <strong>Privacy</strong>, désactive l'utilisation des "
                        "données API pour l'amélioration. Le forfait gratuit peut utiliser les données pour "
                        "l'entraînement, sauf si tu t'y opposes. Un DPA est disponible, aucune conservation des "
                        'données sur demande.',
        'prov_novita': 'Selon ses conditions : aucune conservation des données et aucun entraînement sur ton contenu '
                       "par défaut. Les métadonnées d'utilisation sont conservées jusqu'à 2 ans ; les données peuvent "
                       'être traitées aux États-Unis (SCC). Un DPA est disponible uniquement pour les clients '
                       'entreprises. Régie par la loi du Delaware, États-Unis.',
        'setup_1': '<strong>Vérifie les permissions.</strong> Dans chaque canal lié, YATB a besoin de : {perms}.',
        'setup_2': '<strong>Relie les salons.</strong> Les salons portant le même nom de Bridge sont traduits les uns '
                   'vers les autres :<br><code>/yatb bridge add chat #english English</code><br><code>/yatb bridge add '
                   'chat #deutsch German</code><br>Les salons de forum et de médias fonctionnent de la même manière - '
                   "toujours forum avec forum. YATB crée lui-même les tags manquants s'il dispose de la permission "
                   '<em>Gérer les salons</em> dans le forum.',
        'setup_3': '<strong>Ajoute des clés API (optionnel).</strong> Sans clés, YATB utilise LibreTranslate. Pour une '
                   'meilleure qualité, ajoute des clés avec <code>/yatb keys add</code> - voir <a href="keys">clés '
                   'API</a>.',
        'setup_4': '<strong>Définit un canal de journalisation.</strong> <code>/yatb log set</code> - YATB y signale '
                   "les avertissements d'utilisation, les problèmes de clés et les changements.",
        'setup_5': '<strong>Informe tes membres.</strong> Fais un lien vers le <a href="members">guide des membres</a> '
                   'ou ajoute une règle courte, par exemple :',
        'setup_check': "<code>/yatb status</code> affiche la chaîne de traduction de ton serveur et l'état de chaque "
                       'service.',
        'setup_rule': 'Traduction (YATB) : Dans les canaux liés, le bot YATB traduit automatiquement les messages et '
                      'les republie sous ton nom. Pour cela, ils peuvent être envoyés à des services externes (ex. : '
                      "fournisseurs d'IA, Google). Les textes des messages ne sont pas stockés. Traduction Local "
                      'uniquement : /yatb-user privacy',
        'site_desc': 'YATB relie des salons Discord dans différentes langues et traduit chaque message - sous le nom '
                     "de l'auteur.",
        'tag_ai': "Fournisseur d'IA (par exemple Mistral ou Google Gemini) - généralement la meilleure qualité",
        'tag_azure': 'Azure Translator (Microsoft)',
        'tag_google': 'Google Translate',
        'tag_libre': 'LibreTranslate - hébergé sur notre propre serveur',
        'tag_raw': "Non traduit - aucun service n'était disponible à ce moment-là",
        'terms_1': 'YATB est un projet privé et non commercial. Il est gratuit, ne fonctionne actuellement que sur '
                   'certains serveurs et est fourni sans aucune garantie de disponibilité. Les fonctionnalités peuvent '
                   "changer ou s'arrêter à tout moment.",
        'terms_1_title': '1. Le service',
        'terms_2': "Les traductions sont effectuées par des machines et peuvent être erronées ou incomplètes. Ne t'y "
                   'fie pas pour des questions importantes, juridiques, médicales ou financières.',
        'terms_2_title': '2. Traductions',
        'terms_3': '<ul><li>Tu es responsable des clés API que tu ajoutes, des conditions de leurs fournisseurs et des '
                   "coûts associés. Le comptage de l'utilisation par YATB est une estimation - définis des limites de "
                   'dépenses chez le fournisseur.</li><li>Informe tes membres que les messages dans les canaux liés '
                   '(Bridge) sont traduits et peuvent être envoyés à des services externes.</li><li>Utilise YATB '
                   "uniquement conformément à la loi et aux conditions de Discord - pas de spam, pas d'abus.</li></ul>",
        'terms_3_title': '3. Administrateurs de serveur',
        'terms_4': "YATB est fourni gratuitement et en l'état. La responsabilité est limitée au dol et à la faute "
                   'lourde, dans la mesure où la loi le permet.',
        'terms_4_title': '4. Responsabilité',
        'terms_5': 'Les dons (par exemple via Ko-fi) sont volontaires et ne créent aucun droit à des fonctionnalités, '
                   'à un support ou à une disponibilité.',
        'terms_5_title': '5. Dons',
        'terms_6': "Le droit allemand s'applique.",
        'terms_6_title': '6. Dispositions finales',
        'terms_lead': 'Court et simple : YATB est un projet amateur gratuit. En utilisant YATB sur un serveur, tu '
                      'acceptes ces conditions.',
        'terms_title': "Conditions d'utilisation"},
 'it': {'admins_chain_intro': 'Per ogni messaggio, YATB prova i servizi in questo ordine e utilizza il primo risultato '
                              'valido:',
        'admins_chain_note': 'Ogni risposta viene controllata (menzioni, link, formattazione). Una risposta errata, un '
                             'errore o un limite raggiunto fanno passare al servizio successivo; un servizio non '
                             "funzionante viene ignorato per un po'. I membri con <em>Solo locale</em> ricevono sempre "
                             'LibreTranslate.',
        'admins_chain_title': 'La catena di traduzione',
        'admins_col_command': 'Comando',
        'admins_col_desc': 'Descrizione',
        'admins_commands_title': 'Tutti i comandi',
        'admins_dashboard': '<p>Nel <a href="{url}">pannello di controllo</a> accedi con Discord e vedi tutti i server '
                            'con YATB di cui sei amministratore.</p><ul><li>Utilizzo per chiave API: oggi e questo '
                            'mese, rispetto ai limiti gratuiti o al tuo budget - si aggiorna '
                            "automaticamente.</li><li>Modifica l'etichetta, il piano, il budget e il limite di una "
                            'chiave, oppure rimuovila. La chiave vera e propria non viene mai mostrata o inserita sul '
                            "sito: aggiungere una chiave resta un modulo su Discord.</li><li>Modifica l'ordine della "
                            'catena di traduzione.</li><li>Statistiche per 7, 30 e 90 giorni: chiamate, successo e '
                            'volume per servizio.</li><li>Ogni modifica viene segnalata nel canale log del server con '
                            'il tuo nome.</li></ul>',
        'admins_dashboard_title': 'Pannello di controllo',
        'admins_forum': '<ul><li>Collega i forum come i canali testuali, ad esempio <code>/yatb bridge add forum '
                        '#forum-en English</code>. Un Bridge contiene solo forum o solo canali testuali, mai entrambi. '
                        'I canali media funzionano allo stesso modo.</li><li>Un nuovo post appare in ogni altro forum '
                        "del Bridge: titolo e testo tradotti, tag corrispondenti, sotto il nome dell'autore. Risposte, "
                        "modifiche, eliminazioni e reazioni all'interno del post vengono replicate.</li><li>La "
                        'ridenominazione, la modifica dei tag, la chiusura o il blocco del post originale vengono '
                        'applicati alle copie.</li><li>I tag vengono abbinati 1:1. YATB crea da solo i tag mancanti '
                        "(nome tradotto, stessa emoji) se dispone dell'autorizzazione <em>Gestisci canali</em>; in "
                        'caso contrario, vengono abbinati solo i tag con lo stesso nome. Discord consente 20 tag per '
                        'forum.</li></ul>',
        'admins_forum_perms': '<p>Dove concedere <em>Gestisci canali</em>:</p><ul><li><strong>Sulla categoria dei '
                              'forum</strong> (consigliato): tutti i forum al suo interno sono coperti, inclusi quelli '
                              'nuovi, e il resto del server rimane protetto.</li><li><strong>Su ogni singolo '
                              "forum</strong>: l'opzione più restrittiva, ma ogni nuovo forum necessita nuovamente "
                              "dell'autorizzazione.</li><li><strong>A livello di server</strong> (ruolo del bot o link "
                              "d'invito): la più comoda, ma il bot potrebbe modificare o eliminare qualsiasi canale; "
                              'se il suo token venisse rubato, il danno sarebbe molto maggiore.</li></ul>',
        'admins_forum_title': 'Forum e canali media',
        'admins_lead': 'YATB è un bot privato. Se è presente sul tuo server, ecco come configurarlo. Tutti i comandi '
                       'sono sotto <code>/yatb</code> e visibili solo agli amministratori.',
        'admins_limits': "<ul><li><strong>Chiavi gratuite:</strong> YATB conteggia l'utilizzo rispetto ai limiti "
                         'gratuiti del provider al minuto, al giorno e al mese.</li><li><strong>Chiavi a '
                         'pagamento:</strong> imposti un budget mensile in USD o EUR. YATB stima il costo in base alle '
                         'tariffe pubblicate: imposta anche un limite di spesa sul provider.</li><li>I limiti '
                         'giornalieri si resettano alle 00:00 UTC, quelli mensili il 1° del mese alle 00:00 '
                         'UTC.</li><li>Avvisi al 90, 95 e 100% vengono inviati al canale log. Quando una chiave è '
                         'esaurita, subentra il servizio successivo.</li><li>Se la stessa chiave viene usata su più '
                         "server, l'utilizzo viene conteggiato insieme. Gli altri server non vengono mai "
                         "menzionati.</li><li><code>/yatb keys list</code> e il pannello mostrano l'utilizzo per "
                         'chiave, <code>/yatb keys edit</code> modifica piano, budget e limite.</li></ul>',
        'admins_limits_title': 'Utilizzo, limiti e budget',
        'admins_remove': '<code>/yatb reset</code> elimina tutti i Bridge, le chiavi e le impostazioni del tuo server. '
                         '<code>/yatb uninstall</code> elimina tutti i dati del tuo server e il bot esce.',
        'admins_remove_title': 'Rimozione di YATB',
        'admins_security': 'Le chiavi vengono inserite in un modulo privato di Discord, mai come opzione di comando. '
                           'Vengono archiviate crittografate (AES-256-GCM, separatamente per ogni server) e non '
                           'vengono mai mostrate di nuovo, ad eccezione degli ultimi 4 caratteri. Questo sito web non '
                           'mostra né accetta mai chiavi.',
        'admins_security_title': 'Come sono protette le chiavi',
        'admins_setup_title': 'Configurazione in 5 passaggi',
        'admins_title': 'Per gli amministratori del server',
        'chain_1': '<strong>Provider AI</strong> con le tue chiavi - prima i gruppi di qualità migliore, poi le chiavi '
                   'gratuite e infine quelle a pagamento',
        'chain_2': '<strong>Google Translate</strong>',
        'chain_3': '<strong>Azure Translator</strong>',
        'chain_4': '<strong>LibreTranslate</strong> sul nostro server - sempre disponibile',
        'chain_5': "<strong>[Raw]</strong> - il testo originale, se nient'altro ha funzionato",
        'faq_dm_a': 'No. YATB elabora solo i messaggi nei canali che gli amministratori hanno collegato a un Bridge.',
        'faq_dm_q': 'YATB legge i miei messaggi diretti o altri canali?',
        'faq_off_a': 'I messaggi nei canali collegati vengono sempre tradotti, in modo che tutti possano seguire la '
                     'conversazione. Con <em>Solo locale</em> rimangono sul nostro server. I canali non collegati non '
                     'vengono mai toccati.',
        'faq_off_q': 'Posso disattivare completamente la traduzione?',
        'faq_wrong_a': 'Modifica il tuo messaggio: anche la traduzione verrà aggiornata. Se un termine viene sempre '
                       'tradotto in modo errato, segnalalo agli amministratori del tuo server.',
        'faq_wrong_q': 'La traduzione è errata. Cosa posso fare?',
        'feat_fallback_text': 'Senza alcuna chiave, YATB traduce con LibreTranslate sul nostro server: gratuito e '
                              'nulla lascia il server.',
        'feat_fallback_title': 'Sempre una traduzione',
        'feat_format_text': 'Grassetto, elenchi, citazioni, spoiler, emoji, menzioni e link rimangono intatti. Il '
                            'codice reale viene lasciato non tradotto.',
        'feat_format_title': 'Mantiene la formattazione di Discord',
        'feat_keys_text': 'Gli amministratori del server aggiungono le proprie chiavi API in un modulo privato. Le '
                          'chiavi vengono archiviate crittografate e non vengono mai più mostrate. Limiti e avvisi sul '
                          'budget inclusi.',
        'feat_keys_title': 'Le tue chiavi, il tuo budget',
        'feat_mirror_text': 'Risposte, modifiche, eliminazioni, reazioni e thread vengono replicati in tutti i canali '
                            'collegati. Anche gli annunci dai canali seguiti vengono tradotti.',
        'feat_mirror_title': 'Rispecchia la conversazione',
        'feat_natural_text': 'Traduzione IA che comprende la conversazione: slang, termini di gioco e risposte brevi '
                             'vengono tradotti correttamente. Se un servizio fallisce, subentra il successivo.',
        'feat_natural_title': 'Traduzioni naturali',
        'feat_privacy_text': 'Nessun testo dei messaggi viene archiviato. Ogni membro può scegliere che i propri '
                             'messaggi vengano tradotti solo sul nostro server.',
        'feat_privacy_title': 'Privacy by design',
        'footer_note': 'YATB è un progetto privato e non commerciale e non è affiliato a Discord.',
        'home_badge_langs': '7 lingue',
        'home_badge_private': 'Bot privato',
        'home_badge_storage': 'Nessun testo dei messaggi archiviato',
        'home_example_note': 'Esempio di una coppia di canali collegati. Il tag dopo il nome indica quale servizio ha '
                             'effettuato la traduzione.',
        'home_example_src': 'Anyone up for a raid tonight? Meet at 8 pm in <span class="mention">#voice</span> 🎮',
        'home_example_tgt': 'Qualcuno è disponibile per un raid stasera? Ci vediamo alle 20:00 in <span '
                            'class="mention">#voice</span> 🎮',
        'home_example_tgt_channel': 'italiano',
        'home_example_title': 'Esempio',
        'home_features_title': 'Cosa fa YATB',
        'home_how_title': 'Come funziona',
        'home_lead': 'YATB - <em>Yet Another Translation Bot</em> - collega canali in lingue diverse. Ognuno scrive '
                     "nella propria lingua, YATB pubblica la traduzione negli altri canali, sotto il nome e l'avatar "
                     "dell'autore.",
        'home_private_text': 'Al momento no. YATB è un bot privato e funziona solo su server selezionati. Se YATB è '
                             'già sul tuo server, consulta le guide <a href="members">per i membri</a> e <a '
                             'href="admins">per gli amministratori</a>.',
        'home_private_title': 'Posso aggiungere YATB al mio server?',
        'home_support_text': 'YATB è gratuito e senza pubblicità. Se vuoi contribuire ai costi di gestione, puoi '
                             'sostenerlo su Ko-fi.',
        'home_support_title': 'Ti piace YATB?',
        'home_title': 'Comunica in diverse lingue su Discord',
        'how_1': '<strong>Gli amministratori collegano i canali</strong> - ad esempio <code>#english</code> e '
                 '<code>#deutsch</code> - in un unico Bridge.',
        'how_2': '<strong>I membri scrivono semplicemente</strong> nella propria lingua. Non servono comandi.',
        'how_3': '<strong>YATB pubblica la traduzione</strong> negli altri canali nel giro di pochi secondi.',
        'imprint_title': 'Note legali',
        'keys_kind_ai': 'Provider AI',
        'keys_kind_mt': 'Servizio di traduzione',
        'keys_lead': 'Le chiavi API rendono le traduzioni migliori rispetto al LibreTranslate gratuito. Ogni chiave '
                     'appartiene a te o al tuo server: YATB la utilizza solo per il tuo server e la archivia '
                     'crittografata.',
        'keys_menu_note': "I nomi dei menu presso i fornitori possono cambiare. Stato dell'informativa sulla privacy: "
                          '{date}.',
        'keys_open': 'Apri console',
        'keys_plan': 'Piano',
        'keys_privacy': 'Privacy',
        'keys_source': 'Informativa sulla privacy del fornitore',
        'keys_steps': 'Passaggi',
        'keys_tips': "<ul><li>Imposta un <strong>limite di spesa</strong> nell'account del tuo provider oltre al "
                     'budget in YATB.</li><li>Dove disponibile, attiva la <strong>conservazione zero dei dati</strong> '
                     "o disattiva l'addestramento sui tuoi dati.</li><li>Aggiungi chiavi con <code>/yatb keys "
                     'add</code>: scegli il provider, quindi incolla la chiave nel modulo privato.</li></ul>',
        'keys_title': 'Ottenere chiavi API',
        'kofi': 'Supporta YATB su Ko-fi',
        'lang_name': 'Italiano',
        'legal_binding': 'Questo testo è disponibile in diverse lingue. In caso di discrepanze, fa fede la versione '
                         'tedesca.',
        'legal_updated': 'Ultimo aggiornamento: {date}',
        'members_choice_local': '<strong>Solo locale</strong> - i tuoi messaggi vengono tradotti solo da '
                                'LibreTranslate sul nostro server e non vengono mai inviati a fornitori di IA, Google '
                                'o Azure, nemmeno come contesto per le traduzioni di altre persone. La qualità è '
                                'inferiore.',
        'members_choice_note': "L'impostazione è visibile solo a te e si applica a ogni server con YATB. "
                               '<code>/yatb-user help</code> mostra un breve riepilogo su Discord.',
        'members_choice_standard': '<strong>Standard</strong> - qualità migliore. I tuoi messaggi potrebbero essere '
                                   'inviati ai servizi aggiunti dagli amministratori.',
        'members_choice_title': 'La tua scelta: <code>/yatb-user privacy</code>',
        'members_dashboard': 'Puoi anche controllare e modificare la tua scelta nel <a href="{url}">pannello di '
                             'controllo</a> (accedi con Discord).',
        'members_data': '<ul><li>YATB <strong>non memorizza i testi dei messaggi</strong>. Ricorda solo quale '
                        'messaggio appartiene a quale traduzione, per {map_days} giorni, in modo che le modifiche e le '
                        'eliminazioni possano essere sincronizzate.</li><li>Per tradurre, il tuo messaggio viene '
                        'inviato ai servizi di traduzione scelti dagli amministratori del tuo server (vedi <a '
                        'href="privacy">privacy</a>).</li><li>I fornitori di IA ricevono anche fino a {context_lines} '
                        'messaggi precedenti della stessa conversazione come contesto, affinché le risposte brevi '
                        'vengano tradotte correttamente.</li></ul>',
        'members_data_title': 'I tuoi dati',
        'members_faq_title': 'Domande',
        'members_how': '<ul><li>Scrivi nella tua lingua in un canale collegato. YATB pubblica una traduzione negli '
                       'altri canali collegati, a tuo nome e con il tuo avatar.</li><li>Risposte, modifiche, '
                       'eliminazioni e thread vengono rispecchiati. Anche le reazioni: appaiono negli altri canali '
                       'come reazione da parte di YATB.</li><li>Formattazione, emoji, menzioni e link vengono '
                       'mantenuti.</li><li>La traduzione appare negli altri canali: le persone che non possono vedere '
                       'il tuo canale potrebbero comunque leggerla lì.</li></ul>',
        'members_how_title': 'Come funziona',
        'members_lead': 'Alcuni canali sul tuo server sono collegati da YATB. Ecco cosa significa per te.',
        'members_tags_intro': "Ogni traduzione mostra quale servizio l'ha effettuata:",
        'members_tags_title': 'Il tag dopo il nome',
        'members_title': 'Per i membri',
        'nav_admins': 'Per gli amministratori',
        'nav_dashboard': 'Pannello di controllo',
        'nav_home': 'Home',
        'nav_imprint': 'Note legali',
        'nav_keys': 'Chiavi API',
        'nav_language': 'Lingua',
        'nav_members': 'Per i membri',
        'nav_menu': 'Menu',
        'nav_more': 'Altri progetti di Gladi',
        'nav_privacy': 'Privacy',
        'nav_terms': 'Termini',
        'not_found_text': 'Questa pagina non esiste. Torna alla <a href="/">home page</a>.',
        'not_found_title': 'Pagina non trovata',
        'pd_backup_how_long': '14 giorni sul server, 30 giorni in Oracle Object Storage (Francoforte)',
        'pd_backup_what': 'Backup crittografati dei dati sopra indicati (mai i testi dei messaggi)',
        'pd_backup_why': 'Ripristino dopo errori',
        'pd_choice_how_long': "Fino a quando non richiedi l'eliminazione",
        'pd_choice_what': 'Il tuo ID utente e la tua scelta sulla privacy',
        'pd_choice_why': 'Rispettare <code>/yatb-user privacy</code> su ogni server',
        'pd_config_how_long': 'Fino alla rimozione, <code>/yatb reset</code> o <code>/yatb uninstall</code>',
        'pd_config_what': 'Impostazioni del server: Bridge, canale di log, chiavi API crittografate, ID '
                          "dell'amministratore che ha aggiunto una chiave",
        'pd_config_why': 'Esecuzione del bot sul server',
        'pd_map_how_long': '{map_days} giorni',
        'pd_map_what': 'ID dei messaggi e un checksum del testo',
        'pd_map_why': 'Rispecchiare risposte, modifiche ed eliminazioni nelle traduzioni',
        'pd_stats_how_long': '{raw_days} giorni, dopodiché solo totali giornalieri per server',
        'pd_stats_what': 'Statistiche di utilizzo: server, servizio, lingue, numero di caratteri, durata, risultato - '
                         'nessun testo, nessun ID utente',
        'pd_stats_why': 'Limiti, costi, affidabilità dei servizi',
        'pd_text_how_long': 'Non memorizzato. Mantenuto in memoria solo durante la traduzione; il contesto dei '
                            'messaggi recenti viene perso a ogni riavvio.',
        'pd_text_what': 'Testo del messaggio e nome visualizzato',
        'pd_text_why': 'Traduzione; inviata ai servizi di traduzione del server (vedi 4). I fornitori di IA ricevono '
                       'fino a {context_lines} dei tuoi stessi messaggi precedenti nello stesso Bridge come contesto — '
                       'mai quelli di altre persone.',
        'privacy_basis': "Art. 6(1)(f) GDPR - il nostro legittimo interesse, e l'interesse delle community dei server, "
                         'a una comunicazione multilingue e a un servizio sicuro e affidabile. La tua scelta di '
                         "<em>Solo locale</em> limita l'elaborazione al nostro server.",
        'privacy_basis_title': '6. Base giuridica',
        'privacy_bot_intro': 'YATB elabora i messaggi solo nei canali che gli amministratori di un server hanno '
                             'collegato a un Bridge.',
        'privacy_bot_title': '3. Il bot Discord',
        'privacy_col_how_long': 'Conservazione',
        'privacy_col_note': 'Cosa dice il provider',
        'privacy_col_service': 'Servizio',
        'privacy_col_what': 'Dati',
        'privacy_col_why': 'Scopo',
        'privacy_controller_missing': 'I dettagli di contatto del gestore verranno aggiunti qui.',
        'privacy_controller_title': '1. Chi è il responsabile',
        'privacy_dash': '<ul><li>Su <code>/app</code> puoi accedere con Discord. YATB riceve solo il tuo ID utente '
                        'Discord e il nome (scope <code>identify</code>). Il token di accesso di Discord viene '
                        "revocato subito dopo l'accesso e non viene mai memorizzato.</li><li>Un cookie di sessione "
                        "(<code>yatb_session</code>, valido 7 giorni) ti mantiene connesso; durante l'accesso, un "
                        'secondo cookie protegge da accessi contraffatti per un massimo di 10 minuti. Entrambi sono '
                        "tecnicamente necessari e non vengono utilizzati per nient'altro.</li><li>Memorizzati sul "
                        'nostro server: un hash del token di sessione, il tuo ID Discord, il nome visualizzato, la '
                        'lingua e la data di scadenza - eliminati quando effettui il logout o dopo 7 '
                        'giorni.</li><li>La possibilità di gestire un server viene verificata dal bot direttamente con '
                        'Discord a ogni richiesta. Le modifiche che apporti vengono segnalate nel canale log di quel '
                        'server con il tuo nome.</li></ul>',
        'privacy_dash_title': 'Dashboard (accesso con Discord)',
        'privacy_discord': 'I messaggi vengono scritti e visualizzati su Discord. Discord li elabora secondo la '
                           'propria <a href="https://discord.com/privacy" rel="noopener">informativa sulla '
                           'privacy</a>.',
        'privacy_discord_title': '5. Discord',
        'privacy_lead': 'Questa pagina spiega quali dati elaborano il sito web di YATB e il bot Discord YATB, perché e '
                        'per quanto tempo.',
        'privacy_rights': 'Hai il diritto di accesso, rettifica, cancellazione, limitazione del trattamento, '
                          "portabilità dei dati e di opposizione, e puoi presentare reclamo a un'autorità di controllo "
                          'per la protezione dei dati. Per esercitare i tuoi diritti, contatta il gestore (sezione 1). '
                          'Su Discord, <code>/yatb-user privacy</code> ti permette di scegliere <em>Solo locale</em> '
                          'in qualsiasi momento.',
        'privacy_rights_title': '7. I tuoi diritti',
        'privacy_services_intro': 'Gli amministratori di ogni server decidono quali servizi traducono i loro messaggi. '
                                  'I messaggi dei membri con <em>Solo locale</em> vengono tradotti solo da '
                                  "LibreTranslate sul nostro server. Sui server gestiti dall'operatore, vengono "
                                  "utilizzati gli account a pagamento dell'operatore stesso.",
        'privacy_services_title': '4. Servizi di traduzione',
        'privacy_title': 'Informativa sulla privacy',
        'privacy_web': '<ul><li>Le pagine informative non utilizzano cookie, tracciamento, analisi o font o script '
                       "esterni.</li><li>Per fornire le pagine, l'indirizzo IP del tuo browser e la richiesta vengono "
                       'elaborati brevemente dal server web. Il server web non conserva log di accesso.</li><li>Il '
                       'sito web è ospitato su un server di Oracle Cloud a Francoforte (Germania). I certificati HTTPS '
                       "provengono da Let's Encrypt; nessun dato dei visitatori viene condiviso per questo.</li><li>I "
                       'link ad altri siti (Discord, Ko-fi, fornitori) sono link normali: lì si applicano le loro '
                       'informative sulla privacy.</li></ul>',
        'privacy_web_title': '2. Questo sito web',
        'prov_azure': 'La traduzione del testo non archivia il testo ("nessuna traccia"). YATB utilizza l\'endpoint '
                      'globale, quindi le richieste possono essere elaborate in qualsiasi data center Microsoft, '
                      'solitamente quello più vicino.',
        'prov_gemini': 'Solo chiavi con fatturazione attiva - il piano gratuito potrebbe non essere utilizzabile per '
                       'gli utenti nello SEE, nel Regno Unito o in Svizzera. Piano a pagamento: Google non utilizza i '
                       'contenuti per migliorare i propri prodotti; i prompt vengono registrati per un periodo '
                       'limitato per rilevare abusi. Elaborato da Google a livello globale.',
        'prov_google_translate': 'Il testo viene mantenuto in memoria solo per la traduzione e non viene utilizzato '
                                 'per addestrare o migliorare la traduzione di Google. Elaborato da Google a livello '
                                 'globale.',
        'prov_groq': 'Per impostazione predefinita, Groq non conserva i dati di inferenza; i log per la risoluzione '
                     'dei problemi o gli abusi vengono conservati fino a 30 giorni. La conservazione dei dati pari a '
                     'zero può essere attivata per chiunque sotto <strong>Data Controls</strong>. I dati sono '
                     'archiviati negli Stati Uniti.',
        'prov_libre': 'Eseguito sul nostro server a Francoforte (Germania). Nulla viene inviato a terze parti.',
        'prov_mistral': 'Mistral AI (Francia). Nessun addestramento sui tuoi contenuti, salvo dove consentito da '
                        "un'impostazione del prodotto: nella console Mistral, sotto <strong>Privacy</strong>, "
                        "disattiva l'uso dei dati API per il miglioramento. Il piano gratuito potrebbe utilizzare i "
                        "dati per l'addestramento a meno che tu non scelga di non partecipare. È disponibile un DPA, "
                        'conservazione dei dati pari a zero su richiesta.',
        'prov_novita': 'Secondo i suoi termini: conservazione dei dati pari a zero e nessun addestramento sui tuoi '
                       'contenuti per impostazione predefinita. I metadati di utilizzo vengono conservati fino a 2 '
                       'anni; i dati possono essere elaborati negli Stati Uniti (SCC). Un DPA è disponibile solo per i '
                       'clienti enterprise. Disciplinato dalla legge del Delaware, USA.',
        'setup_1': '<strong>Controlla i permessi.</strong> In ogni canale collegato YATB necessita di: {perms}.',
        'setup_2': '<strong>Collega i canali.</strong> I canali con lo stesso nome di Bridge vengono tradotti tra '
                   'loro:<br><code>/yatb bridge add chat #english English</code><br><code>/yatb bridge add chat '
                   '#deutsch German</code><br>I canali forum e media funzionano allo stesso modo: sempre forum con '
                   'forum. YATB crea da solo i tag mancanti se ha il permesso di <em>Gestire i canali</em> nel forum.',
        'setup_3': '<strong>Aggiungi chiavi API (opzionale).</strong> Senza chiavi YATB utilizza LibreTranslate. Per '
                   'una qualità migliore aggiungi le chiavi con <code>/yatb keys add</code> - vedi <a '
                   'href="keys">chiavi API</a>.',
        'setup_4': '<strong>Imposta un canale di log.</strong> <code>/yatb log set</code> - YATB vi segnalerà avvisi '
                   "sull'utilizzo, problemi con le chiavi e modifiche.",
        'setup_5': '<strong>Informa i tuoi membri.</strong> Inserisci un link alla <a href="members">guida per i '
                   'membri</a> o aggiungi una breve regola, ad esempio:',
        'setup_check': '<code>/yatb status</code> mostra la catena di traduzione del tuo server e lo stato di ogni '
                       'servizio.',
        'setup_rule': 'Traduzione (YATB): Nei canali collegati, il bot YATB traduce automaticamente i messaggi e li '
                      'ripubblica a tuo nome. Per farlo, i testi potrebbero essere inviati a servizi esterni (es. '
                      'provider AI, Google). I testi dei messaggi non vengono archiviati. Traduzione Solo locale: '
                      '/yatb-user privacy',
        'site_desc': 'YATB collega canali Discord in lingue diverse e traduce ogni messaggio sotto il nome '
                     "dell'autore.",
        'tag_ai': 'Fornitore IA (ad esempio Mistral o Google Gemini) - solitamente la qualità migliore',
        'tag_azure': 'Azure Translator (Microsoft)',
        'tag_google': 'Google Translate',
        'tag_libre': 'LibreTranslate - eseguito sul nostro server',
        'tag_raw': 'Non tradotto - nessun servizio era disponibile in quel momento',
        'terms_1': 'YATB è un progetto privato e non commerciale. È gratuito, attualmente funziona solo su server '
                   'selezionati e viene fornito senza alcuna garanzia di disponibilità. Le funzionalità possono '
                   'cambiare o terminare in qualsiasi momento.',
        'terms_1_title': '1. Il servizio',
        'terms_2': 'Le traduzioni sono effettuate da macchine e possono essere errate o incomplete. Non fare '
                   'affidamento su di esse per questioni importanti, legali, mediche o finanziarie.',
        'terms_2_title': '2. Traduzioni',
        'terms_3': '<ul><li>Sei responsabile delle chiavi API che aggiungi, dei termini dei relativi fornitori e dei '
                   "costi. Il conteggio dell'utilizzo di YATB è una stima: imposta dei limiti di spesa presso il "
                   'fornitore.</li><li>Informa i tuoi membri che i messaggi nei canali collegati (Bridge) vengono '
                   'tradotti e potrebbero essere inviati a servizi esterni.</li><li>Utilizza YATB solo in conformità '
                   'con la legge e i termini di Discord: niente spam, niente abusi.</li></ul>',
        'terms_3_title': '3. Amministratori del server',
        'terms_4': "YATB è fornito gratuitamente e così com'è. La responsabilità è limitata al dolo e alla colpa "
                   'grave, per quanto consentito dalla legge.',
        'terms_4_title': '4. Responsabilità',
        'terms_5': 'Le donazioni (ad esempio tramite Ko-fi) sono volontarie e non creano alcun diritto a funzionalità, '
                   'supporto o disponibilità.',
        'terms_5_title': '5. Donazioni',
        'terms_6': 'Si applica la legge tedesca.',
        'terms_6_title': '6. Disposizioni finali',
        'terms_lead': 'Breve e semplice: YATB è un progetto amatoriale gratuito. Utilizzando YATB su un server, '
                      'accetti questi termini.',
        'terms_title': 'Termini di utilizzo'},
 'nl': {'admins_chain_intro': 'Voor elk bericht probeert YATB de diensten in deze volgorde en neemt het eerste goede '
                              'resultaat:',
        'admins_chain_note': 'Elk antwoord wordt gecontroleerd (vermeldingen, links, opmaak). Een slecht antwoord, een '
                             'fout of een bereikte limiet zorgt voor een overstap naar de volgende dienst; een falende '
                             'dienst wordt tijdelijk overgeslagen. Leden met <em>Alleen lokaal</em> krijgen altijd '
                             'LibreTranslate.',
        'admins_chain_title': 'De vertaalketen',
        'admins_col_command': 'Commando',
        'admins_col_desc': 'Beschrijving',
        'admins_commands_title': "Alle commando's",
        'admins_dashboard': '<p>In de <a href="{url}">dashboard</a> log je in met Discord en zie je elke server met '
                            'YATB waarop je beheerder bent.</p><ul><li>Gebruik per API-sleutel: vandaag en deze maand, '
                            'tegen de gratis limieten of je budget – het wordt automatisch bijgewerkt.</li><li>Wijzig '
                            'de label, het plan, budget en limiet van een sleutel, of verwijder een sleutel. De '
                            'sleutel zelf wordt nooit getoond of ingevoerd op de website – een sleutel toevoegen '
                            'blijft een formulier in Discord.</li><li>Wijzig de volgorde van de '
                            'vertaalketen.</li><li>Statistieken voor 7, 30 en 90 dagen: oproepen, succes en volume per '
                            'dienst.</li><li>Elke wijziging wordt gemeld in het logkanaal van de server met je '
                            'naam.</li></ul>',
        'admins_dashboard_title': 'Dashboard',
        'admins_forum': '<ul><li>Koppel forums zoals tekstkanalen, bijv. <code>/yatb bridge add forum #forum-en '
                        'English</code>. Een Bridge bevat ofwel forums ofwel tekstkanalen, nooit beide. Mediakanalen '
                        'werken op dezelfde manier.</li><li>Een nieuw bericht verschijnt in elk ander forum van de '
                        'Bridge - vertaalde titel en tekst, overeenkomende tags, onder de naam van de auteur. '
                        'Antwoorden, bewerkingen, verwijderingen en reacties binnen het bericht worden '
                        'gespiegeld.</li><li>Het hernoemen, opnieuw taggen, sluiten of vergrendelen van het originele '
                        'bericht wordt toegepast op de kopieën.</li><li>Tags worden 1:1 gekoppeld. YATB maakt '
                        'ontbrekende tags zelf aan (vertaalde naam, zelfde emoji) als het de toestemming <em>Kanalen '
                        'beheren</em> heeft - anders worden alleen tags met dezelfde naam gekoppeld. Discord staat 20 '
                        'tags per forum toe.</li></ul>',
        'admins_forum_perms': '<p>Waar je <em>Kanalen beheren</em> moet verlenen:</p><ul><li><strong>Op de categorie '
                              'van de forums</strong> (aanbevolen): alle forums daarin worden gedekt, inclusief '
                              'nieuwe, en de rest van de server blijft beschermd.</li><li><strong>Op elk '
                              'forum</strong>: de meest beperkte optie, maar elk nieuw forum heeft het opnieuw '
                              'nodig.</li><li><strong>Serverbreed</strong> (botrol of uitnodigingslink): de handigste '
                              'optie, maar de bot zou dan elk kanaal kunnen bewerken of verwijderen - als het token '
                              'ooit gestolen zou worden, zou de schade veel groter zijn.</li></ul>',
        'admins_forum_title': 'Forum- en mediakanalen',
        'admins_lead': 'YATB is een privébot. Als deze op je server staat, kun je hem als volgt instellen. Alle '
                       "commando's staan onder <code>/yatb</code> en zijn alleen zichtbaar voor beheerders.",
        'admins_limits': '<ul><li><strong>Gratis sleutels:</strong> YATB telt het gebruik mee tegen de gratis limieten '
                         'van de provider per minuut, dag en maand.</li><li><strong>Betaalde sleutels:</strong> je '
                         'stelt een maandbudget in in USD of EUR. YATB schat de kosten in op basis van de lijstprijzen '
                         '– stel ook een uitgavenlimiet in bij de provider.</li><li>Dagelijkse limieten resetten om '
                         '00:00 UTC, maandelijkse limieten op de 1e om 00:00 UTC.</li><li>Waarschuwingen bij 90, 95 en '
                         '100 % gaan naar het logkanaal. Als een sleutel op is, neemt de volgende dienst het '
                         'over.</li><li>Als dezelfde sleutel op meerdere servers wordt gebruikt, wordt het gebruik '
                         'samengeteld. Andere servers worden nooit genoemd.</li><li><code>/yatb keys list</code> en de '
                         'dashboard tonen het gebruik per sleutel, <code>/yatb keys edit</code> wijzigt plan, budget '
                         'en limiet.</li></ul>',
        'admins_limits_title': 'Gebruik, limieten en budget',
        'admins_remove': '<code>/yatb reset</code> verwijdert alle Bridges, sleutels en instellingen van je server. '
                         '<code>/yatb uninstall</code> verwijdert alle gegevens van je server en de bot verlaat de '
                         'server.',
        'admins_remove_title': 'YATB verwijderen',
        'admins_security': 'Sleutels worden ingevoerd in een privé Discord-formulier, nooit als een commando-optie. Ze '
                           'worden versleuteld opgeslagen (AES-256-GCM, apart per server) en worden nooit meer getoond '
                           '- alleen de laatste 4 tekens. Deze website toont of accepteert nooit sleutels.',
        'admins_security_title': 'Hoe sleutels worden beschermd',
        'admins_setup_title': 'Instellen in 5 stappen',
        'admins_title': 'Voor serverbeheerders',
        'chain_1': '<strong>AI-providers</strong> met jouw sleutels - betere kwaliteit eerst, gratis sleutels vóór '
                   'betaalde sleutels',
        'chain_2': '<strong>Google Translate</strong>',
        'chain_3': '<strong>Azure Translator</strong>',
        'chain_4': '<strong>LibreTranslate</strong> op onze eigen server - altijd beschikbaar',
        'chain_5': '<strong>[Raw]</strong> - de originele tekst, als niets anders werkte',
        'faq_dm_a': 'Nee. YATB verwerkt alleen berichten in kanalen die de beheerders aan een Bridge hebben gekoppeld.',
        'faq_dm_q': 'Leest YATB mijn privéberichten of andere kanalen?',
        'faq_off_a': 'Berichten in gekoppelde kanalen worden altijd vertaald, zodat iedereen het gesprek kan volgen. '
                     'Met <em>Alleen lokaal</em> blijven ze op onze eigen server. Niet-gekoppelde kanalen worden nooit '
                     'aangeraakt.',
        'faq_off_q': 'Kan ik vertalingen volledig uitschakelen?',
        'faq_wrong_a': 'Bewerk je bericht - de vertaling wordt dan ook bijgewerkt. Als een term altijd verkeerd wordt '
                       'vertaald, laat het dan weten aan de beheerders van je server.',
        'faq_wrong_q': 'De vertaling is fout. Wat kan ik doen?',
        'feat_fallback_text': 'Zonder eigen sleutels vertaalt YATB met LibreTranslate op onze eigen server - gratis, '
                              'en niets verlaat de server.',
        'feat_fallback_title': 'Altijd een vertaling',
        'feat_format_text': "Vetgedrukte tekst, lijsten, citaten, spoilers, emoji's, vermeldingen en links blijven "
                            'intact. Echte code wordt onvertaald gelaten.',
        'feat_format_title': 'Behoudt Discord-opmaak',
        'feat_keys_text': 'Serverbeheerders voegen hun eigen API-sleutels toe in een privéformulier. Sleutels worden '
                          'versleuteld opgeslagen en nooit meer getoond. Limieten en budgetwaarschuwingen zijn '
                          'inbegrepen.',
        'feat_keys_title': 'Jouw sleutels, jouw budget',
        'feat_mirror_text': 'Antwoorden, bewerkingen, verwijderingen, reacties en threads worden gespiegeld naar alle '
                            'gekoppelde kanalen. Aankondigingen van gevolgde kanalen worden ook vertaald.',
        'feat_mirror_title': 'Spiegelt het gesprek',
        'feat_natural_text': 'AI-vertaling die het gesprek begrijpt: straattaal, game-termen en korte antwoorden komen '
                             'goed over. Als een dienst faalt, neemt de volgende het over.',
        'feat_natural_title': 'Natuurlijke vertalingen',
        'feat_privacy_text': 'Er worden geen berichtteksten opgeslagen. Elk lid kan kiezen dat hun berichten alleen op '
                             'onze eigen server worden vertaald.',
        'feat_privacy_title': 'Privacy by design',
        'footer_note': 'YATB is een privaat, niet-commercieel project en is niet gelieerd aan Discord.',
        'home_badge_langs': '7 talen',
        'home_badge_private': 'Privébot',
        'home_badge_storage': 'Geen berichtteksten opgeslagen',
        'home_example_note': 'Voorbeeld van een gekoppeld paar kanalen. Het label na de naam toont welke dienst de '
                             'vertaling heeft uitgevoerd.',
        'home_example_src': 'Anyone up for a raid tonight? Meet at 8 pm in <span class="mention">#voice</span> 🎮',
        'home_example_tgt': 'Heeft er iemand zin in een raid vanavond? We spreken om 20:00 uur af in <span '
                            'class="mention">#voice</span> 🎮',
        'home_example_tgt_channel': 'nederlands',
        'home_example_title': 'Voorbeeld',
        'home_features_title': 'Wat YATB doet',
        'home_how_title': 'Hoe het werkt',
        'home_lead': 'YATB - <em>Yet Another Translation Bot</em> - koppelt kanalen in verschillende talen. Iedereen '
                     'schrijft in zijn eigen taal, YATB plaatst de vertaling in de andere kanalen, onder de naam en '
                     'avatar van de auteur.',
        'home_private_text': 'Op dit moment niet. YATB is een privébot en draait alleen op geselecteerde servers. Als '
                             'YATB al op jouw server staat, bekijk dan de handleidingen <a href="members">voor '
                             'leden</a> en <a href="admins">voor beheerders</a>.',
        'home_private_title': 'Kan ik YATB aan mijn server toevoegen?',
        'home_support_text': 'YATB is gratis en bevat geen advertenties. Als je wilt helpen met de lopende kosten, kun '
                             'je het ondersteunen op Ko-fi.',
        'home_support_title': 'Ben je blij met YATB?',
        'home_title': 'Praat in verschillende talen op Discord',
        'how_1': '<strong>Beheerders koppelen kanalen</strong> - bijvoorbeeld <code>#english</code> en '
                 '<code>#deutsch</code> - in één Bridge.',
        'how_2': "<strong>Leden schrijven gewoon</strong> in hun eigen taal. Geen commando's nodig.",
        'how_3': '<strong>YATB plaatst de vertaling</strong> binnen enkele seconden in de andere kanalen.',
        'imprint_title': 'Colofon',
        'keys_kind_ai': 'AI-provider',
        'keys_kind_mt': 'Vertaalservice',
        'keys_lead': 'API-sleutels maken vertalingen beter dan de gratis LibreTranslate. Elke sleutel is van jou of je '
                     'server - YATB gebruikt deze alleen voor jouw server en slaat deze versleuteld op.',
        'keys_menu_note': 'Menunamen bij de aanbieders kunnen wijzigen. Status van de privacy-informatie: {date}.',
        'keys_open': 'Console openen',
        'keys_plan': 'Plan',
        'keys_privacy': 'Privacy',
        'keys_source': 'Privacy-informatie van de aanbieder',
        'keys_steps': 'Stappen',
        'keys_tips': '<ul><li>Stel naast het budget in YATB ook een <strong>bestedingslimiet</strong> in bij je '
                     'provideraccount.</li><li>Schakel waar mogelijk <strong>zero data retention</strong> in of '
                     'schakel training op jouw gegevens uit.</li><li>Voeg sleutels toe met <code>/yatb keys '
                     'add</code>: kies de provider en plak de sleutel in het privéformulier.</li></ul>',
        'keys_title': 'API-sleutels verkrijgen',
        'kofi': 'Steun YATB op Ko-fi',
        'lang_name': 'Nederlands',
        'legal_binding': 'Deze tekst is beschikbaar in verschillende talen. Bij verschillen tussen de versies is de '
                         'Duitse versie leidend.',
        'legal_updated': 'Laatst bijgewerkt: {date}',
        'members_choice_local': '<strong>Alleen lokaal</strong> - je berichten worden alleen vertaald door '
                                'LibreTranslate op onze eigen server en nooit verzonden naar AI-providers, Google of '
                                'Azure - zelfs niet als context voor de vertalingen van anderen. De kwaliteit is '
                                'lager.',
        'members_choice_note': 'De instelling is alleen voor jou zichtbaar en is van toepassing op elke server met '
                               'YATB. <code>/yatb-user help</code> toont een korte samenvatting in Discord.',
        'members_choice_standard': '<strong>Standaard</strong> - beste kwaliteit. Je berichten kunnen worden verzonden '
                                   'naar de services die de beheerders hebben toegevoegd.',
        'members_choice_title': 'Jouw keuze: <code>/yatb-user privacy</code>',
        'members_dashboard': 'Je kunt je keuze ook bekijken en aanpassen in de <a href="{url}">dashboard</a> (log in '
                             'met Discord).',
        'members_data': '<ul><li>YATB <strong>slaat geen berichtteksten op</strong>. Het onthoudt alleen welk bericht '
                        'bij welke vertaling hoort, gedurende {map_days} dagen, zodat bewerkingen en verwijderingen '
                        'kunnen worden gespiegeld.</li><li>Om te vertalen wordt je bericht verzonden naar de '
                        'vertaalservices die door de beheerders van je server zijn gekozen (zie <a '
                        'href="privacy">privacy</a>).</li><li>AI-providers ontvangen ook maximaal {context_lines} '
                        'eerdere berichten uit hetzelfde gesprek als context, zodat korte antwoorden correct worden '
                        'vertaald.</li></ul>',
        'members_data_title': 'Jouw gegevens',
        'members_faq_title': 'Vragen',
        'members_how': '<ul><li>Schrijf in je eigen taal in een gekoppeld kanaal. YATB plaatst een vertaling in de '
                       'andere gekoppelde kanalen, onder jouw naam en avatar.</li><li>Antwoorden, bewerkingen, '
                       'verwijderingen en threads worden gespiegeld. Reacties ook: ze verschijnen in de andere kanalen '
                       "als een reactie van YATB.</li><li>Opmaak, emoji's, vermeldingen en links blijven "
                       'behouden.</li><li>De vertaling verschijnt in de andere kanalen - mensen die jouw kanaal niet '
                       'kunnen zien, kunnen het daar alsnog lezen.</li></ul>',
        'members_how_title': 'Hoe het werkt',
        'members_lead': 'Sommige kanalen op jouw server zijn gekoppeld door YATB. Dit is wat dat voor jou betekent.',
        'members_tags_intro': 'Elke vertaling toont welke service deze heeft gemaakt:',
        'members_tags_title': 'De tag achter de naam',
        'members_title': 'Voor leden',
        'nav_admins': 'Voor beheerders',
        'nav_dashboard': 'Dashboard',
        'nav_home': 'Home',
        'nav_imprint': 'Colofon',
        'nav_keys': 'API-sleutels',
        'nav_language': 'Taal',
        'nav_members': 'Voor leden',
        'nav_menu': 'Menu',
        'nav_more': 'Meer projecten van Gladi',
        'nav_privacy': 'Privacy',
        'nav_terms': 'Voorwaarden',
        'not_found_text': 'Deze pagina bestaat niet. Ga naar de <a href="/">homepagina</a>.',
        'not_found_title': 'Pagina niet gevonden',
        'pd_backup_how_long': '14 dagen op de server, 30 dagen in Oracle Object Storage (Frankfurt)',
        'pd_backup_what': 'Versleutelde back-ups van bovenstaande gegevens (nooit berichtteksten)',
        'pd_backup_why': 'Herstel na fouten',
        'pd_choice_how_long': 'Totdat je om verwijdering vraagt',
        'pd_choice_what': 'Je gebruikers-ID en je privacykeuze',
        'pd_choice_why': 'Het respecteren van <code>/yatb-user privacy</code> op elke server',
        'pd_config_how_long': 'Totdat deze worden verwijderd, <code>/yatb reset</code> of <code>/yatb uninstall</code>',
        'pd_config_what': 'Serverinstellingen: Bridges, logkanaal, versleutelde API-sleutels, ID van de beheerder die '
                          'een sleutel heeft toegevoegd',
        'pd_config_why': 'Het draaien van de bot op de server',
        'pd_map_how_long': '{map_days} dagen',
        'pd_map_what': "Bericht-ID's en een checksum van de tekst",
        'pd_map_why': 'Het spiegelen van antwoorden, bewerkingen en verwijderingen naar de vertalingen',
        'pd_stats_how_long': '{raw_days} dagen, daarna alleen dagtotalen per server',
        'pd_stats_what': 'Gebruiksstatistieken: server, dienst, talen, aantal tekens, duur, resultaat - geen tekst, '
                         "geen gebruikers-ID's",
        'pd_stats_why': 'Limieten, kosten, betrouwbaarheid van de diensten',
        'pd_text_how_long': 'Niet opgeslagen. Alleen in het geheugen gehouden tijdens het vertalen; de context van '
                            'recente berichten gaat bij elke herstart verloren.',
        'pd_text_what': 'Berichttekst en weergavenaam',
        'pd_text_why': 'Vertaling; wordt naar de vertaalservices van de server gestuurd (zie 4). AI-aanbieders krijgen '
                       'tot {context_lines} van jouw eigen eerdere berichten in dezelfde Bridge als context – nooit '
                       'berichten van anderen.',
        'privacy_basis': 'Art. 6 lid 1 sub f AVG - ons gerechtvaardigd belang, en het belang van de '
                         'servergemeenschappen, bij meertalige communicatie en bij een veilige, betrouwbare dienst. '
                         'Jouw keuze voor <em>Alleen lokaal</em> beperkt de verwerking tot onze eigen server.',
        'privacy_basis_title': '6. Rechtsgrondslag',
        'privacy_bot_intro': 'YATB verwerkt alleen berichten in kanalen die door de beheerders van een server zijn '
                             'gekoppeld aan een Bridge.',
        'privacy_bot_title': '3. De Discord-bot',
        'privacy_col_how_long': 'Bewaard voor',
        'privacy_col_note': 'Wat de aanbieder zegt',
        'privacy_col_service': 'Dienst',
        'privacy_col_what': 'Gegevens',
        'privacy_col_why': 'Doel',
        'privacy_controller_missing': 'Contactgegevens van de beheerder worden hier toegevoegd.',
        'privacy_controller_title': '1. Wie is verantwoordelijk',
        'privacy_dash': '<ul><li>Op <code>/app</code> kun je inloggen met Discord. YATB ontvangt alleen je '
                        'Discord-gebruikers-ID en naam (scope <code>identify</code>). Het toegangstoken van Discord '
                        'wordt direct na het inloggen ingetrokken en nooit opgeslagen.</li><li>Een sessiecookie '
                        '(<code>yatb_session</code>, 7 dagen geldig) houdt je ingelogd; tijdens het inloggen beschermt '
                        'een tweede cookie tegen vervalste logins gedurende maximaal 10 minuten. Beide zijn technisch '
                        'noodzakelijk en worden nergens anders voor gebruikt.</li><li>Opgeslagen op onze server: een '
                        'hash van het sessietoken, je Discord-ID, weergavenaam, taal en de vervaldatum - verwijderd '
                        'wanneer je uitlogt of na 7 dagen.</li><li>Of je een server mag beheren, wordt bij elk verzoek '
                        'door de bot direct gecontroleerd bij Discord. Wijzigingen die je aanbrengt, worden met je '
                        'naam gerapporteerd in het logkanaal van die server.</li></ul>',
        'privacy_dash_title': 'Dashboard (inloggen met Discord)',
        'privacy_discord': 'Berichten worden geschreven en getoond op Discord. Discord verwerkt deze onder zijn eigen '
                           '<a href="https://discord.com/privacy" rel="noopener">privacybeleid</a>.',
        'privacy_discord_title': '5. Discord',
        'privacy_lead': 'Deze pagina legt uit welke gegevens de YATB-website en de YATB Discord-bot verwerken, waarom '
                        'en hoe lang.',
        'privacy_rights': 'Je hebt het recht op inzage, rectificatie, wissing, beperking van de verwerking, '
                          'overdraagbaarheid van gegevens en om bezwaar te maken, en je kunt een klacht indienen bij '
                          'een toezichthoudende autoriteit voor gegevensbescherming. Om je rechten uit te oefenen, '
                          'neem je contact op met de beheerder (sectie 1). In Discord kun je met <code>/yatb-user '
                          'privacy</code> op elk gewenst moment kiezen voor <em>Alleen lokaal</em>.',
        'privacy_rights_title': '7. Jouw rechten',
        'privacy_services_intro': 'De beheerders van elke server bepalen welke diensten hun berichten vertalen. '
                                  'Berichten van leden met <em>Alleen lokaal</em> worden alleen vertaald door '
                                  'LibreTranslate op onze eigen server. Op servers die door de beheerder worden '
                                  'beheerd, worden de eigen betaalde accounts van de beheerder gebruikt.',
        'privacy_services_title': '4. Vertaaldiensten',
        'privacy_title': 'Privacybeleid',
        'privacy_web': "<ul><li>De informatiepagina's gebruiken geen cookies, geen tracking, geen analytics en geen "
                       "externe lettertypes of scripts.</li><li>Om de pagina's te leveren, worden het IP-adres en het "
                       'verzoek van je browser kortstondig verwerkt door de webserver. De webserver houdt geen '
                       'toegangslogs bij.</li><li>De website draait op een server van Oracle Cloud in Frankfurt '
                       "(Duitsland). HTTPS-certificaten zijn afkomstig van Let's Encrypt; hiervoor worden geen "
                       'bezoekersgegevens gedeeld.</li><li>Links naar andere sites (Discord, Ko-fi, aanbieders) zijn '
                       'normale links - daarop is hun privacybeleid van toepassing.</li></ul>',
        'privacy_web_title': '2. Deze website',
        'prov_azure': 'Vertaaltekst slaat de tekst niet op ("no trace"). YATB gebruikt het wereldwijde eindpunt, dus '
                      'verzoeken kunnen in elk Microsoft-datacenter worden verwerkt, meestal het dichtstbijzijnde.',
        'prov_gemini': 'Alleen sleutels met facturering ingeschakeld - de gratis laag mag niet worden gebruikt voor '
                       'gebruikers in de EER, het VK of Zwitserland. Betaalde laag: Google gebruikt de inhoud niet om '
                       'zijn producten te verbeteren; prompts worden voor een beperkte tijd gelogd om misbruik op te '
                       'sporen. Wordt wereldwijd door Google verwerkt.',
        'prov_google_translate': 'De tekst wordt alleen in het geheugen gehouden voor de vertaling en wordt niet '
                                 'gebruikt om de vertaling van Google te trainen of te verbeteren. Wordt wereldwijd '
                                 'door Google verwerkt.',
        'prov_groq': 'Standaard bewaart Groq geen inferentiegegevens; logs voor probleemoplossing of misbruik worden '
                     'tot 30 dagen bewaard. Geen gegevensretentie kan voor iedereen worden ingeschakeld onder '
                     '<strong>Data Controls</strong>. Gegevens worden opgeslagen in de VS.',
        'prov_libre': 'Draait op onze eigen server in Frankfurt (Duitsland). Er wordt niets naar derden verzonden.',
        'prov_mistral': 'Mistral AI (Frankrijk). Geen training op jouw inhoud - behalve waar een productinstelling dit '
                        'toestaat: schakel in de Mistral-console onder <strong>Privacy</strong> het gebruik van '
                        'API-gegevens voor verbetering uit. Het gratis plan kan gegevens gebruiken voor training, '
                        'tenzij je je afmeldt. Een DPA is beschikbaar, geen gegevensretentie op verzoek.',
        'prov_novita': 'Volgens de voorwaarden: standaard geen gegevensretentie en geen training op jouw inhoud. '
                       'Gebruiksmetadata worden tot 2 jaar bewaard; gegevens kunnen in de VS worden verwerkt (SCC). '
                       'Een DPA is alleen beschikbaar voor zakelijke klanten. Onderworpen aan de wetgeving van '
                       'Delaware, VS.',
        'setup_1': '<strong>Controleer machtigingen.</strong> In elk gekoppeld kanaal heeft YATB het volgende nodig: '
                   '{perms}.',
        'setup_2': '<strong>Koppel kanalen.</strong> Kanalen met dezelfde Bridge-naam worden naar elkaar '
                   'vertaald:<br><code>/yatb bridge add chat #english English</code><br><code>/yatb bridge add chat '
                   '#deutsch German</code><br>Forum- en mediakanalen werken op dezelfde manier - altijd forum met '
                   'forum. YATB maakt zelf ontbrekende tags aan als het <em>Kanalen beheren</em>-rechten heeft in het '
                   'forum.',
        'setup_3': '<strong>Voeg API-sleutels toe (optioneel).</strong> Zonder sleutels gebruikt YATB LibreTranslate. '
                   'Voor een betere kwaliteit voeg je sleutels toe met <code>/yatb keys add</code> - zie <a '
                   'href="keys">API-sleutels</a>.',
        'setup_4': '<strong>Stel een logkanaal in.</strong> <code>/yatb log set</code> - YATB rapporteert hier '
                   'waarschuwingen over het gebruik, problemen met sleutels en wijzigingen.',
        'setup_5': '<strong>Informeer je leden.</strong> Link naar de <a href="members">handleiding voor leden</a> of '
                   'voeg een korte regel toe, bijvoorbeeld:',
        'setup_check': '<code>/yatb status</code> toont de vertaalketen van je server en de status van elke dienst.',
        'setup_rule': 'Vertaling (YATB): In gekoppelde kanalen vertaalt de bot YATB berichten automatisch en plaatst '
                      'deze opnieuw onder jouw naam. Hiervoor kunnen ze worden verzonden naar externe diensten (bijv. '
                      'AI-providers, Google). Berichtteksten worden niet opgeslagen. Alleen lokaal vertalen: '
                      '/yatb-user privacy',
        'site_desc': 'YATB koppelt Discord-kanalen in verschillende talen en vertaalt elk bericht - onder de naam van '
                     'de auteur.',
        'tag_ai': 'AI-provider (bijvoorbeeld Mistral of Google Gemini) - meestal de beste kwaliteit',
        'tag_azure': 'Azure Translator (Microsoft)',
        'tag_google': 'Google Translate',
        'tag_libre': 'LibreTranslate - draait op onze eigen server',
        'tag_raw': 'Niet vertaald - er was op dat moment geen service beschikbaar',
        'terms_1': 'YATB is een privaat, niet-commercieel project. Het is gratis, draait momenteel alleen op '
                   'geselecteerde servers en wordt geleverd zonder enige garantie op beschikbaarheid. Functies kunnen '
                   'op elk moment veranderen of beëindigd worden.',
        'terms_1_title': '1. De dienst',
        'terms_2': 'Vertalingen worden door machines gemaakt en kunnen onjuist of onvolledig zijn. Vertrouw er niet op '
                   'voor belangrijke, juridische, medische of financiële zaken.',
        'terms_2_title': '2. Vertalingen',
        'terms_3': '<ul><li>Jij bent verantwoordelijk voor de API-sleutels die je toevoegt, voor de voorwaarden van '
                   'hun aanbieders en voor de kosten. De gebruikstelling van YATB is een schatting - stel '
                   'bestedingslimieten in bij de aanbieder.</li><li>Informeer je leden dat berichten in gekoppelde '
                   'kanalen (Bridge) worden vertaald en naar externe diensten kunnen worden verzonden.</li><li>Gebruik '
                   'YATB alleen in overeenstemming met de wet en de Discord-voorwaarden - geen spam, geen '
                   'misbruik.</li></ul>',
        'terms_3_title': '3. Serverbeheerders',
        'terms_4': "YATB wordt gratis en 'as is' aangeboden. Aansprakelijkheid is beperkt tot opzet en grove "
                   'nalatigheid, voor zover de wet dit toestaat.',
        'terms_4_title': '4. Aansprakelijkheid',
        'terms_5': 'Donaties (bijvoorbeeld via Ko-fi) zijn vrijwillig en creëren geen recht op functies, ondersteuning '
                   'of beschikbaarheid.',
        'terms_5_title': '5. Donaties',
        'terms_6': 'Het Duitse recht is van toepassing.',
        'terms_6_title': '6. Slotbepalingen',
        'terms_lead': 'Kort en simpel: YATB is een gratis hobbyproject. Door YATB op een server te gebruiken, ga je '
                      'akkoord met deze voorwaarden.',
        'terms_title': 'Gebruiksvoorwaarden'},
 'ru': {'admins_chain_intro': 'Для каждого сообщения YATB пробует сервисы в этом порядке и выбирает первый успешный '
                              'результат:',
        'admins_chain_note': 'Каждый ответ проверяется (упоминания, ссылки, форматирование). Плохой ответ, ошибка или '
                             'исчерпанный лимит переводят запрос к следующему сервису; неработающий сервис временно '
                             'пропускается. Участники с настройкой <em>Только локально</em> всегда получают '
                             'LibreTranslate.',
        'admins_chain_title': 'Цепочка перевода',
        'admins_col_command': 'Команда',
        'admins_col_desc': 'Описание',
        'admins_commands_title': 'Все команды',
        'admins_dashboard': '<p>В <a href="{url}">панели управления</a> ты входишь через Discord и видишь все серверы '
                            'с YATB, где ты администратор.</p><ul><li>Использование по API-ключу: сегодня и за этот '
                            'месяц, в сравнении с бесплатными лимитами или твоим бюджетом — данные обновляются '
                            'автоматически.</li><li>Меняй метку, план, бюджет и лимит ключа или удаляй его. Сам ключ '
                            'никогда не показывается и не вводится на сайте — добавление ключа остаётся формой в '
                            'Discord.</li><li>Меняй порядок цепочки переводчиков.</li><li>Статистика за 7, 30 и 90 '
                            'дней: вызовы, успешность и объём по каждой службе.</li><li>Все изменения отображаются в '
                            'канале лога сервера с твоим именем.</li></ul>',
        'admins_dashboard_title': 'Панель управления',
        'admins_forum': '<ul><li>Связывай форумы как текстовые каналы, например, <code>/yatb bridge add forum '
                        '#forum-en English</code>. Bridge содержит либо форумы, либо текстовые каналы, но никогда не и '
                        'то, и другое вместе. Медиаканалы работают аналогично.</li><li>Новая публикация появляется во '
                        'всех остальных форумах в составе Bridge — с переведенным заголовком и текстом, '
                        'соответствующими тегами и от имени автора. Ответы, правки, удаления и реакции внутри '
                        'публикации синхронизируются.</li><li>Переименование, изменение тегов, закрытие или блокировка '
                        'исходной публикации применяются к копиям.</li><li>Теги сопоставляются 1:1. YATB создает '
                        'недостающие теги самостоятельно (переведенное название, тот же эмодзи), если у него есть '
                        'разрешение <em>Управление каналами</em> — в противном случае сопоставляются только теги с '
                        'одинаковыми названиями. Discord позволяет использовать до 20 тегов на форум.</li></ul>',
        'admins_forum_perms': '<p>Где предоставить разрешение <em>Управление каналами</em>:</p><ul><li><strong>На '
                              'категории форумов</strong> (рекомендуется): охватывает все форумы в ней, включая новые, '
                              'при этом остальная часть сервера остается защищенной.</li><li><strong>На каждом '
                              'форуме</strong>: самый узкий вариант, но для каждого нового форума разрешение нужно '
                              'выдавать заново.</li><li><strong>На уровне сервера</strong> (роль бота или '
                              'ссылка-приглашение): самый удобный вариант, но бот сможет редактировать или удалять '
                              'любой канал — если его токен будет украден, ущерб будет значительно больше.</li></ul>',
        'admins_forum_title': 'Форумы и медиаканалы',
        'admins_lead': 'YATB — это приватный бот. Если он есть на твоем сервере, вот как его настроить. Все команды '
                       'находятся в <code>/yatb</code> и видны только администраторам.',
        'admins_limits': '<ul><li><strong>Бесплатные ключи:</strong> YATB учитывает использование в пределах '
                         'бесплатных лимитов провайдера в минуту, день и месяц.</li><li><strong>Платные '
                         'ключи:</strong> ты устанавливаешь ежемесячный бюджет в долларах США или евро. YATB оценивает '
                         'стоимость по прайс-листам — также задай лимит расходов у провайдера.</li><li>Ежедневные '
                         'лимиты сбрасываются в 00:00 UTC, ежемесячные — 1-го числа в 00:00 '
                         'UTC.</li><li>Предупреждения на 90, 95 и 100 % отправляются в канал лога. Когда ключ '
                         'заканчивается, подключается следующая служба.</li><li>Если один и тот же ключ используется '
                         'на нескольких серверах, использование суммируется. Другие серверы никогда не '
                         'упоминаются.</li><li><code>/yatb keys list</code> и панель управления показывают '
                         'использование по ключу, <code>/yatb keys edit</code> меняет план, бюджет и лимит.</li></ul>',
        'admins_limits_title': 'Использование, лимиты и бюджет',
        'admins_remove': '<code>/yatb reset</code> удаляет все Bridge, ключи и настройки твоего сервера. <code>/yatb '
                         'uninstall</code> удаляет все данные твоего сервера, и бот покидает его.',
        'admins_remove_title': 'Удаление YATB',
        'admins_security': 'Ключи вводятся в приватной форме Discord, а не в качестве аргумента команды. Они хранятся '
                           'в зашифрованном виде (AES-256-GCM, отдельно для каждого сервера) и никогда не отображаются '
                           'снова — только последние 4 символа. Этот сайт никогда не показывает и не принимает ключи.',
        'admins_security_title': 'Как защищены ключи',
        'admins_setup_title': 'Настройка в 5 шагов',
        'admins_title': 'Для администраторов сервера',
        'chain_1': '<strong>ИИ-провайдеры</strong> с твоими ключами — сначала группа с лучшим качеством, бесплатные '
                   'ключи перед платными',
        'chain_2': '<strong>Google Translate</strong>',
        'chain_3': '<strong>Azure Translator</strong>',
        'chain_4': '<strong>LibreTranslate</strong> на нашем сервере — доступен всегда',
        'chain_5': '<strong>[Raw]</strong> — исходный текст, если ничего другое не сработало',
        'faq_dm_a': 'Нет. YATB обрабатывает сообщения только в тех каналах, которые администраторы добавили в Bridge.',
        'faq_dm_q': 'Читает ли YATB мои личные сообщения или другие каналы?',
        'faq_off_a': 'Сообщения в каналах, объединенных в Bridge, переводятся всегда, чтобы все могли следить за ходом '
                     'беседы. При выборе <em>Только локально</em> они остаются на нашем собственном сервере. Каналы, '
                     'не входящие в Bridge, не затрагиваются.',
        'faq_off_q': 'Можно ли полностью отключить перевод?',
        'faq_wrong_a': 'Отредактируй свое сообщение — перевод также обновится. Если какой-то термин постоянно '
                       'переводится неправильно, сообщи об этом администраторам своего сервера.',
        'faq_wrong_q': 'Перевод неверный. Что делать?',
        'feat_fallback_text': 'Даже без ключей YATB переводит через LibreTranslate на нашем сервере — бесплатно, и '
                              'данные не покидают сервер.',
        'feat_fallback_title': 'Перевод всегда доступен',
        'feat_format_text': 'Жирный шрифт, списки, цитаты, спойлеры, эмодзи, упоминания и ссылки остаются без '
                            'изменений. Настоящий код не переводится.',
        'feat_format_title': 'Сохранение форматирования Discord',
        'feat_keys_text': 'Администраторы сервера добавляют свои API-ключи через приватную форму. Ключи хранятся в '
                          'зашифрованном виде и больше никогда не отображаются. Предусмотрены лимиты и уведомления о '
                          'бюджете.',
        'feat_keys_title': 'Твои ключи, твой бюджет',
        'feat_mirror_text': 'Ответы, правки, удаления, реакции и ветки дублируются во все связанные каналы. Объявления '
                            'из отслеживаемых каналов также переводятся.',
        'feat_mirror_title': 'Зеркальное отображение беседы',
        'feat_natural_text': 'ИИ-перевод, который понимает контекст беседы: сленг, игровые термины и короткие ответы '
                             'звучат правильно. Если один сервис дает сбой, его заменяет следующий.',
        'feat_natural_title': 'Естественный перевод',
        'feat_privacy_text': 'Тексты сообщений не сохраняются. Каждый участник может выбрать, чтобы его сообщения '
                             'переводились только на нашем сервере.',
        'feat_privacy_title': 'Конфиденциальность по умолчанию',
        'footer_note': 'YATB — это частный некоммерческий проект, не связанный с Discord.',
        'home_badge_langs': '7 языков',
        'home_badge_private': 'Приватный бот',
        'home_badge_storage': 'Тексты сообщений не сохраняются',
        'home_example_note': 'Пример связанной пары каналов. Тег после имени показывает, какой сервис выполнил '
                             'перевод.',
        'home_example_src': 'Anyone up for a raid tonight? Meet at 8 pm in <span class="mention">#voice</span> 🎮',
        'home_example_tgt': 'Кто готов к рейду сегодня вечером? Встречаемся в 20:00 в <span '
                            'class="mention">#voice</span> 🎮',
        'home_example_tgt_channel': 'русский',
        'home_example_title': 'Пример',
        'home_features_title': 'Что делает YATB',
        'home_how_title': 'Как это работает',
        'home_lead': 'YATB — <em>Yet Another Translation Bot</em> — связывает каналы на разных языках. Каждый пишет на '
                     'своем языке, а YATB публикует перевод в других каналах под именем и аватаром автора.',
        'home_private_text': 'На данный момент нет. YATB — это приватный бот, который работает только на выбранных '
                             'серверах. Если YATB уже есть на твоем сервере, ознакомься с руководствами <a '
                             'href="members">для участников</a> и <a href="admins">для администраторов</a>.',
        'home_private_title': 'Могу ли я добавить YATB на свой сервер?',
        'home_support_text': 'YATB бесплатен и не содержит рекламы. Если хочешь помочь с оплатой расходов на '
                             'содержание, можешь поддержать проект на Ko-fi.',
        'home_support_title': 'Нравится YATB?',
        'home_title': 'Общайся на разных языках в Discord',
        'how_1': '<strong>Администраторы связывают каналы</strong> — например, <code>#english</code> и '
                 '<code>#deutsch</code> — в один Bridge.',
        'how_2': '<strong>Участники просто пишут</strong> на своем языке. Никаких команд не требуется.',
        'how_3': '<strong>YATB публикует перевод</strong> в других каналах за несколько секунд.',
        'imprint_title': 'Выходные данные',
        'keys_kind_ai': 'ИИ-провайдер',
        'keys_kind_mt': 'Сервис перевода',
        'keys_lead': 'API-ключи делают перевод лучше, чем бесплатный LibreTranslate. Каждый ключ принадлежит тебе или '
                     'твоему серверу — YATB использует его только для твоего сервера и хранит в зашифрованном виде.',
        'keys_menu_note': 'Названия меню у провайдеров могут меняться. Статус информации о конфиденциальности: {date}.',
        'keys_open': 'Открыть консоль',
        'keys_plan': 'План',
        'keys_privacy': 'Конфиденциальность',
        'keys_source': 'Информация о конфиденциальности провайдера',
        'keys_steps': 'Шаги',
        'keys_tips': '<ul><li>Установи <strong>лимит расходов</strong> в аккаунте провайдера в дополнение к бюджету в '
                     'YATB.</li><li>Где возможно, включи <strong>отказ от хранения данных</strong> или отключи '
                     'обучение на твоих данных.</li><li>Добавляй ключи через <code>/yatb keys add</code>: выбери '
                     'провайдера, затем вставь ключ в приватную форму.</li></ul>',
        'keys_title': 'Получение API-ключей',
        'kofi': 'Поддержи YATB на Ko-fi',
        'lang_name': 'Русский',
        'legal_binding': 'Этот текст доступен на нескольких языках. В случае расхождений преимущественную силу имеет '
                         'немецкая версия.',
        'legal_updated': 'Последнее обновление: {date}',
        'members_choice_local': '<strong>Только локально</strong> — твои сообщения переводятся только через '
                                'LibreTranslate на нашем собственном сервере и никогда не отправляются провайдерам ИИ, '
                                'Google или Azure — даже в качестве контекста для переводов других людей. Качество '
                                'ниже.',
        'members_choice_note': 'Эта настройка видна только тебе и применяется на каждом сервере с YATB. '
                               '<code>/yatb-user help</code> показывает краткую справку в Discord.',
        'members_choice_standard': '<strong>Стандартный</strong> — лучшее качество. Твои сообщения могут отправляться '
                                   'в сервисы, добавленные администраторами.',
        'members_choice_title': 'Твой выбор: <code>/yatb-user privacy</code>',
        'members_dashboard': 'Ты можешь проверить и изменить свой выбор в <a href="{url}">панели управления</a> (войди '
                             'через Discord).',
        'members_data': '<ul><li>YATB <strong>не хранит тексты сообщений</strong>. Бот лишь запоминает, какое '
                        'сообщение к какому переводу относится, в течение {map_days} дней, чтобы изменения и удаления '
                        'могли синхронизироваться.</li><li>Для перевода твое сообщение отправляется в сервисы '
                        'перевода, выбранные администраторами твоего сервера (см. <a '
                        'href="privacy">конфиденциальность</a>).</li><li>Провайдеры ИИ также получают до '
                        '{context_lines} предыдущих сообщений из того же диалога в качестве контекста, чтобы короткие '
                        'ответы переводились корректно.</li></ul>',
        'members_data_title': 'Твои данные',
        'members_faq_title': 'Вопросы',
        'members_how': '<ul><li>Пиши на своем языке в связанном канале. YATB опубликует перевод в других связанных '
                       'каналах от твоего имени и с твоим аватаром.</li><li>Ответы, правки, удаления и ветки сообщений '
                       'дублируются. Реакции тоже: они появляются в других каналах как реакции от '
                       'YATB.</li><li>Форматирование, эмодзи, упоминания и ссылки сохраняются.</li><li>Перевод '
                       'появляется в других каналах — люди, которые не видят твой канал, все равно смогут прочитать '
                       'его там.</li></ul>',
        'members_how_title': 'Как это работает',
        'members_lead': 'Некоторые каналы на твоем сервере связаны с помощью YATB. Вот что это значит для тебя.',
        'members_tags_intro': 'Каждый перевод показывает, какой сервис его выполнил:',
        'members_tags_title': 'Тег после имени',
        'members_title': 'Для участников',
        'nav_admins': 'Для администраторов',
        'nav_dashboard': 'Панель управления',
        'nav_home': 'Главная',
        'nav_imprint': 'Выходные данные',
        'nav_keys': 'API-ключи',
        'nav_language': 'Язык',
        'nav_members': 'Для участников',
        'nav_menu': 'Меню',
        'nav_more': 'Другие проекты от Gladi',
        'nav_privacy': 'Конфиденциальность',
        'nav_terms': 'Условия',
        'not_found_text': 'Эта страница не существует. Перейди на <a href="/">главную страницу</a>.',
        'not_found_title': 'Страница не найдена',
        'pd_backup_how_long': '14 дней на сервере, 30 дней в Oracle Object Storage (Франкфурт)',
        'pd_backup_what': 'Зашифрованные резервные копии указанных выше данных (тексты сообщений не сохраняются)',
        'pd_backup_why': 'Восстановление после ошибок',
        'pd_choice_how_long': 'До тех пор, пока ты не запросишь удаление',
        'pd_choice_what': 'Твой ID пользователя и выбранный уровень приватности',
        'pd_choice_why': 'Соблюдение настроек <code>/yatb-user privacy</code> на каждом сервере',
        'pd_config_how_long': 'До удаления, выполнения <code>/yatb reset</code> или <code>/yatb uninstall</code>',
        'pd_config_what': 'Настройки сервера: Bridge, канал логов, зашифрованные API-ключи, ID администратора, '
                          'добавившего ключ',
        'pd_config_why': 'Работа бота на сервере',
        'pd_map_how_long': '{map_days} дней',
        'pd_map_what': 'ID сообщений и контрольная сумма текста',
        'pd_map_why': 'Отражение ответов, правок и удалений в переводах',
        'pd_stats_how_long': '{raw_days} дней, после чего остаются только ежедневные итоги по серверу',
        'pd_stats_what': 'Статистика использования: сервер, сервис, языки, количество символов, длительность, '
                         'результат — без текста и ID пользователей',
        'pd_stats_why': 'Лимиты, расходы, надежность сервисов',
        'pd_text_how_long': 'Не сохраняется. Хранится в памяти только во время перевода; контекст недавних сообщений '
                            'теряется при каждом перезапуске.',
        'pd_text_what': 'Текст сообщения и отображаемое имя',
        'pd_text_why': 'Перевод; отправляется на серверные переводческие службы (см. п. 4). Провайдеры ИИ также '
                       'получают до {context_lines} твоих предыдущих сообщений в том же Bridge в качестве контекста — '
                       'никогда чужие сообщения.',
        'privacy_basis': 'Ст. 6(1)(f) GDPR — наш законный интерес, а также интерес серверных сообществ в многоязычном '
                         'общении и в безопасном, надежном сервисе. Твой выбор <em>Только локально</em> ограничивает '
                         'обработку нашим собственным сервером.',
        'privacy_basis_title': '6. Правовое основание',
        'privacy_bot_intro': 'YATB обрабатывает сообщения только в тех каналах, которые администраторы сервера '
                             'привязали к Bridge.',
        'privacy_bot_title': '3. Discord-бот',
        'privacy_col_how_long': 'Срок хранения',
        'privacy_col_note': 'Что говорит провайдер',
        'privacy_col_service': 'Сервис',
        'privacy_col_what': 'Данные',
        'privacy_col_why': 'Цель',
        'privacy_controller_missing': 'Контактные данные оператора будут добавлены здесь.',
        'privacy_controller_title': '1. Кто несет ответственность',
        'privacy_dash': '<ul><li>По адресу <code>/app</code> ты можешь войти через Discord. YATB получает только твой '
                        'ID пользователя Discord и имя (область <code>identify</code>). Токен доступа Discord '
                        'отзывается сразу после входа и никогда не сохраняется.</li><li>Сессионный файл cookie '
                        '(<code>yatb_session</code>, действителен 7 дней) поддерживает твой вход; во время входа '
                        'второй файл cookie защищает от поддельных входов максимум на 10 минут. Оба технически '
                        'необходимы и не используются ни для чего другого.</li><li>Хранится на нашем сервере: хеш '
                        'сессионного токена, твой ID Discord, отображаемое имя, язык и дата истечения срока действия — '
                        'удаляются при выходе из системы или через 7 дней.</li><li>Право на управление сервером '
                        'проверяется ботом напрямую через Discord при каждом запросе. Внесенные тобой изменения '
                        'фиксируются в лог-канале этого сервера с указанием твоего имени.</li></ul>',
        'privacy_dash_title': 'Панель управления (вход через Discord)',
        'privacy_discord': 'Сообщения пишутся и отображаются в Discord. Discord обрабатывает их в соответствии со '
                           'своей собственной <a href="https://discord.com/privacy" rel="noopener">политикой '
                           'конфиденциальности</a>.',
        'privacy_discord_title': '5. Discord',
        'privacy_lead': 'На этой странице объясняется, какие данные обрабатывают веб-сайт YATB и Discord-бот YATB, '
                        'зачем и как долго.',
        'privacy_rights': 'Ты имеешь право на доступ, исправление, удаление, ограничение обработки, переносимость '
                          'данных и возражение, а также можешь подать жалобу в надзорный орган по защите данных. Чтобы '
                          'воспользоваться своими правами, свяжись с оператором (раздел 1). В Discord команда '
                          '<code>/yatb-user privacy</code> позволяет тебе в любое время выбрать <em>Только '
                          'локально</em>.',
        'privacy_rights_title': '7. Твои права',
        'privacy_services_intro': 'Администраторы каждого сервера решают, какие службы будут переводить их сообщения. '
                                  'Сообщения участников с настройкой <em>Только локально</em> переводятся только через '
                                  'LibreTranslate на нашем собственном сервере. На серверах, управляемых оператором, '
                                  'используются его собственные платные аккаунты.',
        'privacy_services_title': '4. Службы перевода',
        'privacy_title': 'Политика конфиденциальности',
        'privacy_web': '<ul><li>Информационные страницы не используют файлы cookie, отслеживание, аналитику, а также '
                       'внешние шрифты или скрипты.</li><li>Для доставки страниц IP-адрес твоего браузера и запрос '
                       'кратковременно обрабатываются веб-сервером. Веб-сервер не ведет логи доступа.</li><li>Сайт '
                       'работает на сервере Oracle Cloud во Франкфурте (Германия). HTTPS-сертификаты предоставлены '
                       "Let's Encrypt; данные посетителей для этого не передаются.</li><li>Ссылки на другие сайты "
                       '(Discord, Ko-fi, провайдеры) являются обычными ссылками — там действуют их политики '
                       'конфиденциальности.</li></ul>',
        'privacy_web_title': '2. Этот веб-сайт',
        'prov_azure': 'Перевод текста не сохраняет сам текст («no trace»). YATB использует глобальную конечную точку, '
                      'поэтому запросы могут обрабатываться в любом центре обработки данных Microsoft, обычно в '
                      'ближайшем.',
        'prov_gemini': 'Только ключи с включенным биллингом — бесплатный уровень может быть недоступен для '
                       'пользователей в ЕЭЗ, Великобритании или Швейцарии. Платный уровень: Google не использует '
                       'контент для улучшения своих продуктов; запросы логируются в течение ограниченного времени для '
                       'обнаружения злоупотреблений. Обрабатывается Google по всему миру.',
        'prov_google_translate': 'Текст удерживается в памяти только для перевода и не используется для обучения или '
                                 'улучшения перевода Google. Обрабатывается Google по всему миру.',
        'prov_groq': 'По умолчанию Groq не хранит данные инференса; логи для устранения неполадок или выявления '
                     'злоупотреблений хранятся до 30 дней. Нулевое хранение данных можно включить для всех в разделе '
                     '<strong>Data Controls</strong>. Данные хранятся в США.',
        'prov_libre': 'Работает на нашем собственном сервере во Франкфурте (Германия). Ничего не отправляется третьим '
                      'лицам.',
        'prov_mistral': 'Mistral AI (Франция). Обучение на твоем контенте не проводится, за исключением случаев, когда '
                        'это разрешено настройками продукта: в консоли Mistral в разделе <strong>Privacy</strong> '
                        'отключи использование данных API для улучшения. Бесплатный план может использовать данные для '
                        'обучения, если ты не откажешься от этого. Доступно DPA, нулевое хранение данных по запросу.',
        'prov_novita': 'Согласно условиям: нулевое хранение данных и отсутствие обучения на твоем контенте по '
                       'умолчанию. Метаданные использования хранятся до 2 лет; данные могут обрабатываться в США '
                       '(SCC). DPA доступно только для корпоративных клиентов. Регулируется законодательством штата '
                       'Делавэр, США.',
        'setup_1': '<strong>Проверь права доступа.</strong> В каждом канале Bridge боту YATB нужны: {perms}.',
        'setup_2': '<strong>Связывай каналы.</strong> Каналы с одинаковым названием Bridge переводятся друг в '
                   'друга:<br><code>/yatb bridge add chat #english English</code><br><code>/yatb bridge add chat '
                   '#deutsch German</code><br>Форумные и медиаканалы работают так же — всегда форум с форумом. YATB '
                   'сам создает недостающие теги, если у него есть право <em>Управление каналами</em> на форуме.',
        'setup_3': '<strong>Добавь API-ключи (необязательно).</strong> Без ключей YATB использует LibreTranslate. Для '
                   'лучшего качества добавь ключи через <code>/yatb keys add</code> — см. <a '
                   'href="keys">API-ключи</a>.',
        'setup_4': '<strong>Укажи канал для логов.</strong> <code>/yatb log set</code> — YATB будет отправлять туда '
                   'предупреждения об использовании, проблемы с ключами и изменения.',
        'setup_5': '<strong>Уведомь участников.</strong> Дай ссылку на <a href="members">руководство для '
                   'участников</a> или добавь краткое правило, например:',
        'setup_check': '<code>/yatb status</code> показывает цепочку перевода твоего сервера и состояние каждого '
                       'сервиса.',
        'setup_rule': 'Перевод (YATB): В связанных каналах бот YATB автоматически переводит сообщения и публикует их '
                      'от твоего имени. Для этого они могут отправляться во внешние сервисы (например, ИИ-провайдеры, '
                      'Google). Тексты сообщений не сохраняются. Перевод «Только локально»: /yatb-user privacy',
        'site_desc': 'YATB связывает каналы Discord на разных языках и переводит каждое сообщение — под именем автора.',
        'tag_ai': 'Провайдер ИИ (например, Mistral или Google Gemini) — обычно лучшее качество',
        'tag_azure': 'Azure Translator (Microsoft)',
        'tag_google': 'Google Translate',
        'tag_libre': 'LibreTranslate — работает на нашем собственном сервере',
        'tag_raw': 'Не переведено — в тот момент ни один сервис не был доступен',
        'terms_1': 'YATB — это частный некоммерческий проект. Он бесплатен, в настоящее время работает только на '
                   'выбранных серверах и предоставляется без каких-либо гарантий доступности. Функции могут измениться '
                   'или быть прекращены в любое время.',
        'terms_1_title': '1. Сервис',
        'terms_2': 'Переводы выполняются машинами и могут быть неточными или неполными. Не полагайся на них в важных, '
                   'юридических, медицинских или финансовых вопросах.',
        'terms_2_title': '2. Переводы',
        'terms_3': '<ul><li>Ты несешь ответственность за добавленные тобой API-ключи, за условия их провайдеров и за '
                   'расходы. Подсчет использования YATB является приблизительным — устанавливай лимиты расходов у '
                   'провайдера.</li><li>Информируй своих участников о том, что сообщения в каналах Bridge переводятся '
                   'и могут быть отправлены внешним сервисам.</li><li>Используй YATB только в соответствии с законом и '
                   'условиями Discord — никакого спама, никаких злоупотреблений.</li></ul>',
        'terms_3_title': '3. Администраторы серверов',
        'terms_4': 'YATB предоставляется бесплатно и «как есть». Ответственность ограничена умыслом и грубой '
                   'неосторожностью, насколько это позволяет закон.',
        'terms_4_title': '4. Ответственность',
        'terms_5': 'Пожертвования (например, через Ko-fi) являются добровольными и не создают никаких прав на функции, '
                   'поддержку или доступность.',
        'terms_5_title': '5. Пожертвования',
        'terms_6': 'Применяется законодательство Германии.',
        'terms_6_title': '6. Заключительные положения',
        'terms_lead': 'Коротко и просто: YATB — это бесплатный хобби-проект. Используя YATB на сервере, ты '
                      'соглашаешься с этими условиями.',
        'terms_title': 'Условия использования'}}

SOURCE_HASH = {'admins_chain_intro': '1a810dee3646',
 'admins_chain_note': '2f9c0cb334ca',
 'admins_chain_title': '36b9538a8630',
 'admins_col_command': '713166971d73',
 'admins_col_desc': '526e0087cc3f',
 'admins_commands_title': 'f9c42878c290',
 'admins_dashboard': 'd7552aac9d0d',
 'admins_dashboard_title': '67b696468610',
 'admins_forum': 'd133d4864c9f',
 'admins_forum_perms': '51aee937438f',
 'admins_forum_title': '5346d54cffa5',
 'admins_lead': '91fec99fba5a',
 'admins_limits': '59ce5ffcd687',
 'admins_limits_title': '0dd60ead156b',
 'admins_remove': '415cb4b789f2',
 'admins_remove_title': '9d8c3e2dc03b',
 'admins_security': 'c2556bfd1175',
 'admins_security_title': '09c51a0eff66',
 'admins_setup_title': '191a4e9769c0',
 'admins_title': 'd01e61ce8395',
 'chain_1': '9641fd6b84e6',
 'chain_2': 'cd9f5cf0c9a2',
 'chain_3': '839af9b75d37',
 'chain_4': '481ff400443e',
 'chain_5': 'cabb04713ca9',
 'faq_dm_a': '3555fb9bb48f',
 'faq_dm_q': '2d9768cf4e7f',
 'faq_off_a': '4d606a2d0019',
 'faq_off_q': '1b29575e23d9',
 'faq_wrong_a': '106b19349103',
 'faq_wrong_q': '615e48099582',
 'feat_fallback_text': 'df514427ef61',
 'feat_fallback_title': 'd93089a423f8',
 'feat_format_text': 'e2e4a798a773',
 'feat_format_title': '79562a5372fc',
 'feat_keys_text': '9c19ce390958',
 'feat_keys_title': '1aa914697ff0',
 'feat_mirror_text': '3148692bddbc',
 'feat_mirror_title': 'cb34b3ceeed9',
 'feat_natural_text': '68c6af831a4e',
 'feat_natural_title': '8b83aedbb83a',
 'feat_privacy_text': 'd155cc3f02ac',
 'feat_privacy_title': 'dcad2c4b2c09',
 'footer_note': '6f8e2c44c723',
 'home_badge_langs': '5d5a84b96ef1',
 'home_badge_private': 'be2eea30c6ff',
 'home_badge_storage': '51d3ce030beb',
 'home_example_note': '24a236acd69b',
 'home_example_src': 'e119f8a197d7',
 'home_example_tgt': '06424c2a5d62',
 'home_example_tgt_channel': '303183b71842',
 'home_example_title': 'd029f87e3d80',
 'home_features_title': '6d7c0c70a6fe',
 'home_how_title': '9c870aa6e5e9',
 'home_lead': 'd5bfa1e13daf',
 'home_private_text': 'b14459c786e8',
 'home_private_title': '598bc9b019ff',
 'home_support_text': 'cccc113e60ea',
 'home_support_title': '11ffd39101f1',
 'home_title': '1d1189b0801b',
 'how_1': 'a42765ccdffc',
 'how_2': '615780624442',
 'how_3': '0d8744d7ef32',
 'imprint_title': 'd198ed30d09b',
 'keys_kind_ai': '8791254537f4',
 'keys_kind_mt': 'd054ef74d80d',
 'keys_lead': '31095e59b657',
 'keys_menu_note': '8816360b2a55',
 'keys_open': 'f4063d1b2a07',
 'keys_plan': 'fa8ed0bdabdd',
 'keys_privacy': '54a57c3147c4',
 'keys_source': '88be93e1726a',
 'keys_steps': '1de3df70ddf4',
 'keys_tips': 'f715e3e6fe3c',
 'keys_title': '56778d6133df',
 'kofi': '30facc2586d4',
 'lang_name': 'ba118bf7fc9c',
 'legal_binding': 'f3687a8757e9',
 'legal_updated': '9f8c977a7c7a',
 'members_choice_local': '6ff35f93bb44',
 'members_choice_note': 'cdb38c3a1b72',
 'members_choice_standard': '6e6e1dfa359c',
 'members_choice_title': '92475389ace1',
 'members_dashboard': '507eeb8a93d2',
 'members_data': '52d6baea5928',
 'members_data_title': 'ee5ef73aae18',
 'members_faq_title': '9a72221a2747',
 'members_how': 'f550f25df272',
 'members_how_title': '9c870aa6e5e9',
 'members_lead': '5d25a7e51167',
 'members_tags_intro': '77fb5ecc3ff9',
 'members_tags_title': '2898e0376359',
 'members_title': '892ae6013aa9',
 'nav_admins': '38e68419607c',
 'nav_dashboard': '67b696468610',
 'nav_home': '3a78695388b3',
 'nav_imprint': 'd198ed30d09b',
 'nav_keys': '98aae8972102',
 'nav_language': 'a4fe65264ef7',
 'nav_members': '892ae6013aa9',
 'nav_menu': '99af6606ff9d',
 'nav_more': 'c8e54e891a39',
 'nav_privacy': '54a57c3147c4',
 'nav_terms': 'ede548996483',
 'not_found_text': 'd3be4c51d1a7',
 'not_found_title': 'a469ab4ca4e5',
 'pd_backup_how_long': '7989b45fe40b',
 'pd_backup_what': '573c46434e2b',
 'pd_backup_why': 'b8caf96eb502',
 'pd_choice_how_long': '35a91aa7a85e',
 'pd_choice_what': 'c9024419a161',
 'pd_choice_why': 'd94f208759a1',
 'pd_config_how_long': '160505d57a77',
 'pd_config_what': '42898b1b60a2',
 'pd_config_why': 'f3ba69aa9825',
 'pd_map_how_long': '47f0dbd3e3c3',
 'pd_map_what': '26f6e93a50b1',
 'pd_map_why': '99b45a86d8bf',
 'pd_stats_how_long': 'cb5c34b7be85',
 'pd_stats_what': '01c47b1aadea',
 'pd_stats_why': 'b98c0e493bdf',
 'pd_text_how_long': 'e1279ce78a24',
 'pd_text_what': 'f9840ee8bef5',
 'pd_text_why': '9693a7292479',
 'privacy_basis': 'c5e11aae1082',
 'privacy_basis_title': '2848edf5fd3c',
 'privacy_bot_intro': '21e73e8ed224',
 'privacy_bot_title': 'c3be55dba252',
 'privacy_col_how_long': 'a646856428da',
 'privacy_col_note': 'b2d867a03385',
 'privacy_col_service': 'd677190e0a99',
 'privacy_col_what': 'cec3a9b89b2e',
 'privacy_col_why': 'd4e8830a71c7',
 'privacy_controller_missing': '899ec22ef8f5',
 'privacy_controller_title': '751a3235528a',
 'privacy_dash': '3f21190472da',
 'privacy_dash_title': '58abde59fd2a',
 'privacy_discord': '0f08b2e96bdd',
 'privacy_discord_title': '77c28c991c31',
 'privacy_lead': 'efaa3d5d3fe1',
 'privacy_rights': '7c34645548b3',
 'privacy_rights_title': '52a1791fa137',
 'privacy_services_intro': 'f17a5af34855',
 'privacy_services_title': '5c6df9ef50a1',
 'privacy_title': 'ba445cff3898',
 'privacy_web': '1f833156f9c7',
 'privacy_web_title': '27980c4931ca',
 'prov_azure': '44f1ac263396',
 'prov_gemini': '2dd7d37ececd',
 'prov_google_translate': '752a4b2e2cb0',
 'prov_groq': 'fa181b2aa8c5',
 'prov_libre': '609766191aa3',
 'prov_mistral': 'dc119ac54c2e',
 'prov_novita': '33610ffa6797',
 'setup_1': '4f431da4a8b5',
 'setup_2': '696e41b61405',
 'setup_3': 'c27cc1abe6ce',
 'setup_4': '3b9206306cc3',
 'setup_5': '96495df5bc03',
 'setup_check': '4aa37ee6fb72',
 'setup_rule': '5cc554daba18',
 'site_desc': '548c245095b8',
 'tag_ai': 'b41732cd0c6c',
 'tag_azure': 'c9d59ac4b6e7',
 'tag_google': '47a414e6183a',
 'tag_libre': '35249b946213',
 'tag_raw': '21e5a3f7c0b8',
 'terms_1': '90c32a355453',
 'terms_1_title': '5b9dd13447a6',
 'terms_2': '55a965d64b9c',
 'terms_2_title': '75e621bbaaef',
 'terms_3': '66d5fbaa17f0',
 'terms_3_title': 'b4883047a399',
 'terms_4': '881d7b4b9f23',
 'terms_4_title': 'fa33159ff63a',
 'terms_5': '3b7cd8a480af',
 'terms_5_title': 'cbfd85040e26',
 'terms_6': '87dffb3dd011',
 'terms_6_title': 'c868eb359dad',
 'terms_lead': 'd967eb55ab5b',
 'terms_title': '8c45a486e4b1'}
