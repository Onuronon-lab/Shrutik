import React from 'react';
import { useTranslation } from 'react-i18next';

const LanguageToggle = () => {
    const { i18n } = useTranslation();

    const toggleLanguage = () => {
        const newLang = i18n.language === 'en' ? 'bn' : 'en';
        i18n.changeLanguage(newLang);
        localStorage.setItem('appLanguage', newLang);
    };

    return (
        <button
            onClick={toggleLanguage}
            style={{
                padding: '8px 16px',
                borderRadius: '8px',
                border: '1px solid #ccc',
                cursor: 'pointer',
                backgroundColor: '#f9f9f9',
                minWidth: '90px',
                textAlign: 'center',
                display: 'inline-block',
            }}
        >
            {i18n.language === 'en' ? '🇬🇧 Eng' : '🇧🇩 Ban'}{' '}
        </button>
    );
};

export default LanguageToggle;
