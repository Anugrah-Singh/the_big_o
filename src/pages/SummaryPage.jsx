import React, { useState, useRef } from 'react'; // Added useState, useRef
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FileText, ListChecks, Stethoscope, CalendarPlus, UploadCloud, AlertCircle } from 'lucide-react'; // Added UploadCloud, AlertCircle
import axios from 'axios'; // Added axios

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

  const prescriptionInputRef = useRef(null);
  const reportInputRef = useRef(null);

  const [prescriptionFile, setPrescriptionFile] = useState(null);
  const [prescriptionCaptions, setPrescriptionCaptions] = useState([]);
  const [isUploadingPrescription, setIsUploadingPrescription] = useState(false);
  const [prescriptionError, setPrescriptionError] = useState(null);
  const [showPrescriptionDropdown, setShowPrescriptionDropdown] = useState(false);

  const [reportFile, setReportFile] = useState(null);
  const [reportCaptions, setReportCaptions] = useState([]);
  const [isUploadingReport, setIsUploadingReport] = useState(false);
  const [reportError, setReportError] = useState(null);
  const [showReportDropdown, setShowReportDropdown] = useState(false);

  const [isBooking, setIsBooking] = useState(false);
  const [bookingError, setBookingError] = useState(null);
  const [bookingSuccess, setBookingSuccess] = useState(null);

  const VITE_PRESCRIPTION_UPLOAD_URL = import.meta.env.VITE_PRESCRIPTION_UPLOAD_URL;
  const VITE_REPORTS_UPLOAD_URL = import.meta.env.VITE_REPORTS_UPLOAD_URL;
  const VITE_BOOK_APPOINTMENT_URL = import.meta.env.VITE_BOOK_APPOINTMENT_URL; // Added for booking

  const handlePrescriptionFileChange = (event) => {
    setPrescriptionFile(event.target.files[0]);
    setPrescriptionCaptions([]);
    setPrescriptionError(null);
    setShowPrescriptionDropdown(false);
  };

  const handleUploadPrescription = async () => {
    if (!prescriptionFile) {
      setPrescriptionError(t('summaryPage.selectPrescriptionFilePrompt', 'Please select a prescription image first.'));
      return;
    }
    if (!VITE_PRESCRIPTION_UPLOAD_URL) {
      setPrescriptionError(t('summaryPage.configError', 'Prescription upload service URL is not configured.'));
      console.error("VITE_PRESCRIPTION_UPLOAD_URL is not set in .env file");
      return;
    }

    const formData = new FormData();
    formData.append('images', prescriptionFile);

    setIsUploadingPrescription(true);
    setPrescriptionError(null);
    setPrescriptionCaptions([]);

    try {
      const response = await axios.post(VITE_PRESCRIPTION_UPLOAD_URL, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      console.log('Prescription upload response:', response); // Added console.log
      if (response.data && Array.isArray(response.data.captions)) {
        setPrescriptionCaptions(response.data.captions);
        setShowPrescriptionDropdown(true);
      } else {
        setPrescriptionCaptions([t('summaryPage.noCaptionsFound', 'No captions returned or invalid format.')]);
        setShowPrescriptionDropdown(true);
      }
    } catch (error) {
      console.error('Error uploading prescription:', error);
      setPrescriptionError(error.response?.data?.error || error.message || t('summaryPage.uploadError', 'Failed to upload prescription.'));
      setShowPrescriptionDropdown(false);
    } finally {
      setIsUploadingPrescription(false);
    }
  };

  const handleReportFileChange = (event) => {
    setReportFile(event.target.files[0]);
    setReportCaptions([]);
    setReportError(null);
    setShowReportDropdown(false);
  };

  const handleUploadReport = async () => {
    if (!reportFile) {
      setReportError(t('summaryPage.selectReportFilePrompt', 'Please select a report PDF first.'));
      return;
    }
    if (!VITE_REPORTS_UPLOAD_URL) {
      setReportError(t('summaryPage.configError', 'Report upload service URL is not configured.'));
      console.error("VITE_REPORTS_UPLOAD_URL is not set in .env file");
      return;
    }

    const formData = new FormData();
    formData.append('documents', reportFile);
    // Backend expects 'page_number', 'src_lang', 'tgt_lang' as form fields.
    // Adding them with default/placeholder values.
    formData.append('page_number', '1');
    formData.append('src_lang', 'english');
    formData.append('tgt_lang', 'kannada');

    setIsUploadingReport(true);
    setReportError(null);
    setReportCaptions([]);

    try {
      const response = await axios.post(VITE_REPORTS_UPLOAD_URL, formData, {
        // headers: {
        //   // 'Content-Type': 'multipart/form-data' // Usually set by browser with FormData
        // },
      });
      console.log('Report upload response:', response);

      if (response.data && response.data.success && Array.isArray(response.data.results)) {
        const newCaptions = response.data.results.map(result => {
          if (result.extraction) {
            // Adjust how 'extraction' is displayed based on its actual structure
            const extractionData = typeof result.extraction === 'object' ? JSON.stringify(result.extraction, null, 2) : result.extraction;
            return `${result.filename}: ${extractionData}`;
          } else if (result.error) {
            return `${result.filename}: ${t('summaryPage.reportProcessingError', 'Error')}: ${result.error}`;
          }
          return `${result.filename}: ${t('summaryPage.noDataForFile', 'No data processed for this file.')}`;
        });
        setReportCaptions(newCaptions);
        setShowReportDropdown(true);
      } else if (response.data && response.data.error) {
        // Handle backend explicitly signaling an error (e.g., "No documents provided")
        setReportError(response.data.error);
        setReportCaptions([]);
        setShowReportDropdown(false);
      } else {
        // General case for unexpected response structure
        setReportError(t('summaryPage.uploadError', 'Failed to process report. Unexpected response format.'));
        setReportCaptions([]);
        setShowReportDropdown(false);
      }
    } catch (error) {
      console.error('Error uploading report:', error);
      setReportError(error.response?.data?.error || error.message || t('summaryPage.uploadError', 'Failed to upload report.'));
      setShowReportDropdown(false);
    } finally {
      setIsUploadingReport(false);
    }
  };


  // Enhanced check for missing critical data
  const isDataMissing = !location.state || (!summaryReport && possibleRemedies.length === 0 && diagnosticsTests.length === 0);

  if (isDataMissing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-2xl p-8 text-center">
          <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="w-10 h-10 text-red-500" />
          </div>
          <h1 className="text-2xl font-bold text-red-600 mb-4">{t('summaryPage.noDataTitle', 'No Summary Data Available')}</h1>
          <p className="text-gray-600 mb-8">{t('summaryPage.noDataText', 'It seems there was an issue retrieving your summary. Please try again or contact support.')}</p>
          <button
            onClick={() => navigate('/')}
            className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-bold py-3 px-6 rounded-xl shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-all duration-200 transform hover:scale-105"
          >
            {t('summaryPage.goHomeButton', 'Go to Home')}
          </button>
        </div>
      </div>
    );
  }

  const handleBookAppointment = async () => {
    if (!VITE_BOOK_APPOINTMENT_URL) {
      setBookingError(t('summaryPage.configErrorBooking', 'Appointment booking service URL is not configured.'));
      console.error("VITE_BOOK_APPOINTMENT_URL is not set in .env file");
      return;
    }

    setIsBooking(true);
    setBookingError(null);
    setBookingSuccess(null);

    // Construct payload based on the new template
    // Many fields will need actual data from your application's state or forms
    const appointmentData = {
      name: patientName || t('summaryPage.unknownPatient', 'Unknown Patient'),
      age: "N/A - Data to be collected", // Placeholder - collect this data
      blood_group: "N/A - Data to be collected", // Placeholder
      dob: "N/A - Data to be collected", // Placeholder
      contact_info: "N/A - Data to be collected", // Placeholder
      symptoms: [
        // This is a placeholder.
        // You'll need to derive this from `summaryReport` or pass structured symptom data.
        // Example: { symptom: "Fever", onset: "3 days ago", severity: "Moderate" }
        // For now, using a generic entry if summaryReport exists.
        ...(summaryReport ? [{ symptom: summaryReport.substring(0,100) + (summaryReport.length > 100 ? '...' : ''), onset: "Unknown", severity: "Unknown"}] : [])
      ],
      medical_history: {
        conditions: [], // Placeholder - collect this data (e.g., from patient input or profile)
        allergies: []   // Placeholder - collect this data
      }
    };

    // Include possibleRemedies and diagnosticsTests if available, perhaps in a notes field or similar
    // if your backend supports it. For this template, they don't directly fit.
    // You might want to extend the backend template or add them as a general note if applicable.
    // appointmentData.notes = {
    //   consultationSummary: summaryReport,
    //   possibleRemedies: possibleRemedies,
    //   diagnosticsTests: diagnosticsTests
    // };


    try {
      console.log("Booking appointment with data:", JSON.stringify(appointmentData, null, 2));
      const response = await axios.post(VITE_BOOK_APPOINTMENT_URL, appointmentData);
      console.log('Book appointment response:', response);

      if (response.data && response.status === 200) { // Adjust based on actual success criteria
        setBookingSuccess(t('summaryPage.bookingSuccessMessage', 'Appointment booked successfully!') + (response.data.message ? ` ${response.data.message}` : ''));
        // Optionally, navigate or clear form
        // navigate('/appointment-confirmation', { state: { bookingDetails: response.data } });
      } else {
        setBookingError(response.data?.error || response.data?.message || t('summaryPage.bookingFailedError', 'Failed to book appointment. Unexpected response.'));
      }
    } catch (error) {
      console.error('Error booking appointment:', error);
      setBookingError(error.response?.data?.error || error.message || t('summaryPage.bookingApiError', 'Failed to book appointment due to a server error.'));
    } finally {
      setIsBooking(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 to-sky-100 py-8 px-4 sm:px-6 lg:px-8">
      <div className="container mx-auto max-w-4xl">
        {/* Header Section */}
        <div className="bg-white rounded-2xl shadow-2xl mb-8 overflow-hidden">
          <div className="bg-gradient-to-r from-blue-600 to-indigo-700 p-6 sm:p-8">
            <h1 className="text-3xl sm:text-4xl font-extrabold text-white text-center">
              {t('summaryPage.title', 'Consultation Summary')}
            </h1>
            {patientName && (
              <p className="text-lg text-blue-100 mt-2 text-center">
                {t('summaryPage.forPatient', 'For: {{name}}', { name: patientName })}
              </p>
            )}
          </div>
        </div>

        {/* Main Content Container */}
        <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8">

        {/* Summary Report Section - always render structure, show default if empty */}
        <section className="mb-8 p-6 bg-gradient-to-r from-sky-50 to-blue-50 rounded-2xl shadow-lg border border-sky-200">
          <h2 className="text-2xl font-semibold text-sky-700 mb-4 flex items-center">
            <FileText size={28} className="mr-3 text-sky-600" />
            {t('summaryPage.summaryReportTitle', 'Summary Report')}
          </h2>
          <div className="bg-white rounded-xl p-4 shadow-inner">
            <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
              {summaryReport || t('summaryPage.defaultSummary', 'No summary provided.')}
            </p>
          </div>
        </section>

        {/* Upload Prescription Section */}
        <section className="my-8 p-6 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl shadow-lg border border-indigo-200">
          <h2 className="text-2xl font-semibold text-indigo-700 mb-4 flex items-center">
            <UploadCloud size={28} className="mr-3 text-indigo-600" />
            {t('summaryPage.uploadPrescriptionTitle', 'Upload Your Prescription')}
          </h2>
          <div className="flex flex-col sm:flex-row items-center gap-4">
            <input
              type="file"
              accept="image/*"
              onChange={handlePrescriptionFileChange}
              ref={prescriptionInputRef}
              style={{ display: 'none' }}
              id="prescriptionUpload"
            />
            <button
              onClick={() => prescriptionInputRef.current && prescriptionInputRef.current.click()}
              className="w-full sm:w-auto bg-indigo-500 hover:bg-indigo-600 text-white font-semibold py-2 px-4 rounded-lg shadow-md inline-flex items-center justify-center text-base focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-opacity-50 transition-colors"
            >
              <UploadCloud size={20} className="mr-2" />
              {prescriptionFile ? prescriptionFile.name : t('summaryPage.selectPrescriptionButton', 'Select Prescription Image')}
            </button>
            {prescriptionFile && (
              <button
                onClick={handleUploadPrescription}
                disabled={isUploadingPrescription}
                className="w-full sm:w-auto bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-4 rounded-lg shadow-md inline-flex items-center justify-center text-base focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-opacity-50 transition-colors disabled:bg-gray-400"
              >
                {isUploadingPrescription ? t('summaryPage.uploadInProgress', 'Uploading...') : t('summaryPage.processPrescriptionButton', 'Process Prescription')}
              </button>
            )}
          </div>
          {prescriptionError && (
            <div className="mt-3 p-3 bg-red-100 border-l-4 border-red-500 text-red-700 flex items-center">
              <AlertCircle size={20} className="mr-2" />
              <p>{prescriptionError}</p>
            </div>
          )}
          {showPrescriptionDropdown && prescriptionCaptions.length > 0 && (
            <div className="mt-4 p-4 bg-indigo-50 border border-indigo-200 rounded-md shadow">
              <h3 className="text-md font-semibold text-indigo-700 mb-2">{t('summaryPage.prescriptionCaptionsTitle', 'Prescription Details:')}</h3>
              <ul className="list-disc list-inside text-gray-700 space-y-1">
                {prescriptionCaptions.map((caption, index) => (
                  <li key={index}>{caption}</li>
                ))}
              </ul>
            </div>
          )}
        </section>

        {/* Upload Test Reports Section */}
        <section className="my-8 p-6 bg-teal-50 rounded-lg shadow">
          <h2 className="text-2xl font-semibold text-teal-700 mb-4 flex items-center">
            <UploadCloud size={28} className="mr-3 text-teal-600" />
            {t('summaryPage.uploadReportTitle', 'Upload Your Test Reports')}
          </h2>
          <div className="flex flex-col sm:flex-row items-center gap-4">
            <input
              type="file"
              accept=".pdf"
              onChange={handleReportFileChange}
              ref={reportInputRef}
              style={{ display: 'none' }}
              id="reportUpload"
            />
            <button
              onClick={() => reportInputRef.current && reportInputRef.current.click()}
              className="w-full sm:w-auto bg-teal-500 hover:bg-teal-600 text-white font-semibold py-2 px-4 rounded-lg shadow-md inline-flex items-center justify-center text-base focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-opacity-50 transition-colors"
            >
              <UploadCloud size={20} className="mr-2" />
              {reportFile ? reportFile.name : t('summaryPage.selectReportButton', 'Select Report PDF')}
            </button>
            {reportFile && (
              <button
                onClick={handleUploadReport}
                disabled={isUploadingReport}
                className="w-full sm:w-auto bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-4 rounded-lg shadow-md inline-flex items-center justify-center text-base focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-opacity-50 transition-colors disabled:bg-gray-400"
              >
                {isUploadingReport ? t('summaryPage.uploadInProgress', 'Uploading...') : t('summaryPage.processReportButton', 'Process Report')}
              </button>
            )}
          </div>
          {reportError && (
            <div className="mt-3 p-3 bg-red-100 border-l-4 border-red-500 text-red-700 flex items-center">
              <AlertCircle size={20} className="mr-2" />
              <p>{reportError}</p>
            </div>
          )}
          {showReportDropdown && reportCaptions.length > 0 && (
            <div className="mt-4 p-4 bg-teal-50 border border-teal-200 rounded-md shadow">
              <h3 className="text-md font-semibold text-teal-700 mb-2">{t('summaryPage.reportCaptionsTitle', 'Report Details:')}</h3>
              <ul className="list-disc list-inside text-gray-700 space-y-1">
                {reportCaptions.map((caption, index) => (
                  <li key={index}>{caption}</li>
                ))}
              </ul>
            </div>
          )}
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
            disabled={isBooking}
            className="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg shadow-md inline-flex items-center text-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-opacity-50 transition-transform transform hover:scale-105 disabled:bg-gray-400"
          >
            <CalendarPlus size={22} className="mr-2" />
            {isBooking ? t('summaryPage.bookingInProgress', 'Booking...') : t('summaryPage.bookAppointmentButton', 'Book an Appointment')}
          </button>
          {bookingError && (
            <div className="mt-4 p-3 bg-red-100 border-l-4 border-red-500 text-red-700 flex items-center justify-center">
              <AlertCircle size={20} className="mr-2" />
              <p>{bookingError}</p>
            </div>
          )}
          {bookingSuccess && (
            <div className="mt-4 p-3 bg-green-100 border-l-4 border-green-500 text-green-700 flex items-center justify-center">
              <p>{bookingSuccess}</p>
            </div>
          )}
        </div>
        </div>
      </div>
    </div>
  );
};

export default SummaryPage;
