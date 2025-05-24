import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

// Hardcoded credentials (replace with actual authentication in a real app)
const HARDCODED_PATIENT_ID = 'patient123';
const HARDCODED_PASSWORD = 'password';

const LoginPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [patientId, setPatientId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    setError(''); // Clear previous errors

    if (!patientId.trim() || !password.trim()) {
      setError(t('loginPage.error_empty_fields', 'Please enter Patient ID and Password.'));
      return;
    }

    if (patientId === HARDCODED_PATIENT_ID && password === HARDCODED_PASSWORD) {
      // Simulate successful login
      console.log('Login successful');
      // In a real app, you would set some authentication state (e.g., token, user object in context/redux)
      navigate('/'); // Redirect to home page
    } else {
      setError(t('loginPage.error_invalid_credentials', 'Invalid Patient ID or Password.'));
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-100 to-sky-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-2xl">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            {t('loginPage.title', 'Patient Login')}
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="p-3 bg-red-100 border-l-4 border-red-500 text-red-700 rounded-md">
              <p>{error}</p>
            </div>
          )}
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="patient-id" className="sr-only">
                {t('loginPage.patientIdLabel', 'Patient ID')}
              </label>
              <input
                id="patient-id"
                name="patient-id"
                type="text"
                autoComplete="username"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder={t('loginPage.patientIdPlaceholder', 'Patient ID')}
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                {t('loginPage.passwordLabel', 'Password')}
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder={t('loginPage.passwordPlaceholder', 'Password')}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
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
