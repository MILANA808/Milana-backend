import { createGptIntegration } from './gpt.js';
import { createKnowledgeHub } from './knowledge.js';
import { createMemoryVault } from './memory.js';
import { createFreeTierEngine } from './free-tier.js';
import { i18n, t, applyTranslations, createLanguageSwitcher } from './i18n.js';
import { FileUploadManager, createUploadButtons, createFilePreview } from './file-upload.js';

document.addEventListener('DOMContentLoaded', () => {
    // Initialize language switcher
    const langSwitcher = createLanguageSwitcher();
    document.body.appendChild(langSwitcher);

    // Set initial HTML lang attribute
    document.documentElement.lang = i18n.getLanguage();

    // Apply initial translations
    applyTranslations();

    // Subscribe to language changes for DOM updates
    i18n.subscribe((lang) => {
        document.documentElement.lang = lang;
        applyTranslations();
    });

    const sections = document.querySelectorAll('.app-section');
    const navButtons = document.querySelectorAll('#sidebar button[data-target]');
    const newChatButton = document.getElementById('newChatButton');
    const launchAksichat = document.getElementById('launchAksichat');
    let resetChat = null;
    let chatInputElement = null;

    const highlightNewChat = (isActive) => {
        if (newChatButton) {
            newChatButton.classList.toggle('active', !!isActive);
        }
    };

    const showSection = (id) => {
        if (!id) return;
        let found = false;
        sections.forEach(section => {
            const match = section.id === id;
            section.style.display = match ? 'block' : 'none';
            if (match) found = true;
        });
        if (!found) return;
        navButtons.forEach(button => {
            button.classList.toggle('active', button.dataset.target === id);
        });
        highlightNewChat(id === 'aksichat');
    };

    window.showSection = showSection;

    if (newChatButton) {
        newChatButton.addEventListener('click', () => {
            showSection('aksichat');
            if (typeof resetChat === 'function') {
                resetChat({ greet: true });
            }
            if (chatInputElement) {
                chatInputElement.focus();
            }
            newChatButton.blur();
        });
    }

    navButtons.forEach(button => {
        button.addEventListener('click', () => showSection(button.dataset.target));
    });

    if (navButtons.length) {
        showSection(navButtons[0].dataset.target);
    }

    const knowledgeHub = createKnowledgeHub();
    const memoryVault = createMemoryVault();
    const freeTierEngine = createFreeTierEngine({ knowledgeHub, memoryVault });

    const gptIntegration = createGptIntegration({
        keyField: document.getElementById('gptApiKey'),
        saveButton: document.getElementById('gptSaveKey'),
        testButton: document.getElementById('gptTestKey'),
        clearButton: document.getElementById('gptClearKey'),
        statusField: document.getElementById('gptKeyStatus'),
        freeTier: freeTierEngine
    });

    const queryGPT = (...args) => gptIntegration.query(...args);
    const formatGptError = (error) => gptIntegration.formatError(error);

    const knowledgeSourcesList = document.getElementById('knowledgeSourcesList');
    const knowledgePreview = document.getElementById('knowledgePreview');
    const knowledgeStatus = document.getElementById('knowledgeStatus');
    const knowledgeRefreshButton = document.getElementById('knowledgeRefreshButton');
    const memoryStatus = document.getElementById('memoryStatus');
    const memoryClearButton = document.getElementById('memoryClearButton');

    const setKnowledgeStatus = (message, isError = false) => {
        if (!knowledgeStatus) return;
        knowledgeStatus.textContent = message || '';
        knowledgeStatus.style.color = isError ? '#ff8fb7' : '#d4c7ff';
    };

    const updateMemoryStatus = () => {
        if (!memoryStatus) return;
        const summary = memoryVault.recall({ limit: 6, maxLength: 900 });
        memoryStatus.textContent = summary
            ? `${t('memory.title')} Milana GPTb:\n${summary}`
            : t('memory.empty');
    };

    // Subscribe to language changes to update memory status
    i18n.subscribe(() => updateMemoryStatus());

    const renderKnowledgeSources = () => {
        if (!knowledgeSourcesList) return;
        knowledgeSourcesList.innerHTML = '';
        knowledgeHub.getConnectors().forEach((connector) => {
            const item = document.createElement('li');
            item.className = 'knowledge-source';

            const label = document.createElement('label');
            label.className = 'knowledge-source-label';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = connector.enabled;
            checkbox.addEventListener('change', () => {
                knowledgeHub.setConnectorEnabled(connector.id, checkbox.checked);
            });

            const title = document.createElement('span');
            title.className = 'knowledge-source-title';
            title.textContent = connector.label;

            const description = document.createElement('span');
            description.className = 'knowledge-source-description';
            description.textContent = connector.description;

            const textContainer = document.createElement('div');
            textContainer.className = 'knowledge-source-text';
            textContainer.appendChild(title);
            textContainer.appendChild(description);

            label.appendChild(checkbox);
            label.appendChild(textContainer);
            item.appendChild(label);
            knowledgeSourcesList.appendChild(item);
        });
    };

    knowledgeHub.subscribe(renderKnowledgeSources);
    renderKnowledgeSources();
    updateMemoryStatus();

    const formatKnowledgeEntries = (entries) => {
        if (!entries.length) {
            return 'Активируйте источники или уточните запрос, чтобы получить внешние данные.';
        }
        return entries.map((entry) => {
            if (entry.error) {
                return `⚠️ ${entry.label}: ${entry.error}`;
            }
            return `# ${entry.label}\n${entry.content}`;
        }).join('\n\n');
    };

    const refreshKnowledgePreview = async (query) => {
        if (!knowledgePreview) return { combinedText: '', entries: [], errors: [] };
        knowledgePreview.textContent = 'Подключаем интернет-источники...';
        try {
            const result = await knowledgeHub.gather(query, { limit: 5 });
            freeTierEngine.recordAggregation({
                topic: query,
                combinedText: result.combinedText,
                entries: result.entries,
                errors: result.errors
            });
            knowledgePreview.textContent = formatKnowledgeEntries(result.entries);
            if (result.errors.length) {
                setKnowledgeStatus(result.errors[0], true);
            } else if (result.entries.length) {
                setKnowledgeStatus('Интернет-данные синхронизированы.', false);
            } else {
                setKnowledgeStatus('Источники активны, но не нашли совпадений.', false);
            }
            return result;
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            knowledgePreview.textContent = `Ошибка агрегации данных: ${message}`;
            setKnowledgeStatus(message, true);
            freeTierEngine.recordAggregation({
                topic: query,
                combinedText: '',
                entries: [],
                errors: [message]
            });
            return { combinedText: '', entries: [], errors: [message] };
        }
    };

    if (knowledgeRefreshButton) {
        knowledgeRefreshButton.addEventListener('click', async () => {
            const query = chatInputElement?.value?.trim() || 'искусственный интеллект';
            await refreshKnowledgePreview(query);
        });
    }

    if (memoryClearButton) {
        memoryClearButton.addEventListener('click', () => {
            memoryVault.clear();
            updateMemoryStatus();
        });
    }

    refreshKnowledgePreview('искусственный интеллект');

    const moodMirrorButton = document.getElementById('moodMirrorButton');
    if (moodMirrorButton) {
        const select = document.getElementById('moodMirrorSelect');
        const display = document.getElementById('moodMirrorDisplay');
        moodMirrorButton.addEventListener('click', () => {
            const mood = select.value;
            let color = '';
            let text = '';
            switch (mood) {
                case 'happy': color = '#ffe066'; text = 'Вы счастливы!'; break;
                case 'sad': color = '#74c0fc'; text = 'Вы грустите.'; break;
                case 'angry': color = '#fa5252'; text = 'Вы злитесь.'; break;
                case 'calm': color = '#b2f2bb'; text = 'Вы спокойны.'; break;
            }
            display.style.backgroundColor = color;
            display.innerText = text;
        });
    }

    const mindMirrorSave = document.getElementById('mindMirrorSave');
    if (mindMirrorSave) {
        const reflections = [
            'Попробуйте выразить благодарность за что-то.',
            'Сделайте глубокий вдох и расслабьтесь.',
            'Запишите положительный момент из дня.',
            'Уделите время отдыху и восстановлению.'
        ];
        const entryField = document.getElementById('mindMirrorEntry');
        const entriesContainer = document.getElementById('mindMirrorEntries');
        const reflectionOutput = document.getElementById('mindMirrorReflection');

        const loadEntries = () => {
            const entries = JSON.parse(localStorage.getItem('mindEntries') || '[]');
            entriesContainer.innerHTML = '';
            entries.forEach((entry, index) => {
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = `<strong>Запись ${index + 1}</strong><p>${entry}</p>`;
                entriesContainer.appendChild(card);
            });
        };

        mindMirrorSave.addEventListener('click', () => {
            const text = entryField.value.trim();
            if (!text) return;
            const entries = JSON.parse(localStorage.getItem('mindEntries') || '[]');
            entries.push(text);
            localStorage.setItem('mindEntries', JSON.stringify(entries));
            entryField.value = '';
            loadEntries();
            const reflection = reflections[Math.floor(Math.random() * reflections.length)];
            reflectionOutput.innerText = `Совет: ${reflection}`;
        });

        loadEntries();
    }

    const mindLinkButton = document.getElementById('mindLinkButton');
    if (mindLinkButton) {
        const progress = document.getElementById('mindLinkProgress');
        const status = document.getElementById('mindLinkStatus');
        mindLinkButton.addEventListener('click', () => {
            const value = Math.floor(Math.random() * 101);
            progress.value = value;
            if (value < 33) status.innerText = 'Низкая активность';
            else if (value < 66) status.innerText = 'Средняя активность';
            else status.innerText = 'Высокая активность';
        });
    }

    const healthScanButton = document.getElementById('healthScanButton');
    if (healthScanButton) {
        healthScanButton.addEventListener('click', () => {
            const heart = parseInt(document.getElementById('healthPulse').value, 10);
            const sys = parseInt(document.getElementById('healthSystolic').value, 10);
            let message = '';
            if (heart > 100) message += 'Повышенный пульс. ';
            else if (heart < 60) message += 'Низкий пульс. ';
            else message += 'Пульс в норме. ';
            if (sys > 140) message += 'Высокое давление. ';
            else if (sys < 90) message += 'Низкое давление. ';
            else message += 'Давление в норме.';
            document.getElementById('healthResult').innerText = message.trim();
        });
    }

    const mentorButton = document.getElementById('mentorAdviceButton');
    if (mentorButton) {
        const advices = [
            'Верить в себя — первый шаг к успеху.',
            'Каждый день учитесь чему-то новому.',
            'Планируйте и ставьте маленькие цели.',
            'Не бойтесь ошибок — они учат.'
        ];
        const adviceOutput = document.getElementById('mentorAdvice');
        mentorButton.addEventListener('click', () => {
            const advice = advices[Math.floor(Math.random() * advices.length)];
            adviceOutput.innerText = advice;
        });
    }

    const familyAddButton = document.getElementById('familyAddButton');
    if (familyAddButton) {
        const nameField = document.getElementById('familyEventName');
        const dateField = document.getElementById('familyEventDate');
        const table = document.getElementById('familyEventsTable');

        const loadEvents = () => {
            const events = JSON.parse(localStorage.getItem('familyEvents') || '[]');
            table.innerHTML = '<tr><th>Событие</th><th>Дата</th></tr>';
            events.forEach(event => {
                const row = document.createElement('tr');
                row.innerHTML = `<td>${event.name}</td><td>${event.date}</td>`;
                table.appendChild(row);
            });
        };

        familyAddButton.addEventListener('click', () => {
            const name = nameField.value.trim();
            const date = dateField.value;
            if (!name || !date) return;
            const events = JSON.parse(localStorage.getItem('familyEvents') || '[]');
            events.push({ name, date });
            localStorage.setItem('familyEvents', JSON.stringify(events));
            nameField.value = '';
            dateField.value = '';
            loadEvents();
        });

        loadEvents();
    }

    const auraMoodButton = document.getElementById('auraMoodButton');
    if (auraMoodButton) {
        const select = document.getElementById('auraMoodSelect');
        const display = document.getElementById('auraMoodDisplay');
        auraMoodButton.addEventListener('click', () => {
            const mood = select.value;
            let color = '';
            let text = '';
            switch (mood) {
                case 'happy': color = '#ff922b'; text = 'Ваша аура сияет радостью!'; break;
                case 'sad': color = '#4dabf7'; text = 'Ваша аура спокойна и задумчива.'; break;
                case 'angry': color = '#ff6b6b'; text = 'Аура насыщена сильной энергией.'; break;
                case 'calm': color = '#69db7c'; text = 'Аура ровная и гармоничная.'; break;
            }
            display.style.backgroundColor = color;
            display.innerText = text;
        });
    }

    const loveMatchButton = document.getElementById('loveMatchButton');
    if (loveMatchButton) {
        const matches = ['Алексей', 'Ольга', 'Сергей', 'Мария', 'Иван', 'Екатерина'];
        loveMatchButton.addEventListener('click', () => {
            const name = document.getElementById('loveYourName').value.trim();
            const preference = document.getElementById('lovePreference').value.trim();
            const match = matches[Math.floor(Math.random() * matches.length)];
            const prefix = name ? `${name}, ` : '';
            const suffix = preference ? ` (учитывая предпочтение: ${preference})` : '';
            document.getElementById('loveMatchResult').innerText = `${prefix}ваша совместимость на сегодня: ${match}${suffix}`;
        });
    }

    const moodRadioButton = document.getElementById('moodRadioButton');
    if (moodRadioButton) {
        const playlists = {
            happy: ['Happy Song 1', 'Joyful Tune 2', 'Sunny Day'],
            sad: ['Melancholic Melody', 'Slow Ballad', 'Rainy Thoughts'],
            angry: ['Rock Anthem', 'Metal Fury', 'Energetic Beat'],
            calm: ['Peaceful Piano', 'Relaxing Waves', 'Soft Guitar']
        };
        const select = document.getElementById('moodRadioSelect');
        const list = document.getElementById('moodRadioList');
        moodRadioButton.addEventListener('click', () => {
            const mood = select.value;
            list.innerHTML = '';
            playlists[mood].forEach(song => {
                const item = document.createElement('li');
                item.textContent = song;
                list.appendChild(item);
            });
        });
    }

    const cartCount = document.getElementById('cartCount');
    const productList = document.getElementById('productList');
    if (cartCount && productList) {
        const products = [
            { name: 'Смартфон', price: 500 },
            { name: 'Наушники', price: 50 },
            { name: 'Ноутбук', price: 800 },
            { name: 'Фитнес-браслет', price: 100 }
        ];
        let cart = JSON.parse(localStorage.getItem('shopCart') || '[]');

        const updateCart = () => {
            cartCount.innerText = `В корзине: ${cart.length}`;
        };

        const renderProducts = () => {
            productList.innerHTML = '';
            products.forEach((product, index) => {
                const card = document.createElement('div');
                card.className = 'card';
                const title = document.createElement('p');
                title.innerHTML = `<strong>${product.name}</strong> — ${product.price}₽`;
                const button = document.createElement('button');
                button.type = 'button';
                button.textContent = 'Добавить в корзину';
                button.addEventListener('click', () => {
                    cart.push(product);
                    localStorage.setItem('shopCart', JSON.stringify(cart));
                    updateCart();
                });
                card.appendChild(title);
                card.appendChild(button);
                productList.appendChild(card);
            });
        };

        updateCart();
        renderProducts();
    }

    const stylistButton = document.getElementById('stylistButton');
    if (stylistButton) {
        const outfits = [
            'Белая рубашка с джинсами — классика, которая подходит всем.',
            'Пастельные тона и лёгкие ткани — отличный выбор для весны.',
            'Спортивный костюм сочетается с кроссовками для активного дня.',
            'Деловой костюм подчеркнёт вашу уверенность.'
        ];
        const output = document.getElementById('stylistAdvice');
        const preferenceField = document.getElementById('stylistPreference');
        stylistButton.addEventListener('click', () => {
            const advice = outfits[Math.floor(Math.random() * outfits.length)];
            const preference = preferenceField.value.trim();
            output.innerText = preference ? `${advice} Учтите ваш выбор: ${preference}.` : advice;
        });
    }

    const ecoAnalyzeButton = document.getElementById('ecoAnalyzeButton');
    if (ecoAnalyzeButton) {
        ecoAnalyzeButton.addEventListener('click', () => {
            const light = parseFloat(document.getElementById('ecoLight').value);
            const noise = parseFloat(document.getElementById('ecoNoise').value);
            const co2 = parseFloat(document.getElementById('ecoCO2').value);
            let result = '';
            result += light >= 300 && light <= 500 ? 'Хорошая освещённость. ' : 'Плохая освещённость. ';
            result += noise <= 50 ? 'Шум в норме. ' : 'Шум высокий. ';
            result += co2 <= 1000 ? 'CO₂ в норме.' : 'Повышенный CO₂.';
            document.getElementById('ecoResult').innerText = result.trim();
        });
    }

    const dreamSaveButton = document.getElementById('dreamSaveButton');
    if (dreamSaveButton) {
        const entryField = document.getElementById('dreamEntry');
        const container = document.getElementById('dreamEntries');

        const loadEntries = () => {
            const entries = JSON.parse(localStorage.getItem('dreamEntries') || '[]');
            container.innerHTML = '';
            entries.forEach((entry, index) => {
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = `<strong>Запись ${index + 1}</strong><p>${entry}</p>`;
                container.appendChild(card);
            });
        };

        dreamSaveButton.addEventListener('click', () => {
            const text = entryField.value.trim();
            if (!text) return;
            const entries = JSON.parse(localStorage.getItem('dreamEntries') || '[]');
            entries.push(text);
            localStorage.setItem('dreamEntries', JSON.stringify(entries));
            entryField.value = '';
            loadEntries();
        });

        loadEntries();
    }

    const companionTalkButton = document.getElementById('companionTalkButton');
    const companionFeedButton = document.getElementById('companionFeedButton');
    if (companionTalkButton && companionFeedButton) {
        let happiness = 50;
        const phrases = [
            'Приятно с вами общаться!',
            'Надеюсь, у вас хороший день!',
            'Я всегда рядом.',
            'Расскажите мне что-то новое.'
        ];
        const status = document.getElementById('companionStatus');
        const message = document.getElementById('companionMessage');

        const updateCompanion = () => {
            status.innerText = `Уровень радости: ${happiness}%`;
        };

        companionTalkButton.addEventListener('click', () => {
            const phrase = phrases[Math.floor(Math.random() * phrases.length)];
            message.innerText = phrase;
            happiness = Math.min(100, happiness + 5);
            updateCompanion();
        });

        companionFeedButton.addEventListener('click', () => {
            message.innerText = 'Спасибо за еду! :)';
            happiness = Math.min(100, happiness + 10);
            updateCompanion();
        });

        updateCompanion();
    }

    const dressUpButton = document.getElementById('dressUpButton');
    if (dressUpButton) {
        const select = document.getElementById('dressUpSelect');
        const result = document.getElementById('dressUpResult');
        dressUpButton.addEventListener('click', () => {
            const item = select.value;
            result.innerText = item ? `Вы выбрали: ${item}` : '';
        });
    }

    const globalIdButton = document.getElementById('globalIdButton');
    if (globalIdButton) {
        const nameField = document.getElementById('globalIdName');
        const numberField = document.getElementById('globalIdNumber');
        const card = document.getElementById('globalIdCard');
        globalIdButton.addEventListener('click', () => {
            const name = nameField.value.trim();
            const number = numberField.value.trim();
            if (!name || !number) return;
            card.innerHTML = `<p><strong>Имя:</strong> ${name}</p><p><strong>ID:</strong> ${number}</p>`;
        });
    }

    const chatSendButton = document.getElementById('chatSendButton');
    if (chatSendButton) {
        const input = document.getElementById('chatInput');
        const box = document.getElementById('chatBox');
        const chatStatus = document.getElementById('chatStatus');
        const getIntroMessage = () => t('chat.intro');
        const getSystemPrompt = () => t('chat.system');
        const chatHistory = [
            { role: 'system', content: getSystemPrompt() }
        ];
        chatInputElement = input;

        // File preview container
        let filePreviewContainer = document.getElementById('filePreviewContainer');
        if (!filePreviewContainer) {
            filePreviewContainer = document.createElement('div');
            filePreviewContainer.id = 'filePreviewContainer';
            filePreviewContainer.className = 'file-preview-container';
            // Insert before input area
            const aksichatSection = document.getElementById('aksichat');
            if (aksichatSection && input) {
                input.parentNode.insertBefore(filePreviewContainer, input);
            }
        }

        // Initialize file upload manager
        const uploadManager = new FileUploadManager({
            onUpload: (fileData) => {
                const preview = createFilePreview(fileData, () => {
                    const idx = uploadManager.getPendingFiles().indexOf(fileData);
                    if (idx > -1) {
                        uploadManager.removePendingFile(idx);
                    }
                    preview.remove();
                });
                filePreviewContainer.appendChild(preview);
            },
            onError: (error) => {
                setChatStatus(error, true);
            }
        });

        // Create upload buttons and insert them
        const inputParent = input?.parentNode;
        if (inputParent) {
            // Create input area wrapper
            const inputArea = document.createElement('div');
            inputArea.className = 'chat-input-area';

            // Add upload buttons
            const uploadButtons = createUploadButtons(uploadManager);
            inputArea.appendChild(uploadButtons.wrapper);

            // Move input to wrapper
            inputArea.appendChild(input);

            // Move send button to wrapper
            inputArea.appendChild(chatSendButton);

            // Replace original structure
            inputParent.appendChild(inputArea);
        }

        const appendMessage = (role, text, imageUrl = null) => {
            if (!box) return;
            const block = document.createElement('div');
            block.className = `chat-message ${role === 'user' ? 'from-user' : 'from-assistant'}`;

            const avatar = document.createElement('div');
            avatar.className = 'chat-avatar';
            avatar.textContent = role === 'user' ? t('chat.user') : 'AI';

            const bubble = document.createElement('div');
            bubble.className = 'chat-bubble';

            // Handle image + text
            if (imageUrl) {
                const img = document.createElement('img');
                img.src = imageUrl;
                img.alt = 'Uploaded image';
                bubble.appendChild(img);
                if (text) {
                    const textDiv = document.createElement('div');
                    textDiv.className = 'image-analysis';
                    textDiv.textContent = text;
                    bubble.appendChild(textDiv);
                }
            } else {
                bubble.textContent = text;
            }

            block.appendChild(avatar);
            block.appendChild(bubble);
            box.appendChild(block);
            box.scrollTop = box.scrollHeight;
        };

        const setChatStatus = (message, isError = false) => {
            if (!chatStatus) return;
            chatStatus.textContent = message || '';
            chatStatus.style.color = isError ? '#ff8fb7' : '#d4c7ff';
        };

        resetChat = ({ greet = false } = {}) => {
            chatHistory.splice(0); // Clear all
            chatHistory.push({ role: 'system', content: getSystemPrompt() });
            if (box) {
                box.innerHTML = '';
            }
            // Clear pending files
            uploadManager.clearPendingFiles();
            filePreviewContainer.innerHTML = '';

            if (greet) {
                const intro = getIntroMessage();
                appendMessage('assistant', intro);
                chatHistory.push({ role: 'assistant', content: intro });
                setChatStatus(t('chat.newDialog'));
            } else {
                setChatStatus('');
            }
            chatSendButton.disabled = false;
            updateMemoryStatus();
        };

        // Update system prompt on language change
        i18n.subscribe(() => {
            // Update system prompt in chat history
            if (chatHistory[0]?.role === 'system') {
                chatHistory[0].content = getSystemPrompt();
            }
        });

        resetChat({ greet: true });

        const sendMessage = async () => {
            const text = input?.value.trim();
            const pendingFiles = uploadManager.getPendingFiles();

            if (!text && pendingFiles.length === 0) return;

            // Get first pending image if any
            const imageFile = pendingFiles.find(f => f.type === 'image');

            // Show user message with image if present
            if (imageFile) {
                appendMessage('user', text || t('chat.uploadSuccess'), imageFile.previewUrl);
            } else if (text) {
                appendMessage('user', text);
            }

            if (input) input.value = '';
            chatSendButton.disabled = true;

            // Clear pending files and preview
            uploadManager.clearPendingFiles();
            filePreviewContainer.innerHTML = '';

            setChatStatus(t('chat.syncStatus'));

            try {
                const { combinedText } = await refreshKnowledgePreview(text || 'image analysis');
                const runtimeMessages = [...chatHistory];
                const memoryContext = memoryVault.recall({ limit: 6, maxLength: 900 });
                if (memoryContext) {
                    runtimeMessages.push({
                        role: 'system',
                        content: `${t('memory.title')} Milana GPTb:\n${memoryContext}`
                    });
                }
                if (combinedText) {
                    runtimeMessages.push({
                        role: 'system',
                        content: `External data:\n${combinedText}`
                    });
                }

                let userContent;
                if (imageFile) {
                    // For image, create multimodal message
                    const imagePrompt = text || 'Describe this image in detail.';
                    userContent = [
                        { type: 'text', text: imagePrompt },
                        {
                            type: 'image_url',
                            image_url: {
                                url: `data:${imageFile.mimeType};base64,${imageFile.base64}`,
                                detail: 'auto'
                            }
                        }
                    ];
                    setChatStatus(t('chat.analyzing'));
                } else {
                    userContent = text;
                }

                const userMessage = { role: 'user', content: userContent };
                runtimeMessages.push(userMessage);
                chatHistory.push({ role: 'user', content: text || '[Image uploaded]' });

                setChatStatus(t('chat.requestStatus'));
                const reply = await queryGPT(runtimeMessages, {
                    useFreeTier: !imageFile, // Use GPT-4o for images
                    model: imageFile ? 'gpt-4o' : undefined
                });
                chatHistory.push({ role: 'assistant', content: reply });
                appendMessage('assistant', reply);
                memoryVault.remember({ user: text || '[Image]', assistant: reply });
                updateMemoryStatus();
                setChatStatus(t('chat.ready'));
            } catch (error) {
                const message = formatGptError(error);
                setChatStatus(message, true);
                const fallback = error?.code === 'NO_KEY'
                    ? t('chat.noKey')
                    : t('chat.error');
                appendMessage('assistant', fallback);
                chatHistory.push({ role: 'assistant', content: fallback });
            } finally {
                chatSendButton.disabled = false;
                if (input) input.focus();
            }
        };

        chatSendButton.addEventListener('click', sendMessage);
        if (input) {
            input.addEventListener('keydown', (event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    sendMessage();
                }
            });
        }

        if (launchAksichat) {
            launchAksichat.addEventListener('click', () => {
                showSection('aksichat');
                if (input) input.focus();
            });
        }
    }

    const lifeCalcButton = document.getElementById('lifeCalcButton');
    if (lifeCalcButton) {
        lifeCalcButton.addEventListener('click', () => {
            const weight = parseFloat(document.getElementById('lifeWeight').value);
            const height = parseFloat(document.getElementById('lifeHeight').value) / 100;
            if (!weight || !height) return;
            const bmi = weight / (height * height);
            let category = '';
            if (bmi < 18.5) category = 'Недостаток веса';
            else if (bmi < 25) category = 'Норма';
            else if (bmi < 30) category = 'Избыточный вес';
            else category = 'Ожирение';
            document.getElementById('lifeBmiResult').innerText = `ИМТ: ${bmi.toFixed(1)} — ${category}`;
        });
    }

    const capsuleSaveButton = document.getElementById('capsuleSaveButton');
    const capsuleOpenButton = document.getElementById('capsuleOpenButton');
    if (capsuleSaveButton && capsuleOpenButton) {
        const messageField = document.getElementById('capsuleMessage');
        const dateField = document.getElementById('capsuleDate');
        const container = document.getElementById('capsuleList');

        const loadCapsules = () => JSON.parse(localStorage.getItem('timeCapsules') || '[]');

        const renderCapsules = () => {
            const now = new Date();
            container.innerHTML = '';
            loadCapsules().forEach(capsule => {
                const openDate = new Date(capsule.date);
                if (openDate <= now) {
                    const card = document.createElement('div');
                    card.className = 'card';
                    card.innerHTML = `<p>${capsule.msg}</p><small>Дата создания: ${capsule.date}</small>`;
                    container.appendChild(card);
                }
            });
        };

        capsuleSaveButton.addEventListener('click', () => {
            const message = messageField.value.trim();
            const date = dateField.value;
            if (!message || !date) return;
            const capsules = loadCapsules();
            capsules.push({ msg: message, date });
            localStorage.setItem('timeCapsules', JSON.stringify(capsules));
            messageField.value = '';
            dateField.value = '';
        });

        capsuleOpenButton.addEventListener('click', renderCapsules);
    }

    const telehelpButton = document.getElementById('telehelpButton');
    if (telehelpButton) {
        telehelpButton.addEventListener('click', () => {
            document.getElementById('telehelpResult').innerText = 'Запрос SOS отправлен! Дождитесь помощи.';
        });
    }

    const storyButton = document.getElementById('storyButton');
    if (storyButton) {
        const templates = [
            'Однажды {prompt}, и это привело к удивительному приключению, полному неожиданных поворотов.',
            'История о {prompt} началась в туманное утро, когда мир перевернулся с ног на голову.',
            '{prompt} — герой, который доказал, что даже самые смелые мечты могут стать реальностью.',
            'В далёком королевстве жил {prompt}, и однажды он нашёл секрет, изменивший всё.'
        ];
        const promptField = document.getElementById('storyPrompt');
        const output = document.getElementById('storyOutput');
        const storyStatus = document.getElementById('storyStatus');

        const setStoryStatus = (message, isError = false) => {
            if (!storyStatus) return;
            storyStatus.textContent = message || '';
            storyStatus.style.color = isError ? '#ff8fb7' : '#d4c7ff';
        };

        storyButton.addEventListener('click', async () => {
            const prompt = promptField?.value.trim();
            if (!prompt) return;
            setStoryStatus('Обращаемся к GPT...');
            storyButton.disabled = true;

            try {
                const story = await queryGPT([
                    { role: 'system', content: 'Ты — автор вдохновляющих коротких историй на русском языке.' },
                    { role: 'user', content: `Напиши цельный вдохновляющий рассказ объёмом 120–180 слов по теме: "${prompt}". Сделай финал позитивным.` }
                ], { temperature: 0.8 });
                if (output) output.textContent = story;
                setStoryStatus('Готово.');
            } catch (error) {
                const message = formatGptError(error);
                setStoryStatus(`${message} Показан офлайн-шаблон.`, true);
                const template = templates[Math.floor(Math.random() * templates.length)];
                if (output) output.textContent = template.replace('{prompt}', prompt);
            } finally {
                storyButton.disabled = false;
            }
        });
    }
});
