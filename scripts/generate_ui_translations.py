"""Generate HA UI translations; values are ordered as in FIELDS below."""
import json
from pathlib import Path

FIELDS = (
    "connect_title", "connect_description", "url", "api_key",
    "entities_title", "entities_description", "lights", "switches", "fans",
    "climates", "temperature_sensors", "satellite_device_id",
    "cannot_connect", "invalid_url", "select_entities", "already_configured",
)
TRANSLATIONS = {
    "zh-Hans": (
        "连接 Laya", "输入 Home Assistant 可访问的 Laya 地址。请先安装 Laya 服务器。", "Laya 服务器地址", "API 密钥（可选）",
        "允许的实体", "助手只能控制或读取选定的实体。照明开关放在灯光，其他开关放在开关。", "灯和照明开关", "其他开关", "风扇", "空调设备（开/关）", "温度传感器或空调设备", "默认语音设备（可选）",
        "无法连接到兼容的 Laya 服务器。", "只输入服务器地址，例如 http://host:8000。", "至少选择一个实体，且不要在两个控制组中重复选择。", "此 Laya 服务器已配置。"),
    "hi": (
        "Laya से जुड़ें", "Home Assistant से पहुँच योग्य Laya पता दें। पहले Laya सर्वर स्थापित करें।", "Laya सर्वर URL", "API कुंजी (वैकल्पिक)",
        "अनुमत इकाइयाँ", "सहायक केवल चयनित इकाइयों को नियंत्रित या पढ़ सकता है। प्रकाश के स्विच लाइट में रखें।", "लाइट और प्रकाश स्विच", "अन्य स्विच", "पंखे", "जलवायु उपकरण (चालू/बंद)", "तापमान सेंसर या जलवायु उपकरण", "डिफ़ॉल्ट वॉइस उपग्रह (वैकल्पिक)",
        "संगत Laya सर्वर से कनेक्ट नहीं हो सका।", "केवल सर्वर URL दें, जैसे http://host:8000।", "कम से कम एक इकाई चुनें और उसे दो नियंत्रण समूहों में न रखें।", "यह Laya सर्वर पहले से कॉन्फ़िगर है।"),
    "es": (
        "Conectar con Laya", "Introduce una dirección de Laya accesible desde Home Assistant. Instala primero el servidor Laya.", "URL del servidor Laya", "Clave API (opcional)",
        "Entidades permitidas", "El asistente solo puede controlar o leer las entidades seleccionadas. Pon los interruptores de iluminación en Luces.", "Luces e interruptores de iluminación", "Otros interruptores", "Ventiladores", "Climatización (encender/apagar)", "Sensores de temperatura o climatización", "Satélite de voz predeterminado (opcional)",
        "No se puede conectar a un servidor Laya compatible.", "Introduce solo la URL del servidor, por ejemplo http://host:8000.", "Selecciona al menos una entidad y no la incluyas en dos grupos de control.", "Este servidor Laya ya está configurado."),
    "ar": (
        "الاتصال بـ Laya", "أدخل عنوان Laya الذي يستطيع Home Assistant الوصول إليه. ثبّت خادم Laya أولاً.", "عنوان خادم Laya", "مفتاح API (اختياري)",
        "الكيانات المسموح بها", "يمكن للمساعد التحكم في الكيانات المحددة أو قراءتها فقط. ضع مفاتيح الإضاءة ضمن الأضواء.", "الأضواء ومفاتيح الإضاءة", "مفاتيح أخرى", "المراوح", "أجهزة المناخ (تشغيل/إيقاف)", "حساسات الحرارة أو أجهزة المناخ", "القمر الصوتي الافتراضي (اختياري)",
        "تعذر الاتصال بخادم Laya متوافق.", "أدخل عنوان الخادم فقط، مثل http://host:8000.", "اختر كياناً واحداً على الأقل ولا تضعه في مجموعتي تحكم.", "خادم Laya هذا مهيأ بالفعل."),
    "fr": (
        "Connexion à Laya", "Saisissez une adresse Laya accessible depuis Home Assistant. Installez d'abord le serveur Laya.", "URL du serveur Laya", "Clé API (facultative)",
        "Entités autorisées", "L'assistant ne peut contrôler ou lire que les entités choisies. Placez les interrupteurs d'éclairage dans Lumières.", "Lumières et interrupteurs d'éclairage", "Autres interrupteurs", "Ventilateurs", "Climatisation (marche/arrêt)", "Capteurs de température ou climatisation", "Satellite vocal par défaut (facultatif)",
        "Connexion à un serveur Laya compatible impossible.", "Saisissez seulement l'URL du serveur, par exemple http://host:8000.", "Choisissez au moins une entité sans la placer dans deux groupes de contrôle.", "Ce serveur Laya est déjà configuré."),
    "bn": (
        "Laya-তে সংযোগ করুন", "Home Assistant থেকে পৌঁছানো যায় এমন Laya ঠিকানা লিখুন। আগে Laya সার্ভার ইনস্টল করুন।", "Laya সার্ভারের URL", "API কী (ঐচ্ছিক)",
        "অনুমোদিত সত্তা", "সহকারী শুধু নির্বাচিত সত্তা নিয়ন্ত্রণ বা পড়তে পারে। আলোর সুইচ Lights-এ রাখুন।", "আলো ও আলোর সুইচ", "অন্যান্য সুইচ", "পাখা", "জলবায়ু যন্ত্র (চালু/বন্ধ)", "তাপমাত্রা সেন্সর বা জলবায়ু যন্ত্র", "ডিফল্ট ভয়েস স্যাটেলাইট (ঐচ্ছিক)",
        "সামঞ্জস্যপূর্ণ Laya সার্ভারে সংযোগ করা যায়নি।", "শুধু সার্ভারের URL লিখুন, যেমন http://host:8000।", "অন্তত একটি সত্তা বাছুন এবং দুটি নিয়ন্ত্রণ দলে রাখবেন না।", "এই Laya সার্ভার আগেই কনফিগার করা আছে।"),
    "pt": (
        "Conectar ao Laya", "Informe um endereço Laya acessível pelo Home Assistant. Instale o servidor Laya primeiro.", "URL do servidor Laya", "Chave de API (opcional)",
        "Entidades permitidas", "O assistente só pode controlar ou ler as entidades selecionadas. Coloque interruptores de iluminação em Luzes.", "Luzes e interruptores de iluminação", "Outros interruptores", "Ventiladores", "Climatização (ligar/desligar)", "Sensores de temperatura ou climatização", "Satélite de voz padrão (opcional)",
        "Não foi possível conectar a um servidor Laya compatível.", "Informe apenas a URL do servidor, por exemplo http://host:8000.", "Selecione ao menos uma entidade e não a inclua em dois grupos de controle.", "Este servidor Laya já está configurado."),
    "id": (
        "Hubungkan ke Laya", "Masukkan alamat Laya yang dapat diakses Home Assistant. Pasang server Laya terlebih dahulu.", "URL server Laya", "Kunci API (opsional)",
        "Entitas yang diizinkan", "Asisten hanya dapat mengendalikan atau membaca entitas terpilih. Masukkan sakelar lampu ke Lampu.", "Lampu dan sakelar lampu", "Sakelar lain", "Kipas", "Perangkat iklim (nyala/mati)", "Sensor suhu atau perangkat iklim", "Satelit suara bawaan (opsional)",
        "Tidak dapat terhubung ke server Laya yang kompatibel.", "Masukkan hanya URL server, misalnya http://host:8000.", "Pilih setidaknya satu entitas dan jangan taruh di dua grup kendali.", "Server Laya ini sudah dikonfigurasi."),
    "ur": (
        "Laya سے رابطہ", "وہ Laya پتہ درج کریں جس تک Home Assistant پہنچ سکے۔ پہلے Laya سرور نصب کریں۔", "Laya سرور URL", "API کلید (اختیاری)",
        "اجازت یافتہ ادارے", "معاون صرف منتخب اداروں کو کنٹرول یا پڑھ سکتا ہے۔ روشنی کے سوئچ لائٹس میں رکھیں۔", "لائٹس اور روشنی کے سوئچ", "دوسرے سوئچ", "پنکھے", "ماحولیاتی آلات (آن/آف)", "درجہ حرارت سینسر یا ماحولیاتی آلات", "ڈیفالٹ صوتی سیٹلائٹ (اختیاری)",
        "موزوں Laya سرور سے رابطہ نہیں ہو سکا۔", "صرف سرور URL درج کریں، مثلاً http://host:8000۔", "کم از کم ایک ادارہ چنیں اور دو کنٹرول گروہوں میں نہ رکھیں۔", "یہ Laya سرور پہلے سے ترتیب دیا گیا ہے۔"),
    "de": (
        "Mit Laya verbinden", "Gib eine Laya-Adresse ein, die Home Assistant erreichen kann. Installiere zuerst den Laya-Server.", "Laya-Server-URL", "API-Schlüssel (optional)",
        "Erlaubte Entitäten", "Der Assistent darf nur ausgewählte Entitäten steuern oder lesen. Lichtschalter gehören zu Lichter.", "Lichter und Lichtschalter", "Andere Schalter", "Ventilatoren", "Klimageräte (ein/aus)", "Temperatursensoren oder Klimageräte", "Standard-Sprachsatellit (optional)",
        "Keine Verbindung zu einem kompatiblen Laya-Server.", "Gib nur die Server-URL ein, etwa http://host:8000.", "Wähle mindestens eine Entität und ordne sie nicht zwei Steuergruppen zu.", "Dieser Laya-Server ist bereits eingerichtet."),
}

SPOKEN_NAMES_LABEL = {
    "zh-Hans": "口语名称（JSON，可选）", "hi": "बोले जाने वाले नाम (JSON, वैकल्पिक)",
    "es": "Nombres hablados (JSON, opcional)", "ar": "الأسماء المنطوقة (JSON، اختياري)",
    "fr": "Noms prononcés (JSON, facultatif)", "bn": "কথ্য নাম (JSON, ঐচ্ছিক)",
    "pt": "Nomes falados (JSON, opcional)", "id": "Nama lisan (JSON, opsional)",
    "ur": "بولے جانے والے نام (JSON، اختیاری)", "de": "Gesprochene Namen (JSON, optional)",
}

root = Path(__file__).resolve().parents[1] / 'custom_components' / 'laya_assistant' / 'translations'
for code, values in TRANSLATIONS.items():
    if len(values) != len(FIELDS):
        raise ValueError(f'{code}: {len(values)} values')
    v = dict(zip(FIELDS, values))
    fields = {key: v[key] for key in ('lights','switches','fans','climates','temperature_sensors','satellite_device_id')}
    fields['spoken_names'] = SPOKEN_NAMES_LABEL[code]
    result = {'config': {'step': {
        'user': {'title': v['connect_title'], 'description': v['connect_description'], 'data': {'url': v['url'], 'api_key': v['api_key']}},
        'entities': {'title': v['entities_title'], 'description': v['entities_description'], 'data': fields},
    }, 'error': {key: v[key] for key in ('cannot_connect','invalid_url','select_entities')},
       'abort': {'already_configured': v['already_configured']}},
      'options': {'step': {'init': {'title': v['entities_title'], 'data': fields}}}}
    (root / f'{code}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
