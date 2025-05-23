import React, { useState, useEffect, useRef } from "react";
import { useTranslation } from 'react-i18next';
import { Globe, ChevronDown, Stethoscope } from 'lucide-react';
import { Link } from 'react-router-dom';

const Header = () => {
  const { t, i18n } = useTranslation();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const languages = [
    { code: 'en', name: t('languages.en', 'English') },
    { code: 'hi', name: t('languages.hi', 'हिन्दी') },
    { code: 'bn', name: t('languages.bn', 'বাংলা') },
    { code: 'te', name: t('languages.te', 'తెలుగు') },
    { code: 'mr', name: t('languages.mr', 'मराठी') },
    { code: 'ta', name: t('languages.ta', 'தமிழ்') },
    { code: 'gu', name: t('languages.gu', 'ગુજરાતી') },
    { code: 'kn', name: t('languages.kn', 'ಕನ್ನಡ') },
    { code: 'ml', name: t('languages.ml', 'മലയാളം') }
  ];

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    setDropdownOpen(false);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [dropdownRef]);

  const currentLanguageDisplay = languages.find(lang => lang.code === i18n.language)?.name 
                              || t('header.selectLanguage', 'Select Language');

  return (
    <header className="bg-gray-800 text-white p-3 sm:p-4 fixed w-full top-0 z-50 shadow-lg">
      <div className="container mx-auto flex justify-between items-center">
        <Link to="/" className="text-xl sm:text-2xl font-bold">{t('header.title')}</Link>
        <nav className="flex items-center space-x-2 sm:space-x-4">
          <Link 
            to="/chatbot"
            className="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-3 sm:px-4 rounded inline-flex items-center text-sm sm:text-base"
          >
            <Stethoscope className="mr-2 h-4 w-4 sm:h-5 sm:w-5" />
            {t('header.symptomChecker')}
          </Link>
          <div className="relative" ref={dropdownRef}>
            <button 
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="bg-gray-700 hover:bg-gray-600 text-white font-semibold py-2 px-3 sm:px-4 rounded inline-flex items-center text-sm sm:text-base"
            >
              <Globe className="mr-2 h-4 w-4 sm:h-5 sm:w-5" />
              <span>{currentLanguageDisplay}</span>
              <ChevronDown className={`ml-2 h-4 w-4 sm:h-5 sm:w-5 transform transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`} />
            </button>
            {dropdownOpen && (
              <ul className="absolute right-0 mt-2 py-1 w-40 sm:w-48 bg-white text-gray-800 rounded-md shadow-xl z-10 overflow-hidden">
                {languages.map((lang) => (
                  <li key={lang.code}>
                    <button
                      onClick={() => changeLanguage(lang.code)}
                      className={`w-full text-left px-3 sm:px-4 py-2 text-sm sm:text-base hover:bg-gray-100 ${i18n.language === lang.code ? 'font-bold bg-gray-100' : ''}`}
                    >
                      {lang.name}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
};

export default Header;
