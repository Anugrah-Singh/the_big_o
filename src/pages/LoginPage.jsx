import React, { useState } from 'react'; // Removed useContext
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { User, Shield, KeyRound } from 'lucide-react';

// Hardcoded credentials (replace with actual authentication in a real app)
const HARDCODED_PATIENT_ID = 'patient123';
const HARDCODED_PATIENT_PASSWORD = 'password';
const HARDCODED_DOCTOR_ID = 'doctor789';
const HARDCODED_DOCTOR_PASSWORD = 'docpassword';

const LoginPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { login: patientLogin } = useAuth(); // Changed to useAuth

  const [loginType, setLoginType] = useState(null); // 'patient' or 'doctor'
  const [username, setUsername] = useState(''); // Can be patientId or doctorId
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLoginTypeSelection = (type) => {
    setLoginType(type);
    setError('');
    setUsername('');
    setPassword('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (!username.trim() || !password.trim()) {
      setError(t('loginPage.error_empty_fields', 'Please enter ID and Password.'));
      return;
    }

    if (loginType === 'patient') {
      if (username === HARDCODED_PATIENT_ID && password === HARDCODED_PATIENT_PASSWORD) {
        console.log('Patient login successful');
        patientLogin({ username }); // Simulate successful patient login using AuthContext
        navigate('/home'); // Redirect to home page for patients
      } else {
        setError(t('loginPage.error_invalid_patient_credentials', 'Invalid Patient ID or Password.'));
      }
    } else if (loginType === 'doctor') {
      if (username === HARDCODED_DOCTOR_ID && password === HARDCODED_DOCTOR_PASSWORD) {
        console.log('Doctor login successful');
        // For doctor login, redirect to external URL
        window.location.href = 'http://192.168.28.221:5173/';
      } else {
        setError(t('loginPage.error_invalid_doctor_credentials', 'Invalid Doctor ID or Password.'));
      }
    }
  };

  if (!loginType) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-2xl border border-blue-100">
          <div className="text-center">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Shield size={40} className="text-blue-600" />
            </div>
            <h2 className="text-3xl font-extrabold text-gray-900">
              {t('loginPage.selectLoginTypeTitle', 'Select Login Type')}
            </h2>
            <p className="mt-2 text-gray-600">{t('loginPage.selectLoginTypeSubtitle', 'Choose how you want to access the platform')}</p>
          </div>
          <div className="mt-8 space-y-4">
            <button
              onClick={() => handleLoginTypeSelection('patient')}
              className="group relative w-full flex items-center justify-center py-4 px-6 border-2 border-blue-200 text-lg font-medium rounded-xl text-blue-700 bg-blue-50 hover:bg-blue-100 hover:border-blue-300 focus:outline-none focus:ring-4 focus:ring-blue-500/20 transition-all duration-200 transform hover:scale-105"
            >
              <User className="mr-3 h-6 w-6" />
              <div className="text-left">
                <div className="font-semibold">{t('loginPage.patientLoginButton', 'Patient Login')}</div>
                <div className="text-sm text-blue-600">{t('loginPage.patientLoginDesc', 'Access your health records and consultations')}</div>
              </div>
            </button>
            <button
              onClick={() => handleLoginTypeSelection('doctor')}
              className="group relative w-full flex items-center justify-center py-4 px-6 border-2 border-green-200 text-lg font-medium rounded-xl text-green-700 bg-green-50 hover:bg-green-100 hover:border-green-300 focus:outline-none focus:ring-4 focus:ring-green-500/20 transition-all duration-200 transform hover:scale-105"
            >
              <Shield className="mr-3 h-6 w-6" />
              <div className="text-left">
                <div className="font-semibold">{t('loginPage.doctorLoginButton', 'Doctor Login')}</div>
                <div className="text-sm text-green-600">{t('loginPage.doctorLoginDesc', 'Manage patients and medical consultations')}</div>
              </div>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-2xl border border-blue-100">
        <button 
            onClick={() => setLoginType(null)} 
            className="text-sm text-blue-600 hover:text-blue-800 mb-4 inline-flex items-center font-medium transition-colors"
        >
          &larr; {t('loginPage.backButton', 'Back to login type selection')}
        </button>
        <div className="text-center">
          <div className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 ${
            loginType === 'patient' 
              ? 'bg-gradient-to-br from-blue-100 to-blue-200' 
              : 'bg-gradient-to-br from-green-100 to-green-200'
          }`}>
            {loginType === 'patient' ? (
              <User size={40} className="text-blue-600" />
            ) : (
              <Shield size={40} className="text-green-600" />
            )}
          </div>
          <h2 className="text-3xl font-extrabold text-gray-900">
            {loginType === 'patient' ? t('loginPage.patientLoginTitle', 'Patient Login') : t('loginPage.doctorLoginTitle', 'Doctor Login')}
          </h2>
          <p className="mt-2 text-gray-600">
            {loginType === 'patient' 
              ? t('loginPage.patientLoginSubtitle', 'Sign in to access your health dashboard') 
              : t('loginPage.doctorLoginSubtitle', 'Sign in to manage your patients')
            }
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <KeyRound className="h-5 w-5 text-red-400" />
                </div>
                <div className="ml-3">
                  <p className="text-red-800 font-medium">{error}</p>
                </div>
              </div>
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                {loginType === 'patient' ? t('loginPage.patientIdLabel', 'Patient ID') : t('loginPage.doctorIdLabel', 'Doctor ID')}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  className="block w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-200 sm:text-sm"
                  placeholder={loginType === 'patient' ? t('loginPage.patientIdPlaceholder', 'Enter your Patient ID') : t('loginPage.doctorIdPlaceholder', 'Enter your Doctor ID')}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                {t('loginPage.passwordLabel', 'Password')}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <KeyRound className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  className="block w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-200 sm:text-sm"
                  placeholder={t('loginPage.passwordPlaceholder', 'Enter your password')}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>
          </div>

          <div>
            <button
              type="submit"
              className={`group relative w-full flex justify-center py-4 px-6 border border-transparent text-lg font-semibold rounded-xl text-white transition-all duration-200 transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-offset-2 shadow-lg hover:shadow-xl ${
                loginType === 'patient' 
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 focus:ring-blue-500/20' 
                  : 'bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 focus:ring-green-500/20'
              }`}
            >
              {t('loginPage.loginButton', 'Sign in')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
