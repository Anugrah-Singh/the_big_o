import React, { useState, useEffect, useRef } from "react";
import { useTranslation } from 'react-i18next';
import { Globe, ChevronDown, Stethoscope, LogIn, LogOut, User, Heart } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Header = () => {
  const { t, i18n } = useTranslation();
  const { isAuthenticated, logout, user } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  const userDropdownRef = useRef(null);

  const languages = [
    { code: 'en', name: t('languages.en', 'English'), flag: '🇺🇸' },
    { code: 'hi', name: t('languages.hi', 'हिन्दी'), flag: '🇮🇳' },
    { code: 'bn', name: t('languages.bn', 'বাংলা'), flag: '🇧🇩' },
    { code: 'te', name: t('languages.te', 'తెలుగు'), flag: '🇮🇳' },
    { code: 'mr', name: t('languages.mr', 'मराठी'), flag: '🇮🇳' },
    { code: 'ta', name: t('languages.ta', 'தமிழ்'), flag: '🇮🇳' },
    { code: 'gu', name: t('languages.gu', 'ગુજરાતી'), flag: '🇮🇳' },
    { code: 'kn', name: t('languages.kn', 'ಕನ್ನಡ'), flag: '🇮🇳' },
    { code: 'ml', name: t('languages.ml', 'മലയാളം'), flag: '🇮🇳' }
  ];

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    setDropdownOpen(false);
  };

  const handleLogout = () => {
    logout();
    setUserDropdownOpen(false);
  };

  // Close dropdowns when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
      if (userDropdownRef.current && !userDropdownRef.current.contains(event.target)) {
        setUserDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [dropdownRef, userDropdownRef]);

  const currentLanguage = languages.find(lang => lang.code === i18n.language);
  const currentLanguageDisplay = currentLanguage?.name || t('header.selectLanguage', 'Select Language');
  const currentLanguageFlag = currentLanguage?.flag || '🌐';

  return (
    <header className="bg-gradient-to-r from-slate-900 via-purple-900 to-slate-900 text-white fixed w-full top-0 z-50 shadow-2xl backdrop-blur-md border-b border-white/10">
      <div className="container mx-auto px-4 py-3">
        <div className="flex justify-between items-center">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="bg-gradient-to-r from-blue-400 to-purple-500 p-2 rounded-xl group-hover:shadow-lg group-hover:shadow-blue-500/25 transition-all duration-300">
              <Heart className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              {t('header.title', 'ArogyaDhara')}
            </span>
          </Link>

          {/* Navigation */}
          <nav className="flex items-center space-x-2 sm:space-x-4">
            {/* Symptom Checker Button */}
            <Link
              to="/chatbot"
              className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-semibold py-2.5 px-4 sm:px-5 rounded-xl shadow-lg hover:shadow-blue-500/25 inline-flex items-center text-sm sm:text-base transition-all duration-300 transform hover:scale-105"
            >
              <Stethoscope className="mr-2 h-4 w-4 sm:h-5 sm:w-5" />
              <span className="hidden sm:inline">{t('header.symptomChecker', 'Symptom Checker')}</span>
              <span className="sm:hidden">{t('header.check', 'Check')}</span>
            </Link>

            {/* User Authentication */}
            {isAuthenticated ? (
              <div className="relative" ref={userDropdownRef}>
                <button 
                  onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                  className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold py-2.5 px-4 rounded-xl shadow-lg hover:shadow-green-500/25 inline-flex items-center text-sm sm:text-base transition-all duration-300 transform hover:scale-105"
                >
                  <User className="mr-2 h-4 w-4 sm:h-5 sm:w-5" />
                  <span className="hidden sm:inline">{user?.username || t('header.profile', 'Profile')}</span>
                  <ChevronDown className={`ml-2 h-4 w-4 transform transition-transform duration-200 ${userDropdownOpen ? 'rotate-180' : ''}`} />
                </button>
                {userDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white/95 backdrop-blur-md text-gray-800 rounded-2xl shadow-2xl border border-white/20 overflow-hidden animate-fadeInUp">
                    <div className="p-3 border-b border-gray-200">
                      <p className="text-sm text-gray-600">{t('header.welcomeBack', 'Welcome back')}</p>
                      <p className="font-semibold">{user?.username}</p>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-4 py-3 text-sm hover:bg-red-50 flex items-center text-red-600 transition-colors duration-200"
                    >
                      <LogOut className="mr-2 h-4 w-4" />
                      {t('header.logout', 'Logout')}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <Link
                to="/login"
                className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold py-2.5 px-4 sm:px-5 rounded-xl shadow-lg hover:shadow-green-500/25 inline-flex items-center text-sm sm:text-base transition-all duration-300 transform hover:scale-105"
              >
                <LogIn className="mr-2 h-4 w-4 sm:h-5 sm:w-5" />
                <span className="hidden sm:inline">{t('header.login', 'Login')}</span>
                <span className="sm:hidden">{t('header.loginShort', 'Login')}</span>
              </Link>
            )}

            {/* Language Selector */}
            <div className="relative" ref={dropdownRef}>
              <button 
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="bg-white/10 hover:bg-white/20 backdrop-blur-md text-white font-semibold py-2.5 px-4 rounded-xl border border-white/20 shadow-lg hover:shadow-white/10 inline-flex items-center text-sm sm:text-base transition-all duration-300 transform hover:scale-105"
              >
                <Globe className="mr-2 h-4 w-4 sm:h-5 sm:w-5" />
                <span className="mr-1">{currentLanguageFlag}</span>
                <span className="hidden sm:inline">{currentLanguageDisplay}</span>
                <ChevronDown className={`ml-2 h-4 w-4 transform transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`} />
              </button>
              {dropdownOpen && (
                <div className="absolute right-0 mt-2 w-52 bg-white/95 backdrop-blur-md text-gray-800 rounded-2xl shadow-2xl border border-white/20 overflow-hidden animate-fadeInUp">
                  <div className="p-2">
                    {languages.map((lang) => (
                      <button
                        key={lang.code}
                        onClick={() => changeLanguage(lang.code)}
                        className={`w-full text-left px-4 py-3 text-sm rounded-xl transition-all duration-200 flex items-center space-x-3 ${
                          i18n.language === lang.code 
                            ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg' 
                            : 'hover:bg-gray-100'
                        }`}
                      >
                        <span className="text-lg">{lang.flag}</span>
                        <span className="font-medium">{lang.name}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
