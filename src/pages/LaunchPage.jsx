import React from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { LogIn, ShieldCheck, Users, Activity } from 'lucide-react';

const LaunchPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const handleLoginRedirect = () => {
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-100 via-indigo-50 to-purple-100 flex flex-col items-center justify-center p-4">
      <header className="text-center mb-12 animate-fadeInUp">
        <h1 className="text-5xl md:text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-700 mb-4">
          {t('launchPage.title', 'Welcome to HealthConnect')}
        </h1>
        <p className="text-xl md:text-2xl text-gray-700 max-w-3xl mx-auto">
          {t('launchPage.subtitle', 'Your Comprehensive Platform for Seamless Doctor-Patient Interaction and Health Management.')}
        </p>
      </header>

      <main className="grid md:grid-cols-2 gap-8 max-w-5xl w-full mb-12">
        <div className="bg-white p-8 rounded-xl shadow-xl transform hover:scale-105 transition-transform duration-300 animate-slideInLeft">
          <h2 className="text-3xl font-bold text-indigo-700 mb-4 flex items-center">
            <ShieldCheck size={32} className="mr-3 text-indigo-500" />
            {t('launchPage.forPatientsTitle', 'For Patients')}
          </h2>
          <p className="text-gray-600 mb-3">
            {t('launchPage.forPatientsDesc1', 'Easily connect with healthcare professionals, manage your appointments, and access your medical records securely.')}
          </p>
          <ul className="list-disc list-inside text-gray-600 space-y-1">
            <li>{t('launchPage.patientFeature1', 'Symptom Checker & AI Chatbot')}</li>
            <li>{t('launchPage.patientFeature2', 'Securely Upload Prescriptions & Reports')}</li>
            <li>{t('launchPage.patientFeature3', 'Book Appointments Online')}</li>
            <li>{t('launchPage.patientFeature4', 'Multilingual Support')}</li>
          </ul>
        </div>

        <div className="bg-white p-8 rounded-xl shadow-xl transform hover:scale-105 transition-transform duration-300 animate-slideInRight">
          <h2 className="text-3xl font-bold text-purple-700 mb-4 flex items-center">
            <Users size={32} className="mr-3 text-purple-500" />
            {t('launchPage.forDoctorsTitle', 'For Doctors')}
          </h2>
          <p className="text-gray-600 mb-3">
            {t('launchPage.forDoctorsDesc1', 'Streamline your consultations, manage patient records efficiently, and leverage AI-powered diagnostic support.')}
          </p>
          <ul className="list-disc list-inside text-gray-600 space-y-1">
            <li>{t('launchPage.doctorFeature1', 'Efficient Patient Management')}</li>
            <li>{t('launchPage.doctorFeature2', 'AI-Assisted Diagnosis')}</li>
            <li>{t('launchPage.doctorFeature3', 'Secure Data Handling')}</li>
            <li>{t('launchPage.doctorFeature4', 'Teleconsultation Ready')}</li>
          </ul>
        </div>
      </main>

      <div className="text-center animate-fadeInUp animation-delay-600">
        <button
          onClick={handleLoginRedirect}
          className="bg-gradient-to-r from-blue-600 to-indigo-700 hover:from-blue-700 hover:to-indigo-800 text-white font-semibold py-4 px-10 rounded-lg shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 text-xl inline-flex items-center focus:outline-none focus:ring-4 focus:ring-indigo-300"
        >
          <LogIn size={24} className="mr-3" />
          {t('launchPage.loginButton', 'Access Your Account')}
        </button>
      </div>

      <footer className="mt-16 text-center text-gray-600 animate-fadeInUp animation-delay-900">
        <p>&copy; {new Date().getFullYear()} {t('launchPage.footerText', 'HealthConnect. All rights reserved.')}</p>
        <p className="text-sm">
          {t('launchPage.tagline', 'Bridging Gaps, Building Healthier Futures.')}
        </p>
      </footer>

      <style jsx>{`
        .animation-delay-600 { animation-delay: 0.6s; }
        .animation-delay-900 { animation-delay: 0.9s; }
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideInLeft {
          from { opacity: 0; transform: translateX(-30px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes slideInRight {
          from { opacity: 0; transform: translateX(30px); }
          to { opacity: 1; transform: translateX(0); }
        }
        .animate-fadeInUp { animation: fadeInUp 0.5s ease-out forwards; }
        .animate-slideInLeft { animation: slideInLeft 0.5s ease-out 0.2s forwards; }
        .animate-slideInRight { animation: slideInRight 0.5s ease-out 0.4s forwards; }
      `}</style>
    </div>
  );
};

export default LaunchPage;
