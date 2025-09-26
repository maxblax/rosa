import React from 'react';
import { Calendar, Clock } from 'lucide-react';

interface Appointment {
  id: number;
  beneficiary: string;
  date: string;
  time: string;
  type: string;
}

const appointments: Appointment[] = [
  {
    id: 1,
    beneficiary: "Marie Dubois",
    date: "2024-03-20",
    time: "09:30",
    type: "Consultation médicale"
  },
  {
    id: 2,
    beneficiary: "Jean Martin",
    date: "2024-03-21",
    time: "14:00",
    type: "Suivi social"
  },
  {
    id: 3,
    beneficiary: "Sophie Laurent",
    date: "2024-03-22",
    time: "10:00",
    type: "Aide alimentaire"
  }
];

const UpcomingAppointments: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Prochains Rendez-vous</h2>
        <Calendar className="text-blue-600" />
      </div>
      <div className="space-y-4">
        {appointments.map((appointment) => (
          <div key={appointment.id} className="border-l-4 border-blue-500 pl-4 py-2">
            <div className="flex items-center justify-between">
              <span className="font-medium text-gray-800">{appointment.beneficiary}</span>
              <div className="flex items-center text-gray-600">
                <Clock size={16} className="mr-1" />
                <span>{appointment.time}</span>
              </div>
            </div>
            <div className="text-sm text-gray-600 mt-1">
              <span>{new Date(appointment.date).toLocaleDateString('fr-FR')}</span>
              <span className="mx-2">•</span>
              <span>{appointment.type}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default UpcomingAppointments;