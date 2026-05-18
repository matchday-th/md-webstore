(function () {
    const STORAGE_KEY = "app_language";
    const DEFAULT_LANGUAGE = "en";
    const listeners = [];

    function normalizeLanguage(language) {
        return language === "th" ? "th" : "en";
    }

    function getLanguage() {
        return normalizeLanguage(localStorage.getItem(STORAGE_KEY) || DEFAULT_LANGUAGE);
    }

    function setLanguage(language) {
        const nextLanguage = normalizeLanguage(language);
        localStorage.setItem(STORAGE_KEY, nextLanguage);
        document.documentElement.lang = nextLanguage;
        listeners.forEach((listener) => listener(nextLanguage));
    }

    function onChange(listener) {
        listeners.push(listener);
    }

    function bindSelect(select) {
        if (!select) {
            return;
        }

        select.value = getLanguage();
        select.addEventListener("change", (event) => {
            setLanguage(event.target.value);
        });

        onChange((language) => {
            if (select.value !== language) {
                select.value = language;
            }
        });
    }

    function init(callback) {
        const language = getLanguage();
        document.documentElement.lang = language;
        if (callback) {
            callback(language);
            onChange(callback);
        }
    }

    window.EcomI18n = {
        getLanguage,
        setLanguage,
        bindSelect,
        init
    };
})();
