"""Conversation text for ten widely spoken languages, plus Russian."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Locale:
    code: str
    domain_prompt: str
    domain_criteria: tuple[str, str, str, str]
    target_prompts: tuple[str, str, str, str]
    none_target: str
    action_prompt: str
    action_check_prompt: str
    action_criteria: tuple[str, str, str]
    state_criteria: tuple[str, str, str]
    light_template: str
    light_terms: tuple[str, ...]
    on_terms: tuple[str, ...]
    off_terms: tuple[str, ...]
    replies: tuple[str, str, str, str, str, str, str, str, str, str]


# replies: clarify, failed, short, denied_sensor, denied_device,
# unavailable_sensor, unavailable_device, time, temperature, turned_on/off.
LOCALES = {
    "en": Locale("en", "Classify the request as a device command, temperature question, time question or other.",
        ("Turn a light or device on or off now", "Ask for a current temperature reading", "Ask for the current time", "Any other request"),
        ("Which current temperature sensor is requested?", "Which room's lights does the user request?", "Which specific light fixture is requested?", "Which allowed device is requested?"),
        "Other, ambiguous or not listed", "What does the user ask to do with the device?", "Should the device end up on or off?",
        ("turn on", "turn off", "No action"), ("on", "off", "Unclear"), "lights in {area}",
        ("light", "lamp", "lighting"), ("turn on", "switch on", "activate"), ("turn off", "switch off", "deactivate"),
        ("Please clarify the device or command.", "The command failed.", "Say a short command.", "No access to the sensor.", "No access to the device.", "Temperature unavailable.", "Device unavailable.", "It is {time}.", "Temperature {target}: {value} {unit}.", "Turned {action}: {target}.")),
    "zh": Locale("zh", "判断用户请求是控制设备、查询温度、查询时间还是其他内容。",
        ("打开或关闭灯或设备", "查询当前温度", "询问现在的时间", "其他或不清楚"),
        ("用户问的是哪个温度传感器？", "用户说的是哪个房间的灯？", "用户说的是哪盏具体的灯？", "用户说的是哪个设备？"),
        "其他或不确定", "用户要求打开还是关闭设备？", "设备最终应该是开启还是关闭？",
        ("打开", "关闭", "没有操作"), ("开启", "关闭", "不清楚"), "{area}的灯",
        ("灯", "照明"), ("打开", "开启"), ("关闭", "关掉"),
        ("请明确设备或指令。", "指令执行失败。", "请说一个简短的指令。", "无权读取传感器。", "无权控制设备。", "温度不可用。", "设备不可用。", "现在是{time}。", "{target}的温度是{value}{unit}。", "已{action}：{target}。")),
    "hi": Locale("hi", "अनुरोध को उपकरण नियंत्रण, तापमान प्रश्न, समय प्रश्न या अन्य में वर्गीकृत करें।",
        ("लाइट या उपकरण चालू या बंद करें", "वर्तमान तापमान पूछें", "वर्तमान समय पूछें", "अन्य या अस्पष्ट"),
        ("कौन सा तापमान सेंसर पूछा गया है?", "किस कमरे की लाइट?", "कौन सी विशेष लाइट?", "कौन सा उपकरण?"),
        "अन्य या अस्पष्ट", "उपयोगकर्ता उपकरण चालू या बंद करना चाहता है?", "अंत में उपकरण चालू होगा या बंद?",
        ("चालू", "बंद", "कोई क्रिया नहीं"), ("चालू", "बंद", "अस्पष्ट"), "{area} की लाइट",
        ("लाइट", "रोशनी", "बत्ती"), ("चालू", "जलाओ"), ("बंद", "बुझाओ"),
        ("उपकरण या आदेश स्पष्ट करें।", "आदेश पूरा नहीं हुआ।", "छोटा आदेश दें।", "सेंसर पढ़ने की अनुमति नहीं है।", "उपकरण नियंत्रित करने की अनुमति नहीं है।", "तापमान उपलब्ध नहीं है।", "उपकरण उपलब्ध नहीं है।", "अभी {time} बजे हैं।", "{target} का तापमान {value} {unit} है।", "{target}: {action} किया गया।")),
    "es": Locale("es", "Clasifica la petición: controlar un dispositivo, consultar temperatura, consultar hora u otra cosa.",
        ("Encender o apagar una luz o dispositivo", "Preguntar la temperatura actual", "Preguntar la hora actual", "Otra petición"),
        ("¿Qué sensor de temperatura se menciona?", "¿De qué habitación son las luces?", "¿Qué luz concreta se menciona?", "¿Qué dispositivo se menciona?"),
        "Otro o ambiguo", "¿El usuario quiere encender o apagar el dispositivo?", "¿El dispositivo debe quedar encendido o apagado?",
        ("encender", "apagar", "sin acción"), ("encendido", "apagado", "no está claro"), "luces de {area}",
        ("luz", "luces", "lámpara", "iluminación"), ("enciende", "encender", "prende"), ("apaga", "apagar"),
        ("Aclara el dispositivo o la orden.", "No se pudo ejecutar la orden.", "Di una orden breve.", "Sin permiso para leer el sensor.", "Sin permiso para controlar el dispositivo.", "Temperatura no disponible.", "Dispositivo no disponible.", "Son las {time}.", "Temperatura de {target}: {value} {unit}.", "{target}: {action}.")),
    "ar": Locale("ar", "صنّف الطلب: التحكم بجهاز أو سؤال عن الحرارة أو الوقت أو طلب آخر.",
        ("تشغيل أو إطفاء الضوء أو الجهاز", "السؤال عن درجة الحرارة الحالية", "السؤال عن الوقت الحالي", "طلب آخر"),
        ("أي مستشعر حرارة يقصده المستخدم؟", "ما الغرفة المذكورة في الطلب؟", "أي ضوء محدد؟", "أي جهاز؟"),
        "آخر أو غير واضح", "هل يريد المستخدم تشغيل الجهاز أم إيقافه؟", "هل يجب أن يكون الجهاز مشغلاً أم متوقفاً؟",
        ("تشغيل", "إيقاف", "لا أمر"), ("مشغل", "متوقف", "غير واضح"), "أضواء {area}",
        ("ضوء", "أضواء", "نور", "مصباح"), ("شغل", "تشغيل", "افتح"), ("أطفئ", "اطفئ", "إيقاف", "اقفل"),
        ("حدد الجهاز أو الأمر من فضلك.", "تعذر تنفيذ الأمر.", "قل أمراً قصيراً.", "لا إذن لقراءة المستشعر.", "لا إذن للتحكم بالجهاز.", "درجة الحرارة غير متاحة.", "الجهاز غير متاح.", "الوقت الآن {time}.", "درجة حرارة {target}: {value} {unit}.", "تم {action}: {target}.")),
    "fr": Locale("fr", "Classe la demande : commander un appareil, demander la température, demander l'heure ou autre.",
        ("Allumer ou éteindre une lumière ou un appareil", "Demander la température actuelle", "Demander l'heure actuelle", "Autre demande"),
        ("Quel capteur de température est demandé ?", "Les lumières de quelle pièce ?", "Quelle lumière précise ?", "Quel appareil ?"),
        "Autre ou ambigu", "L'utilisateur veut-il allumer ou éteindre l'appareil ?", "L'appareil doit-il être allumé ou éteint ?",
        ("allumer", "éteindre", "aucune action"), ("allumé", "éteint", "incertain"), "lumières de {area}",
        ("lumière", "lumières", "lampe", "éclairage"), ("allume", "allumer", "active"), ("éteins", "éteindre", "désactive"),
        ("Précisez l'appareil ou la commande.", "La commande a échoué.", "Dites une commande courte.", "Accès refusé au capteur.", "Accès refusé à l'appareil.", "Température indisponible.", "Appareil indisponible.", "Il est {time}.", "Température de {target} : {value} {unit}.", "{target} : {action}.")),
    "bn": Locale("bn", "অনুরোধটি শ্রেণিবদ্ধ করুন: যন্ত্র নিয়ন্ত্রণ, তাপমাত্রা, সময়, অথবা অন্য কিছু।",
        ("আলো বা যন্ত্র চালু বা বন্ধ করা", "বর্তমান তাপমাত্রা জিজ্ঞাসা", "বর্তমান সময় জিজ্ঞাসা", "অন্য অনুরোধ"),
        ("কোন তাপমাত্রা সেন্সর?", "কোন ঘরের আলো?", "কোন নির্দিষ্ট আলো?", "কোন যন্ত্র?"),
        "অন্য বা অস্পষ্ট", "ব্যবহারকারী যন্ত্র চালু না বন্ধ করতে চান?", "শেষে যন্ত্রটি চালু না বন্ধ থাকবে?",
        ("চালু", "বন্ধ", "কোনো কাজ নয়"), ("চালু", "বন্ধ", "অস্পষ্ট"), "{area} এর আলো",
        ("আলো", "বাতি"), ("চালু", "জ্বালাও"), ("বন্ধ", "নিভাও"),
        ("যন্ত্র বা নির্দেশ স্পষ্ট করুন।", "নির্দেশ কার্যকর হয়নি।", "ছোট নির্দেশ দিন।", "সেন্সর পড়ার অনুমতি নেই।", "যন্ত্র নিয়ন্ত্রণের অনুমতি নেই।", "তাপমাত্রা পাওয়া যাচ্ছে না।", "যন্ত্র পাওয়া যাচ্ছে না।", "এখন সময় {time}।", "{target} এর তাপমাত্রা {value} {unit}।", "{target}: {action} করা হয়েছে।")),
    "pt": Locale("pt", "Classifique o pedido: controlar dispositivo, perguntar temperatura, perguntar hora ou outro.",
        ("Ligar ou desligar uma luz ou dispositivo", "Perguntar a temperatura atual", "Perguntar a hora atual", "Outro pedido"),
        ("Qual sensor de temperatura?", "Luzes de qual cômodo?", "Qual luz específica?", "Qual dispositivo?"),
        "Outro ou ambíguo", "O usuário quer ligar ou desligar o dispositivo?", "O dispositivo deve ficar ligado ou desligado?",
        ("ligar", "desligar", "sem ação"), ("ligado", "desligado", "não está claro"), "luzes de {area}",
        ("luz", "luzes", "lâmpada", "iluminação"), ("ligue", "ligar", "acenda"), ("desligue", "desligar", "apague"),
        ("Esclareça o dispositivo ou comando.", "Não foi possível executar o comando.", "Diga um comando curto.", "Sem permissão para ler o sensor.", "Sem permissão para controlar o dispositivo.", "Temperatura indisponível.", "Dispositivo indisponível.", "Agora são {time}.", "Temperatura de {target}: {value} {unit}.", "{target}: {action}.")),
    "id": Locale("id", "Klasifikasikan permintaan: kendali perangkat, suhu, waktu, atau lainnya.",
        ("Nyalakan atau matikan lampu atau perangkat", "Tanya suhu saat ini", "Tanya waktu saat ini", "Permintaan lain"),
        ("Sensor suhu yang mana?", "Lampu di ruangan mana?", "Lampu khusus yang mana?", "Perangkat yang mana?"),
        "Lainnya atau tidak jelas", "Pengguna ingin menyalakan atau mematikan perangkat?", "Perangkat harus menyala atau mati?",
        ("nyalakan", "matikan", "tidak ada aksi"), ("menyala", "mati", "tidak jelas"), "lampu di {area}",
        ("lampu", "cahaya", "penerangan"), ("nyalakan", "hidupkan"), ("matikan", "padamkan"),
        ("Perjelas perangkat atau perintah.", "Perintah gagal.", "Ucapkan perintah singkat.", "Tidak diizinkan membaca sensor.", "Tidak diizinkan mengendalikan perangkat.", "Suhu tidak tersedia.", "Perangkat tidak tersedia.", "Sekarang pukul {time}.", "Suhu {target}: {value} {unit}.", "{target}: {action}.")),
    "ur": Locale("ur", "درخواست کی درجہ بندی کریں: آلہ چلانا، درجہ حرارت، وقت یا دوسری درخواست۔",
        ("روشنی یا آلہ چلانا یا بند کرنا", "موجودہ درجہ حرارت پوچھنا", "موجودہ وقت پوچھنا", "دوسری درخواست"),
        ("کون سا درجہ حرارت سینسر؟", "کس کمرے کی روشنی؟", "کون سی مخصوص روشنی؟", "کون سا آلہ؟"),
        "دوسرا یا غیر واضح", "صارف آلہ چلانا چاہتا ہے یا بند کرنا؟", "آخر میں آلہ چل رہا ہو یا بند؟",
        ("چلانا", "بند کرنا", "کوئی حکم نہیں"), ("چالو", "بند", "غیر واضح"), "{area} کی روشنیاں",
        ("روشنی", "بتیاں", "بتی"), ("چلاؤ", "جلاؤ", "آن"), ("بند", "بجھاؤ", "آف"),
        ("آلہ یا حکم واضح کریں۔", "حکم ناکام رہا۔", "مختصر حکم دیں۔", "سینسر پڑھنے کی اجازت نہیں۔", "آلہ چلانے کی اجازت نہیں۔", "درجہ حرارت دستیاب نہیں۔", "آلہ دستیاب نہیں۔", "اب وقت {time} ہے۔", "{target} کا درجہ حرارت {value} {unit} ہے۔", "{target}: {action} کر دیا گیا۔")),
    "de": Locale("de", "Ordne die Anfrage ein: Gerät steuern, Temperatur abfragen, Uhrzeit abfragen oder etwas anderes.",
        ("Licht oder Gerät ein- oder ausschalten", "Aktuelle Temperatur abfragen", "Aktuelle Uhrzeit abfragen", "Andere Anfrage"),
        ("Welcher Temperatursensor ist gemeint?", "Licht in welchem Raum?", "Welche einzelne Lampe ist gemeint?", "Welches Gerät ist gemeint?"),
        "Anderes oder unklar", "Soll das Gerät eingeschaltet oder ausgeschaltet werden?", "Soll das Gerät danach an oder aus sein?",
        ("einschalten", "ausschalten", "keine Aktion"), ("an", "aus", "unklar"), "Licht in {area}",
        ("licht", "lampe", "beleuchtung"), ("schalte ein", "einschalten", "mach an"), ("schalte aus", "ausschalten", "mach aus"),
        ("Bitte Gerät oder Befehl präzisieren.", "Der Befehl ist fehlgeschlagen.", "Bitte einen kurzen Befehl sagen.", "Keine Berechtigung für den Sensor.", "Keine Berechtigung für das Gerät.", "Temperatur nicht verfügbar.", "Gerät nicht verfügbar.", "Es ist {time} Uhr.", "Temperatur von {target}: {value} {unit}.", "{target}: {action}.")),
    "ru": Locale("ru", "Определи домен команды пользователя. on_off: непосредственная просьба включить или выключить свет, устройство; temperature: вопрос о температуре; time: вопрос о текущем времени; none: другое.",
        ("включи свет, выключи свет, зажги свет, погаси свет, turn on/off device", "какая температура, сколько градусов", "который час, сколько времени", "другая просьба"),
        ("Какой датчик температуры назван?", "Какую комнату со светом пользователь назвал?", "Какую конкретную группу света или устройство имеет в виду пользователь?", "Какое устройство названо?"),
        "другое устройство или неизвестно", "Что просит сделать пользователь со светом?", "Свет должен стать включённым или выключенным?",
        ("включить свет", "выключить свет", "нет команды"), ("включённым", "выключенным", "неясно"), "свет в {area}",
        ("свет", "освещение", "лампа", "люстра"), ("включи", "зажги"), ("выключи", "погаси"),
        ("Уточните устройство или команду.", "Не удалось выполнить команду.", "Скажите короткую команду.", "Нет доступа к датчику.", "Нет доступа к устройству.", "Температура недоступна.", "Устройство недоступно.", "Сейчас {time}.", "Температура {target}: {value} {unit}.", "{target}: {action}.")),
}


def get_locale(language: str | None) -> Locale:
    """Resolve HA locale variants such as zh-Hans and pt-BR."""
    base = (language or "en").split("-", 1)[0].split("_", 1)[0].lower()
    return LOCALES.get(base, LOCALES["en"])


SUPPORTED_LANGUAGES = ["en", "zh", "zh-Hans", "zh-Hant", "hi", "es", "ar", "fr", "bn", "pt", "pt-BR", "pt-PT", "id", "ur", "ru", "de"]

DONE_ACTIONS = {
    "en": ("on", "off"), "zh": ("打开", "关闭"), "hi": ("चालू", "बंद"),
    "es": ("encendido", "apagado"), "ar": ("تشغيل", "إيقاف"),
    "fr": ("allumé", "éteint"), "bn": ("চালু", "বন্ধ"),
    "pt": ("ligado", "desligado"), "id": ("menyala", "mati"),
    "ur": ("چالو", "بند"), "ru": ("включено", "выключено"),
    "de": ("eingeschaltet", "ausgeschaltet"),
}

WHOLE_HOME_TERMS = {
    "en": ("all lights", "whole home", "everywhere"),
    "zh": ("所有灯", "全部灯", "全屋灯"),
    "hi": ("सभी लाइट", "सारे घर"),
    "es": ("todas las luces", "toda la casa"),
    "ar": ("كل الأضواء", "كل الأنوار", "المنزل كله"),
    "fr": ("toutes les lumières", "toute la maison"),
    "bn": ("সব আলো", "পুরো বাড়ি"),
    "pt": ("todas as luzes", "casa toda"),
    "id": ("semua lampu", "seluruh rumah"),
    "ur": ("تمام روشنیاں", "پورے گھر"),
    "ru": ("весь свет", "все лампы", "везде", "во всём доме"),
    "de": ("alle lichter", "im ganzen haus"),
}
