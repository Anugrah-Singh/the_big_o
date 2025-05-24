import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FileText, ListChecks, Stethoscope, CalendarPlus } from 'lucide-react';

const SummaryPage = () => {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const { 
    summaryReport = t('summaryPage.defaultSummary', 'No summary provided.'), 
    possibleRemedies = [], 
    diagnosticsTests = [], 
    patientName = t('summaryPage.defaultPatientName', 'Patient') 
  } = location.state || {};

  // Enhanced check for missing critical data
  const isDataMissing = !location.state || (!summaryReport && possibleRemedies.length === 0 && diagnosticsTests.length === 0);

  if (isDataMissing) {
    return (
      <div className="container mx-auto p-4 sm:p-6 lg:p-8 text-center">
        <h1 className="text-2xl font-bold text-red-600 mb-4">{t('summaryPage.noDataTitle', 'No Summary Data Available')}</h1>
        <p className="mb-6">{t('summaryPage.noDataText', 'It seems there was an issue retrieving your summary. Please try again or contact support.')}</p>
        <button
          onClick={() => navigate('/')}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
        >
          {t('summaryPage.goHomeButton', 'Go to Home')}
        </button>
      </div>
    );
  }

  const handleBookAppointment = () => {
    // Placeholder for booking appointment logic
    alert(t('summaryPage.bookAppointmentAlert', 'Appointment booking functionality will be implemented here.'));
    // Future: navigate('/book-appointment', { state: { patientName } });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 to-sky-100 py-8 px-4 sm:px-6 lg:px-8">
      <div className="container mx-auto max-w-3xl bg-white p-6 sm:p-8 rounded-xl shadow-2xl">
        <header className="mb-8 text-center">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900">
            {t('summaryPage.title', 'Consultation Summary')}
          </h1>
          {patientName && (
            <p className="text-lg text-gray-600 mt-2">
              {t('summaryPage.forPatient', 'For: {{name}}', { name: patientName })}
            </p>
          )}
        </header>

        {/* Summary Report Section - always render structure, show default if empty */}
        <section className="mb-8 p-6 bg-sky-50 rounded-lg shadow">
          <h2 className="text-2xl font-semibold text-sky-700 mb-4 flex items-center">
            <FileText size={28} className="mr-3 text-sky-600" />
            {t('summaryPage.summaryReportTitle', 'Summary Report')}
          </h2>
          <p className="text-gray-700 whitespace-pre-wrap">
            {summaryReport || t('summaryPage.defaultSummary', 'No summary provided.')}
          </p>
        </section>

        {/* Possible Remedies Section - conditional rendering if empty */}
        {possibleRemedies && possibleRemedies.length > 0 && (
          <section className="mb-8 p-6 bg-emerald-50 rounded-lg shadow">
            <h2 className="text-2xl font-semibold text-emerald-700 mb-4 flex items-center">
              <ListChecks size={28} className="mr-3 text-emerald-600" />
              {t('summaryPage.possibleRemediesTitle', 'Possible Remedies')}
            </h2>
            <ul className="list-disc list-inside text-gray-700 space-y-1">
              {possibleRemedies.map((remedy, index) => (
                <li key={index}>{remedy}</li>
              ))}
            </ul>
          </section>
        )}

        {/* Diagnostics Tests Section - conditional rendering if empty */}
        {diagnosticsTests && diagnosticsTests.length > 0 && (
          <section className="mb-8 p-6 bg-purple-50 rounded-lg shadow">
            <h2 className="text-2xl font-semibold text-purple-700 mb-4 flex items-center">
              <Stethoscope size={28} className="mr-3 text-purple-600" />
              {t('summaryPage.diagnosticsTestsTitle', 'Suggested Diagnostic Tests')}
            </h2>
            <ul className="list-disc list-inside text-gray-700 space-y-1">
              {diagnosticsTests.map((test, index) => (
                <li key={index}>{test}</li>
              ))}
            </ul>
          </section>
        )}

        <div className="mt-10 text-center">
          <button
            onClick={handleBookAppointment}
            className="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg shadow-md inline-flex items-center text-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-opacity-50 transition-transform transform hover:scale-105"
          >
            <CalendarPlus size={22} className="mr-2" />
            {t('summaryPage.bookAppointmentButton', 'Book an Appointment')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SummaryPage;
