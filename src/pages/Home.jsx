import React from 'react';
import { useTranslation } from 'react-i18next';
import ChatBot from '../components/ChatBot'; // Import the ChatBot component

const Home = () => {
  const { t } = useTranslation();

  return (
    <div className="bg-[#f5f9fc] min-h-screen flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 pt-16">
      <div className="container mx-auto flex flex-col lg:flex-row items-center justify-between gap-12 py-12 lg:py-24">
        {/* Text Content */}
        <div className="lg:w-1/2 text-center lg:text-left">
          <p className="text-lg text-gray-600 mb-2">{t('homePage.careSubtitle')}</p>
          <h1 className="text-5xl lg:text-6xl font-bold text-gray-800 mb-4">
            {t('homePage.mainTitle').split('&')[0]}& <br /> {t('homePage.mainTitle').split('&')[1]}
          </h1>
          <p className="text-gray-700 mb-8 leading-relaxed">
            {t('homePage.description')}
          </p>
          {/* <button className="bg-gradient-to-r from-blue-500 to-blue-700 text-white px-10 py-4 rounded-md text-lg font-medium shadow-lg hover:scale-105 transition-transform focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-opacity-75">
            {t('homePage.appointmentButton')}
          </button> */}
        </div>

        {/* Image Content */}
        <div className="lg:w-1/2 mt-10 lg:mt-0 flex justify-center">
          {/* Placeholder for the image. Replace with your actual image component or path */}
          <img 
            src="src/assets/hero.jpg" 
            alt="Doctor attending to a patient in a hospital bed" 
            className="rounded-lg shadow-xl max-w-full h-auto align-middle border-none"
          />
        </div>
      </div>

      {/* ChatBot Component */}
      {/* <div className="max-w-2xl mx-auto mt-8">
        <ChatBot />
      </div> */}

      {/* Additional Content Placeholder */}
      {/* <div className="mt-8 md:mt-12 text-center">
        <h2 className="text-xl md:text-2xl font-semibold mb-3 md:mb-4">{t('home.additional_content_header')}</h2>
        <p className="text-sm md:text-base">{t('home.additional_content_placeholder')}</p>
      </div> */}
    </div>
  );
};

export default Home;
