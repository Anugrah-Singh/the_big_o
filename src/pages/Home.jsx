import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext'; // Import useAuth
import { UserCircle, CalendarDays, Phone, Mail, MapPin } from 'lucide-react'; // Import icons

const Home = () => {
  const { t } = useTranslation();
  const { user } = useAuth(); // Get user from AuthContext

  // Hardcoded patient data (temporary)
  const patientData = {
    name: user?.username || t('homePage.patientData.name', 'John Doe'), // Use logged-in username or fallback
    id: t('homePage.patientData.id', 'PAT12345'), // This is a label for the ID, actual ID is dynamic
    dateOfBirth: '1985-07-22', // Actual data, not a translation key
    gender: t('homePage.genderMale', 'Male'), // Example, ideally this would come from user data and be translated
    contact: {
      phone: '+1-555-010-1234', // Actual data
      email: 'john.doe@example.com', // Actual data
    },
    address: {
      street: '123 Health St', // Actual data
      city: 'Wellville', // Actual data
      state: 'CA', // Actual data
      zip: '90210', // Actual data
      country: 'USA', // Actual data
    },
    medicalHistorySummary: [ // These are examples, in a real app they would be dynamic and translated if they are codes
      t('homePage.medicalHistoryItems.hypertension', 'Hypertension (diagnosed 2015)'),
      t('homePage.medicalHistoryItems.allergies', 'Seasonal allergies'),
      t('homePage.medicalHistoryItems.appendectomy', 'Appendectomy (2003)'),
    ],
    upcomingAppointments: [
      { date: '2025-06-10', time: '10:00 AM', doctor: t('homePage.appointments.doctorEmilyCarter', 'Dr. Emily Carter'), specialty: t('homePage.appointments.specialtyCardiology', 'Cardiology') },
      { date: '2025-07-05', time: '02:30 PM', doctor: t('homePage.appointments.doctorBenMiller', 'Dr. Ben Miller'), specialty: t('homePage.appointments.specialtyGeneralCheckup', 'General Checkup') },
    ],
  };

  return (
    <div className="bg-gradient-to-br from-slate-100 to-sky-100 min-h-screen px-4 sm:px-6 lg:px-8 pt-20 pb-12">
      <div className="container mx-auto">
        {/* Welcome Message and Patient Name */}
        <div className="bg-white shadow-xl rounded-xl p-6 sm:p-8 mb-8 text-center">
          <UserCircle className="w-20 h-20 text-blue-600 mx-auto mb-4" />
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-800 mb-2">
            {t('homePage.ui.welcomeMessage', { name: patientData.name })}
          </h1>
          <p className="text-lg text-gray-600">
            {t('homePage.healthOverview', "Here's an overview of your health information.")}
          </p>
        </div>

        {/* Patient Information Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Basic Information Card */}
          <div className="bg-white shadow-lg rounded-lg p-6 hover:shadow-xl transition-shadow duration-300">
            <h2 className="text-xl font-semibold text-gray-700 mb-4 border-b pb-2 flex items-center">
              <UserCircle className="w-5 h-5 mr-2 text-blue-500" /> {t('homePage.basicInfo', 'Basic Information')}
            </h2>
            <div className="space-y-3 text-sm text-gray-600">
              <p><strong>{t('homePage.patientData.id', 'Patient ID')}:</strong> {patientData.id}</p> {/* Displaying the translated label for ID */}
              <p><strong>{t('homePage.patientData.dateOfBirth', 'Date of Birth')}:</strong> {patientData.dateOfBirth}</p>
              <p><strong>{t('homePage.gender', 'Gender')}:</strong> {patientData.gender}</p>
            </div>
          </div>

          {/* Contact Information Card */}
          <div className="bg-white shadow-lg rounded-lg p-6 hover:shadow-xl transition-shadow duration-300">
            <h2 className="text-xl font-semibold text-gray-700 mb-4 border-b pb-2 flex items-center">
              <Phone className="w-5 h-5 mr-2 text-green-500" /> {t('homePage.contactInfo', 'Contact Information')}
            </h2>
            <div className="space-y-3 text-sm text-gray-600">
              <p className="flex items-center"><Phone className="w-4 h-4 mr-2 text-gray-400" /> {patientData.contact.phone}</p>
              <p className="flex items-center"><Mail className="w-4 h-4 mr-2 text-gray-400" /> {patientData.contact.email}</p>
              <p className="flex items-start"><MapPin className="w-4 h-4 mr-2 mt-1 text-gray-400 flex-shrink-0" /> 
                <span>
                  {patientData.address.street}, <br />
                  {patientData.address.city}, {patientData.address.state} {patientData.address.zip}, <br />
                  {patientData.address.country}
                </span>
              </p>
            </div>
          </div>
          
          {/* Medical History Summary Card */}
          <div className="bg-white shadow-lg rounded-lg p-6 hover:shadow-xl transition-shadow duration-300 md:col-span-2 lg:col-span-1">
            <h2 className="text-xl font-semibold text-gray-700 mb-4 border-b pb-2 flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 mr-2 text-red-500"><path d="M11.25 4.533A9.707 9.707 0 0 0 6 3a9.735 9.735 0 0 0-3.25.555.75.75 0 0 0-.5.707v14.5a.75.75 0 0 0 .5.707A9.735 9.735 0 0 0 6 21a9.707 9.707 0 0 0 5.25-1.533v-15Z M12.75 4.533V19.5A9.707 9.707 0 0 1 18 21a9.734 9.734 0 0 1 3.25-.555.75.75 0 0 1 .5-.707V3.762a.75.75 0 0 1-.5-.707A9.734 9.734 0 0 1 18 3a9.707 9.707 0 0 1-5.25 1.533Z"></path></svg>
              {t('homePage.medicalHistorySummaryTitle', 'Medical History Summary')}
            </h2>
            {patientData.medicalHistorySummary.length > 0 ? (
              <ul className="list-disc list-inside space-y-2 text-sm text-gray-600">
                {patientData.medicalHistorySummary.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">{t('homePage.none', 'No summary available.')}</p>
            )}
          </div>

          {/* Upcoming Appointments Card */}
          <div className="bg-white shadow-lg rounded-lg p-6 hover:shadow-xl transition-shadow duration-300 md:col-span-2 lg:col-span-3">
            <h2 className="text-xl font-semibold text-gray-700 mb-4 border-b pb-2 flex items-center">
              <CalendarDays className="w-5 h-5 mr-2 text-purple-500" /> {t('homePage.upcomingAppointments', 'Upcoming Appointments')}
            </h2>
            {patientData.upcomingAppointments.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left text-gray-600">
                  <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                    <tr>
                      <th scope="col" className="px-4 py-3">{t('homePage.appointmentsTable.date', 'Date')}</th>
                      <th scope="col" className="px-4 py-3">{t('homePage.appointmentsTable.time', 'Time')}</th>
                      <th scope="col" className="px-4 py-3">{t('homePage.appointmentsTable.doctor', 'Doctor')}</th>
                      <th scope="col" className="px-4 py-3">{t('homePage.appointmentsTable.specialty', 'Specialty')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {patientData.upcomingAppointments.map((appt, index) => (
                      <tr key={index} className="bg-white border-b hover:bg-gray-50">
                        <td className="px-4 py-3">{appt.date}</td>
                        <td className="px-4 py-3">{appt.time}</td>
                        <td className="px-4 py-3">{appt.doctor}</td>
                        <td className="px-4 py-3">{appt.specialty}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-gray-500">{t('homePage.none', 'No upcoming appointments.')}</p>
            )}
          </div>
        </div>

        {/* Original Hero Section (Optional - can be kept or removed) */}
        <div className="container mx-auto flex flex-col lg:flex-row items-center justify-between gap-12 py-12 lg:py-24 mt-12 border-t pt-12">
          {/* Text Content */}
          <div className="lg:w-1/2 text-center lg:text-left">
            <p className="text-lg text-gray-600 mb-2">{t('homePage.careSubtitle')}</p>
            <h1 className="text-4xl lg:text-5xl font-bold text-gray-800 mb-4">
              {t('homePage.mainTitle').split('&')[0]}& <br /> {t('homePage.mainTitle').split('&')[1]}
            </h1>
            <p className="text-gray-700 mb-8 leading-relaxed">
              {t('homePage.description')}
            </p>
          </div>

          {/* Image Content */}
          <div className="lg:w-1/2 mt-10 lg:mt-0 flex justify-center">
            <img 
              src="/src/assets/hero.jpg" // Ensure this path is correct from the public folder or use an import
              alt={t('homePage.heroAlt', 'Doctor attending to a patient')}
              className="rounded-lg shadow-xl max-w-full h-auto align-middle border-none"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
