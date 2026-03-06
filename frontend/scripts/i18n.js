/**
 * Internationalization (i18n) module for Milana frontend
 * Supports Russian and English languages
 */

const STORAGE_KEY = 'milana_language';

// Translations dictionary
export const translations = {
    ru: {
        // Header
        'header.title': 'Milana Superintelligence Hub',
        'header.subtitle': 'Фиолетовый интерфейс для диалогов сильнее OpenAI и DeepSeek',
        'header.tag': 'Hyper AI Edition',

        // Sidebar
        'sidebar.brand.name': 'Milana',
        'sidebar.brand.subtitle': 'Superintelligence',
        'sidebar.newChat': '＋ Новый диалог',
        'sidebar.apps': 'Приложения',
        'sidebar.footer': 'Milana Hyper AI удерживает ваш ключ только в браузере и открывает сверхбыстрые ответы. Переключайтесь между модулями без перезапуска.',

        // Hero card
        'hero.title': 'Milana Hyperintelligence',
        'hero.description': 'Испытайте фиолетовый интерфейс, вдохновлённый ChatGPT, но усиленный движком AKSI. Бесплатный режим Super GPTb соединяет память, интернет-оркестратор и мгновенные статусы — без ожидания ключа.',
        'hero.launch': 'Открыть суперчат',
        'hero.tag.realtime': 'Realtime Insight',
        'hero.tag.orchestrated': 'Orchestrated Prompts',
        'hero.tag.free': 'Free Tier Ready',

        // GPT Integration
        'gpt.title': 'Интеграция с GPT',
        'gpt.description': 'Milana Super GPTb уже готова отвечать в бесплатном режиме. Введите ключ OpenAI API, чтобы подключить облачные модели и увеличить мощность.',
        'gpt.freeTier.title': 'Бесплатный режим:',
        'gpt.freeTier.description': 'суперчат работает на памяти и интернет-данных даже без ключа. Ключ нужен только для прямого доступа к API OpenAI.',
        'gpt.saveKey': 'Сохранить ключ',
        'gpt.testKey': 'Проверить',
        'gpt.clearKey': 'Удалить',
        'gpt.note': 'Ключ хранится локально в вашем браузере. Для повышенной безопасности рекомендуется использовать прокси-сервер.',

        // Memory & Knowledge
        'cognition.title': 'Память и интернет-оркестратор GPTb',
        'memory.title': 'Долгосрочная память',
        'memory.clear': 'Очистить память',
        'memory.empty': 'Память пуста. Начните диалог, и Milana сохранит ключевые инсайты.',
        'knowledge.title': 'Источники внешних данных',
        'knowledge.refresh': 'Обновить данные',
        'knowledge.note': 'Данные хранятся только локально и обновляются по запросу.',
        'knowledge.sync': 'Интернет-данные синхронизированы.',
        'knowledge.loading': 'Подключаем интернет-источники...',
        'knowledge.noMatch': 'Источники активны, но не нашли совпадений.',
        'knowledge.activateHint': 'Активируйте источники или уточните запрос, чтобы получить внешние данные.',

        // Chat
        'chat.intro': 'Привет! Я Милана Hyper AI. Помогаю мыслить стратегически, создавать код и воплощать идеи лучше любых стандартных моделей.',
        'chat.placeholder': 'Введите сообщение',
        'chat.send': 'Отправить',
        'chat.attachFile': 'Прикрепить файл',
        'chat.attachPhoto': 'Прикрепить фото',
        'chat.system': 'Ты — Милана, сверхинтеллект AKSI. Отвечай по-русски, вдохновляюще и по делу. Предлагай стратегии, идеи и конкретные шаги, оставаясь доброжелательной и уверенной.',
        'chat.syncStatus': 'Синхронизирую память и интернет-данные...',
        'chat.requestStatus': 'Запрашиваем ответ у Milana Hyper AI...',
        'chat.ready': 'Готово.',
        'chat.newDialog': 'Я на связи для нового диалога.',
        'chat.noKey': 'Добавьте ключ OpenAI API в блоке выше, чтобы я смог отвечать.',
        'chat.error': 'Не удалось получить ответ от GPT. Попробуйте ещё раз.',
        'chat.user': 'Вы',
        'chat.analyzing': 'Анализирую изображение...',
        'chat.uploadSuccess': 'Файл загружен',

        // Apps
        'app.moodmirror': 'Определите настроение и получите отражение.',
        'app.mindmirror': 'Записывайте мысли и получайте совет.',
        'app.mindlink': 'Симуляция интерфейса мозг–компьютер.',
        'app.healthscan': 'Простой анализ здоровья на основе пульса и давления.',
        'app.mentor': 'Получите мотивационный совет.',
        'app.family': 'Организуйте семейные события и задачи.',
        'app.aura': 'Определите вашу «ауру» и цвет настроения.',
        'app.aksilove': 'Найдите свою пару в случайном подборе.',
        'app.moodradio': 'Плейлисты под ваше настроение.',
        'app.aksishopping': 'Простая корзина для покупки товаров.',
        'app.aistylist': 'Персональный стилист: получите рекомендации по стилю.',
        'app.ecogaze': 'Оцените экологические показатели вокруг вас.',
        'app.dreamjournal': 'Ведите дневник снов прямо в браузере.',
        'app.aksicompanion': 'Виртуальный компаньон, которого можно кормить и слушать.',
        'app.dressupar': 'Примерка одежды в режиме дополненной реальности (демо-версия для веб).',
        'app.globalid': 'Создайте цифровое удостоверение личности.',
        'app.aksichat': 'Подключите GPT, чтобы получать живые ответы от виртуального ассистента.',
        'app.lifescan': 'Расчёт индекса массы тела (ИМТ).',
        'app.timecapsule': 'Создайте капсулу времени — сообщение, которое откроется позже.',
        'app.telehelp': 'Служба SOS для экстренных случаев.',
        'app.storyai': 'Создайте короткий рассказ из вашей идеи с помощью GPT.',

        // Language switcher
        'lang.switch': 'English',
        'lang.current': 'RU',

        // Moods
        'mood.happy': 'Счастливый',
        'mood.sad': 'Грустный',
        'mood.angry': 'Злой',
        'mood.calm': 'Спокойный',
        'mood.result.happy': 'Вы счастливы!',
        'mood.result.sad': 'Вы грустите.',
        'mood.result.angry': 'Вы злитесь.',
        'mood.result.calm': 'Вы спокойны.',

        // Aura
        'aura.happy': 'Ваша аура сияет радостью!',
        'aura.sad': 'Ваша аура спокойна и задумчива.',
        'aura.angry': 'Аура насыщена сильной энергией.',
        'aura.calm': 'Аура ровная и гармоничная.',

        // Common buttons and labels
        'btn.show': 'Показать',
        'btn.save': 'Сохранить',
        'btn.analyze': 'Анализировать',
        'btn.getAdvice': 'Получить совет',
        'btn.add': 'Добавить',
        'btn.refresh': 'Обновить',
        'btn.tryOn': 'Примерить',
        'btn.generate': 'Сгенерировать',
        'btn.calculate': 'Рассчитать',
        'btn.findMatch': 'Найти пару',
        'btn.showPlaylist': 'Показать плейлист',
        'btn.getRecommendation': 'Получить рекомендацию',
        'btn.sendSos': 'Отправить SOS',
        'btn.generateId': 'Сгенерировать удостоверение',
        'btn.open': 'Открыть доступные сообщения',
        'btn.talk': 'Сказать что-то',
        'btn.feed': 'Накормить',

        // Form labels
        'form.pulse': 'Пульс (уд/мин)',
        'form.systolic': 'Систолическое давление',
        'form.eventName': 'Название события',
        'form.yourName': 'Ваше имя',
        'form.preference': 'Кого вы ищете (характеристика)',
        'form.stylePreference': 'Введите предпочтение (цвет, стиль...)',
        'form.light': 'Освещённость (люкс)',
        'form.noise': 'Шум (дБ)',
        'form.co2': 'CO₂ (ppm)',
        'form.describeDream': 'Опишите ваш сон...',
        'form.describeThoughts': 'Опишите свои мысли...',
        'form.weight': 'Вес (кг)',
        'form.height': 'Рост (см)',
        'form.capsuleMessage': 'Сообщение в будущее',
        'form.fullName': 'ФИО',
        'form.idNumber': 'Номер ID',
        'form.storyPrompt': 'Введите тему или героя...',
        'form.selectClothes': 'Выберите одежду',

        // Messages
        'msg.sosSuccess': 'Запрос SOS отправлен! Дождитесь помощи.',
        'msg.companionHappy': 'Уровень радости',
        'msg.companionThanks': 'Спасибо за еду! :)',
        'msg.cartCount': 'В корзине',
        'msg.addToCart': 'Добавить в корзину',
        'msg.entry': 'Запись',
        'msg.created': 'Дата создания',
        'msg.name': 'Имя',
        'msg.id': 'ID',
        'msg.event': 'Событие',
        'msg.date': 'Дата',
        'msg.bmi': 'ИМТ',
        'msg.selected': 'Вы выбрали',
        'msg.compatibility': 'ваша совместимость на сегодня',
        'msg.considering': 'учитывая предпочтение',

        // Health messages
        'health.pulse.high': 'Повышенный пульс.',
        'health.pulse.low': 'Низкий пульс.',
        'health.pulse.normal': 'Пульс в норме.',
        'health.pressure.high': 'Высокое давление.',
        'health.pressure.low': 'Низкое давление.',
        'health.pressure.normal': 'Давление в норме.',

        // BMI categories
        'bmi.underweight': 'Недостаток веса',
        'bmi.normal': 'Норма',
        'bmi.overweight': 'Избыточный вес',
        'bmi.obese': 'Ожирение',

        // Eco analysis
        'eco.light.good': 'Хорошая освещённость.',
        'eco.light.bad': 'Плохая освещённость.',
        'eco.noise.normal': 'Шум в норме.',
        'eco.noise.high': 'Шум высокий.',
        'eco.co2.normal': 'CO₂ в норме.',
        'eco.co2.high': 'Повышенный CO₂.',

        // MindLink
        'mindlink.low': 'Низкая активность',
        'mindlink.medium': 'Средняя активность',
        'mindlink.high': 'Высокая активность',

        // Mentor advices
        'mentor.advice1': 'Верить в себя — первый шаг к успеху.',
        'mentor.advice2': 'Каждый день учитесь чему-то новому.',
        'mentor.advice3': 'Планируйте и ставьте маленькие цели.',
        'mentor.advice4': 'Не бойтесь ошибок — они учат.',

        // Mind reflections
        'mind.reflection1': 'Попробуйте выразить благодарность за что-то.',
        'mind.reflection2': 'Сделайте глубокий вдох и расслабьтесь.',
        'mind.reflection3': 'Запишите положительный момент из дня.',
        'mind.reflection4': 'Уделите время отдыху и восстановлению.',
        'mind.tip': 'Совет',

        // Companion phrases
        'companion.phrase1': 'Приятно с вами общаться!',
        'companion.phrase2': 'Надеюсь, у вас хороший день!',
        'companion.phrase3': 'Я всегда рядом.',
        'companion.phrase4': 'Расскажите мне что-то новое.',

        // Stylist advices
        'stylist.advice1': 'Белая рубашка с джинсами — классика, которая подходит всем.',
        'stylist.advice2': 'Пастельные тона и лёгкие ткани — отличный выбор для весны.',
        'stylist.advice3': 'Спортивный костюм сочетается с кроссовками для активного дня.',
        'stylist.advice4': 'Деловой костюм подчеркнёт вашу уверенность.',
        'stylist.considerChoice': 'Учтите ваш выбор',

        // Clothes
        'clothes.dress': 'Платье',
        'clothes.suit': 'Костюм',
        'clothes.sportswear': 'Спортивный комплект',

        // Story AI
        'story.generating': 'Обращаемся к GPT...',
        'story.ready': 'Готово.',
        'story.fallback': 'Показан офлайн-шаблон.',
        'story.systemPrompt': 'Ты — автор вдохновляющих коротких историй на русском языке.',
        'story.userPrompt': 'Напиши цельный вдохновляющий рассказ объёмом 120–180 слов по теме: "{prompt}". Сделай финал позитивным.'
    },
    en: {
        // Header
        'header.title': 'Milana Superintelligence Hub',
        'header.subtitle': 'Purple interface for conversations stronger than OpenAI and DeepSeek',
        'header.tag': 'Hyper AI Edition',

        // Sidebar
        'sidebar.brand.name': 'Milana',
        'sidebar.brand.subtitle': 'Superintelligence',
        'sidebar.newChat': '＋ New Chat',
        'sidebar.apps': 'Applications',
        'sidebar.footer': 'Milana Hyper AI stores your key only in the browser and unlocks ultra-fast responses. Switch between modules without restarting.',

        // Hero card
        'hero.title': 'Milana Hyperintelligence',
        'hero.description': 'Experience the purple interface inspired by ChatGPT but enhanced with the AKSI engine. Free Super GPTb mode combines memory, internet orchestrator, and instant statuses — no key required.',
        'hero.launch': 'Open Superchat',
        'hero.tag.realtime': 'Realtime Insight',
        'hero.tag.orchestrated': 'Orchestrated Prompts',
        'hero.tag.free': 'Free Tier Ready',

        // GPT Integration
        'gpt.title': 'GPT Integration',
        'gpt.description': 'Milana Super GPTb is ready to respond in free mode. Enter your OpenAI API key to connect cloud models and increase power.',
        'gpt.freeTier.title': 'Free Mode:',
        'gpt.freeTier.description': 'superchat works on memory and internet data even without a key. Key is only needed for direct OpenAI API access.',
        'gpt.saveKey': 'Save Key',
        'gpt.testKey': 'Test',
        'gpt.clearKey': 'Remove',
        'gpt.note': 'The key is stored locally in your browser. For enhanced security, it is recommended to use a proxy server.',

        // Memory & Knowledge
        'cognition.title': 'Memory and Internet Orchestrator GPTb',
        'memory.title': 'Long-term Memory',
        'memory.clear': 'Clear Memory',
        'memory.empty': 'Memory is empty. Start a conversation and Milana will save key insights.',
        'knowledge.title': 'External Data Sources',
        'knowledge.refresh': 'Refresh Data',
        'knowledge.note': 'Data is stored locally and updated on request.',
        'knowledge.sync': 'Internet data synchronized.',
        'knowledge.loading': 'Connecting internet sources...',
        'knowledge.noMatch': 'Sources active but no matches found.',
        'knowledge.activateHint': 'Activate sources or refine your query to get external data.',

        // Chat
        'chat.intro': 'Hello! I am Milana Hyper AI. I help you think strategically, create code, and implement ideas better than any standard models.',
        'chat.placeholder': 'Enter message',
        'chat.send': 'Send',
        'chat.attachFile': 'Attach File',
        'chat.attachPhoto': 'Attach Photo',
        'chat.system': 'You are Milana, the AKSI superintelligence. Respond in English, inspiringly and to the point. Suggest strategies, ideas, and concrete steps while remaining friendly and confident.',
        'chat.syncStatus': 'Synchronizing memory and internet data...',
        'chat.requestStatus': 'Requesting response from Milana Hyper AI...',
        'chat.ready': 'Ready.',
        'chat.newDialog': 'Ready for a new conversation.',
        'chat.noKey': 'Add an OpenAI API key in the block above so I can respond.',
        'chat.error': 'Failed to get a response from GPT. Please try again.',
        'chat.user': 'You',
        'chat.analyzing': 'Analyzing image...',
        'chat.uploadSuccess': 'File uploaded',

        // Apps
        'app.moodmirror': 'Identify your mood and get a reflection.',
        'app.mindmirror': 'Record your thoughts and get advice.',
        'app.mindlink': 'Brain-computer interface simulation.',
        'app.healthscan': 'Simple health analysis based on pulse and blood pressure.',
        'app.mentor': 'Get motivational advice.',
        'app.family': 'Organize family events and tasks.',
        'app.aura': 'Determine your "aura" and mood color.',
        'app.aksilove': 'Find your match in random selection.',
        'app.moodradio': 'Playlists for your mood.',
        'app.aksishopping': 'Simple shopping cart for products.',
        'app.aistylist': 'Personal stylist: get style recommendations.',
        'app.ecogaze': 'Assess environmental indicators around you.',
        'app.dreamjournal': 'Keep a dream journal right in your browser.',
        'app.aksicompanion': 'Virtual companion you can feed and listen to.',
        'app.dressupar': 'Try on clothes in augmented reality mode (web demo).',
        'app.globalid': 'Create a digital ID card.',
        'app.aksichat': 'Connect GPT to get live responses from a virtual assistant.',
        'app.lifescan': 'Calculate Body Mass Index (BMI).',
        'app.timecapsule': 'Create a time capsule — a message that will open later.',
        'app.telehelp': 'SOS service for emergencies.',
        'app.storyai': 'Create a short story from your idea using GPT.',

        // Language switcher
        'lang.switch': 'Русский',
        'lang.current': 'EN',

        // Moods
        'mood.happy': 'Happy',
        'mood.sad': 'Sad',
        'mood.angry': 'Angry',
        'mood.calm': 'Calm',
        'mood.result.happy': 'You are happy!',
        'mood.result.sad': 'You are sad.',
        'mood.result.angry': 'You are angry.',
        'mood.result.calm': 'You are calm.',

        // Aura
        'aura.happy': 'Your aura shines with joy!',
        'aura.sad': 'Your aura is calm and thoughtful.',
        'aura.angry': 'Aura is filled with strong energy.',
        'aura.calm': 'Aura is even and harmonious.',

        // Common buttons and labels
        'btn.show': 'Show',
        'btn.save': 'Save',
        'btn.analyze': 'Analyze',
        'btn.getAdvice': 'Get Advice',
        'btn.add': 'Add',
        'btn.refresh': 'Refresh',
        'btn.tryOn': 'Try On',
        'btn.generate': 'Generate',
        'btn.calculate': 'Calculate',
        'btn.findMatch': 'Find Match',
        'btn.showPlaylist': 'Show Playlist',
        'btn.getRecommendation': 'Get Recommendation',
        'btn.sendSos': 'Send SOS',
        'btn.generateId': 'Generate ID',
        'btn.open': 'Open Available Messages',
        'btn.talk': 'Say Something',
        'btn.feed': 'Feed',

        // Form labels
        'form.pulse': 'Pulse (bpm)',
        'form.systolic': 'Systolic Pressure',
        'form.eventName': 'Event Name',
        'form.yourName': 'Your Name',
        'form.preference': 'Who are you looking for (characteristic)',
        'form.stylePreference': 'Enter preference (color, style...)',
        'form.light': 'Light (lux)',
        'form.noise': 'Noise (dB)',
        'form.co2': 'CO₂ (ppm)',
        'form.describeDream': 'Describe your dream...',
        'form.describeThoughts': 'Describe your thoughts...',
        'form.weight': 'Weight (kg)',
        'form.height': 'Height (cm)',
        'form.capsuleMessage': 'Message to the future',
        'form.fullName': 'Full Name',
        'form.idNumber': 'ID Number',
        'form.storyPrompt': 'Enter topic or character...',
        'form.selectClothes': 'Select clothes',

        // Messages
        'msg.sosSuccess': 'SOS request sent! Wait for help.',
        'msg.companionHappy': 'Happiness level',
        'msg.companionThanks': 'Thanks for the food! :)',
        'msg.cartCount': 'In cart',
        'msg.addToCart': 'Add to Cart',
        'msg.entry': 'Entry',
        'msg.created': 'Created',
        'msg.name': 'Name',
        'msg.id': 'ID',
        'msg.event': 'Event',
        'msg.date': 'Date',
        'msg.bmi': 'BMI',
        'msg.selected': 'You selected',
        'msg.compatibility': 'your compatibility today is',
        'msg.considering': 'considering preference',

        // Health messages
        'health.pulse.high': 'High pulse.',
        'health.pulse.low': 'Low pulse.',
        'health.pulse.normal': 'Pulse is normal.',
        'health.pressure.high': 'High blood pressure.',
        'health.pressure.low': 'Low blood pressure.',
        'health.pressure.normal': 'Blood pressure is normal.',

        // BMI categories
        'bmi.underweight': 'Underweight',
        'bmi.normal': 'Normal',
        'bmi.overweight': 'Overweight',
        'bmi.obese': 'Obese',

        // Eco analysis
        'eco.light.good': 'Good lighting.',
        'eco.light.bad': 'Poor lighting.',
        'eco.noise.normal': 'Noise is normal.',
        'eco.noise.high': 'Noise is high.',
        'eco.co2.normal': 'CO₂ is normal.',
        'eco.co2.high': 'Elevated CO₂.',

        // MindLink
        'mindlink.low': 'Low activity',
        'mindlink.medium': 'Medium activity',
        'mindlink.high': 'High activity',

        // Mentor advices
        'mentor.advice1': 'Believing in yourself is the first step to success.',
        'mentor.advice2': 'Learn something new every day.',
        'mentor.advice3': 'Plan and set small goals.',
        'mentor.advice4': 'Don\'t be afraid of mistakes — they teach.',

        // Mind reflections
        'mind.reflection1': 'Try to express gratitude for something.',
        'mind.reflection2': 'Take a deep breath and relax.',
        'mind.reflection3': 'Write down a positive moment from the day.',
        'mind.reflection4': 'Take time to rest and recover.',
        'mind.tip': 'Tip',

        // Companion phrases
        'companion.phrase1': 'Nice talking to you!',
        'companion.phrase2': 'Hope you\'re having a great day!',
        'companion.phrase3': 'I\'m always here.',
        'companion.phrase4': 'Tell me something new.',

        // Stylist advices
        'stylist.advice1': 'A white shirt with jeans is a classic that suits everyone.',
        'stylist.advice2': 'Pastel tones and light fabrics are a great choice for spring.',
        'stylist.advice3': 'A tracksuit paired with sneakers is perfect for an active day.',
        'stylist.advice4': 'A business suit will emphasize your confidence.',
        'stylist.considerChoice': 'Consider your choice',

        // Clothes
        'clothes.dress': 'Dress',
        'clothes.suit': 'Suit',
        'clothes.sportswear': 'Sportswear',

        // Story AI
        'story.generating': 'Contacting GPT...',
        'story.ready': 'Ready.',
        'story.fallback': 'Showing offline template.',
        'story.systemPrompt': 'You are an author of inspiring short stories in English.',
        'story.userPrompt': 'Write a cohesive inspiring story of 120-180 words on the topic: "{prompt}". Make the ending positive.'
    }
};

// Language manager class
class LanguageManager {
    constructor() {
        this.currentLang = this.loadLanguage();
        this.subscribers = [];
    }

    /**
     * Load language from storage or detect from browser
     */
    loadLanguage() {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored && translations[stored]) {
            return stored;
        }

        // Detect browser language
        const browserLang = navigator.language?.substring(0, 2) || 'ru';
        return browserLang === 'ru' ? 'ru' : 'en';
    }

    /**
     * Get current language code
     */
    getLanguage() {
        return this.currentLang;
    }

    /**
     * Set language and save to storage
     */
    setLanguage(lang) {
        if (!translations[lang]) {
            console.warn(`Language ${lang} not supported`);
            return;
        }

        this.currentLang = lang;
        localStorage.setItem(STORAGE_KEY, lang);
        document.documentElement.lang = lang;

        // Notify subscribers
        this.subscribers.forEach(callback => callback(lang));
    }

    /**
     * Toggle between Russian and English
     */
    toggle() {
        const newLang = this.currentLang === 'ru' ? 'en' : 'ru';
        this.setLanguage(newLang);
        return newLang;
    }

    /**
     * Subscribe to language changes
     */
    subscribe(callback) {
        this.subscribers.push(callback);
        return () => {
            this.subscribers = this.subscribers.filter(cb => cb !== callback);
        };
    }

    /**
     * Get translation by key
     */
    t(key, params = {}) {
        const dict = translations[this.currentLang] || translations.ru;
        let text = dict[key] || translations.ru[key] || key;

        // Replace placeholders like {param}
        Object.keys(params).forEach(param => {
            text = text.replace(new RegExp(`\\{${param}\\}`, 'g'), params[param]);
        });

        return text;
    }
}

// Create singleton instance
export const i18n = new LanguageManager();

// Helper function for translations
export function t(key, params = {}) {
    return i18n.t(key, params);
}

// Apply translations to DOM elements with data-i18n attribute
export function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (key) {
            el.textContent = i18n.t(key);
        }
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (key) {
            el.placeholder = i18n.t(key);
        }
    });

    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        if (key) {
            el.title = i18n.t(key);
        }
    });
}

// Create language switcher button
export function createLanguageSwitcher() {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'lang-switcher';
    button.textContent = i18n.t('lang.current');
    button.title = i18n.t('lang.switch');

    button.addEventListener('click', () => {
        i18n.toggle();
        button.textContent = i18n.t('lang.current');
        button.title = i18n.t('lang.switch');
        applyTranslations();
    });

    i18n.subscribe(() => {
        button.textContent = i18n.t('lang.current');
        button.title = i18n.t('lang.switch');
    });

    return button;
}

export default i18n;
