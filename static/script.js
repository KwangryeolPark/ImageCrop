document.addEventListener('DOMContentLoaded', () => {
    const languageList = document.querySelector('.language-list');
    const confirmButton = document.getElementById('confirm-language-button');
    let selectedLang = 'en'; // Default

    // 언어 선택 UI 초기화
    const initializeSelector = async () => {
        const browserLang = navigator.language.slice(0, 2);
        const supportedLangs = ['ko', 'en', 'ja', 'zh', 'de', 'fr', 'ru'];
        const initialLang = supportedLangs.includes(browserLang) ? browserLang : 'en';
        await applyTranslations(initialLang);
        const defaultLangItem = document.querySelector(`.language-list li[data-lang="${initialLang}"]`);
        if (defaultLangItem) {
            defaultLangItem.classList.add('active');
            selectedLang = initialLang;
        }
    };

    // 번역 적용 함수
    const applyTranslations = async (langCode) => {
        try {
            const response = await fetch(`/locales/${langCode}.json`);
            const translations = await response.json();
            document.querySelectorAll('[data-i18n-key]').forEach(el => {
                const key = el.getAttribute('data-i18n-key');
                if (translations[key]) {
                    el.textContent = translations[key];
                }
            });
            // Handle placeholder translations
            document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
                const key = el.getAttribute('data-i18n-placeholder');
                if (translations[key]) {
                    el.placeholder = translations[key];
                }
            });
            document.title = translations['selectLanguage'] || 'Select Language';
        } catch (error) {
            console.error(`Could not load translations for ${langCode}`, error);
        }
    };

    // 언어 목록 클릭 이벤트
    languageList.addEventListener('click', (e) => {
        if (e.target.tagName === 'LI') {
            document.querySelectorAll('.language-list li').forEach(li => li.classList.remove('active'));
            e.target.classList.add('active');
            selectedLang = e.target.dataset.lang;
            applyTranslations(selectedLang);
        }
    });

    // 확인 버튼 클릭 이벤트
    confirmButton.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/save-language', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ language: selectedLang })
            });
            if (response.ok) {
                window.location.href = '/cropper';
            } else {
                alert('언어 설정 저장에 실패했습니다.');
            }
        } catch (error) {
            console.error("Error saving language:", error);
            alert('오류가 발생했습니다.');
        }
    });

    // 실행 시작 - 언어 선택기 초기화
    initializeSelector();
});